"""
Async email sending — single reusable entry point.

Design goals
------------
1. ONE task (`send_async_email`) is the only place that talks to Django's
   email backend. Plain emails, templated emails, and Djoser's
   activation/password-reset emails all funnel through it. No more
   parallel implementations that quietly drift apart.
2. Retries are automatic for *transient* failures (SMTP hiccups, timeouts,
   DB blips) with exponential backoff + jitter, and are NOT attempted for
   *permanent* failures (missing template, bad header) so a broken
   deployment doesn't hammer your SMTP provider for hours.
3. `acks_late` + `reject_on_worker_lost` so a worker dying mid-send doesn't
   silently drop the email (trade-off: an email can rarely be sent twice —
   acceptable for transactional mail, not for billing webhooks).
4. Recipient lists are validated/deduped before anything is sent.
5. Attachments travel through Celery as base64 so this works safely with
   the JSON serializer (do NOT use the pickle serializer in production).
"""

from __future__ import annotations

import base64
import logging
from smtplib import SMTPException

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.core.validators import validate_email
from django.db import DatabaseError
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils import timezone
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

# Exceptions worth retrying: anything that smells like a transient
# infrastructure problem rather than a bug in the email itself.
RETRYABLE_EXCEPTIONS = (
    SMTPException,
    ConnectionError,
    TimeoutError,
    OSError,
    DatabaseError,
    SoftTimeLimitExceeded,
)


def get_base_email_context(extra_context: dict | None = None) -> dict:
    """Context available to every email template (branding, dates, links)."""
    try:
        domain = getattr(settings, "WEBSITE_URL", "Domain")
    except Exception:  # Sites framework not migrated/configured, DB hiccup, etc.
        logger.warning(
            "Could not resolve current Site; falling back to settings.DOMAIN",
            exc_info=True,
        )
        domain = getattr(settings, "WEBSITE_URL", "localhost")

    base_context = {
        "current_date": timezone.localtime().date(),
        "domain": domain,
        "site_name": getattr(settings, "SITE_NAME", "Site"),
        "logo_url": f"https://{domain}{static('images/logo.png')}",
        "website_url": f"https://{domain}",
        "contact_email": getattr(settings, "CONTACT_EMAIL", "admin@example.com"),
        "social_facebook": getattr(
            settings, "SOCIAL_FACEBOOK", "https://www.facebook.com/"
        ),
        "social_linkedin": getattr(
            settings, "SOCIAL_LINKEDIN", "https://www.linkedin.com/"
        ),
        "social_youtube": getattr(
            settings, "SOCIAL_YOUTUBE", "https://www.youtube.com/"
        ),
        "social_twitter": getattr(settings, "SOCIAL_TWITTER", "https://x.com/"),
    }
    if extra_context:
        base_context.update(extra_context)
    return base_context


def _normalize_recipients(value) -> list[str]:
    """Coerce to a deduped list of valid email addresses, dropping junk."""
    if not value:
        return []
    if isinstance(value, str):
        value = [value]

    cleaned: list[str] = []
    seen: set[str] = set()
    for addr in value:
        addr = (addr or "").strip()
        if not addr or addr.lower() in seen:
            continue
        try:
            validate_email(addr)
        except ValidationError:
            logger.warning("Dropping invalid email address: %r", addr)
            continue
        seen.add(addr.lower())
        cleaned.append(addr)
    return cleaned


def encode_attachment(
    filename: str, content: bytes, mimetype: str | None = None
) -> dict:
    """
    Helper for callers scheduling `send_async_email` with a file attached.
    Celery args must be JSON-serializable, so raw bytes get base64-encoded.

        attachments=[encode_attachment("invoice.pdf", pdf_bytes, "application/pdf")]
    """
    return {
        "filename": filename,
        "content_b64": base64.b64encode(content).decode("ascii"),
        "mimetype": mimetype,
    }


@shared_task(
    bind=True,
    autoretry_for=RETRYABLE_EXCEPTIONS,
    retry_backoff=30,  # 30s, 60s, 120s, ... exponential
    retry_backoff_max=600,  # cap at 10 min
    retry_jitter=True,  # avoid thundering-herd retries
    max_retries=5,
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=25,
    time_limit=45,
)
def send_async_email(
    self,
    *,
    subject: str,
    to: list[str] | str,
    template_name: str | None = None,
    text_template_name: str | None = None,
    context: dict | None = None,
    plain_message: str | None = None,
    cc: list[str] | str | None = None,
    bcc: list[str] | str | None = None,
    attachments: list[dict] | None = None,
    from_email: str | None = None,
    reply_to: list[str] | str | None = None,
    headers: dict | None = None,
) -> None:
    """
    The single reusable entry point for all outgoing email in the project.

    Usage
    -----
    send_async_email.delay(
        subject="Welcome!",
        to=[user.email],
        template_name="emails/welcome.html",   # renders HTML body
        context={"user": {"first_name": user.first_name}},
    )

    send_async_email.delay(
        subject="Heads up",
        to=["ops@example.com"],
        plain_message="Build failed.",         # plain-text-only email
    )
    """
    recipients = _normalize_recipients(to)
    if not recipients:
        logger.warning(
            "send_async_email skipped: no valid recipients (subject=%r)", subject
        )
        return

    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    full_context = get_base_email_context(context)

    try:
        html_body = (
            render_to_string(template_name, full_context) if template_name else None
        )
        text_body = (
            plain_message
            or (
                render_to_string(text_template_name, full_context)
                if text_template_name
                else None
            )
            or (strip_tags(html_body) if html_body else "")
        )
    except TemplateDoesNotExist:
        # A missing template is a bug, not a transient failure — fail loudly,
        # don't burn 5 retries and 10 minutes finding that out.
        logger.error(
            "Email template not found: %r (subject=%r)", template_name, subject
        )
        raise

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=recipients,
        cc=_normalize_recipients(cc) or None,
        bcc=_normalize_recipients(bcc) or None,
        reply_to=_normalize_recipients(reply_to) or None,
        headers=headers or None,
    )

    if html_body:
        email.attach_alternative(html_body, "text/html")

    for attachment in attachments or []:
        email.attach(
            attachment["filename"],
            base64.b64decode(attachment["content_b64"]),
            attachment.get("mimetype"),
        )

    try:
        email.send(fail_silently=False)
    except BadHeaderError:
        # Malformed header (e.g. header injection attempt) — never retry this.
        logger.exception("Refusing to retry send with bad header (subject=%r)", subject)
        raise

    logger.info(
        "Email sent: subject=%r recipients=%d task_id=%s attempt=%d",
        subject,
        len(recipients),
        self.request.id,
        self.request.retries + 1,
    )
