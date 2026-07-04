"""
Djoser email classes wired to the shared `send_async_email` task.

Djoser calls `SomeEmailClass(request, context).send(to)` synchronously,
inline in the request/response cycle — the exact thing we don't want for
an HTTP-facing signup/reset endpoint. We override `send()` to:

  1. Let Djoser's own `get_context_data()` do its (cheap, synchronous) job
     of computing uid/token/url — this is just hashing, no network I/O.
  2. Flatten the `user` object into a plain dict (Celery/JSON can't carry
     a model instance), keeping only what templates need.
  3. Hand the actual SMTP work to `send_async_email`, so signup/reset
     requests return immediately.

Wire these up in settings (already matches what you have):

    DJOSER = {
        ...
        "EMAIL": {
            "activation": "core.emails.AsyncActivationEmail",
            "password_reset": "core.emails.AsyncPasswordResetEmail",
        },
    }
"""

from __future__ import annotations

import logging

from django.conf import settings
from djoser import email as djoser_email

from .tasks import send_async_email

logger = logging.getLogger(__name__)


def _serialize_user(user) -> dict:
    """Flatten the fields templates typically need out of a User instance."""
    if user is None:
        return {}
    return {
        "id": user.pk,
        "pk": user.pk,
        "email": getattr(user, "email", None),
        "name": getattr(user, "name", ""),
        # "username": user.get_username() if hasattr(user, "get_username") else None,
        # "first_name": getattr(user, "first_name", ""),
        # "last_name": getattr(user, "last_name", ""),
    }


class _AsyncDjoserEmailMixin:
    """Mix into a Djoser BaseEmailMessage subclass to send it via Celery."""

    #: Override per subclass, or set DJOSER_EMAIL_SUBJECTS in settings.
    subject_key: str = ""
    default_subject: str = "Notification"

    def get_subject(self) -> str:
        subjects = getattr(settings, "DJOSER_EMAIL_SUBJECTS", {})
        return subjects.get(self.subject_key, self.default_subject)

    def send(self, to, *args, **kwargs):
        context = self.get_context_data()
        user = context.get("user")

        send_async_email.delay(
            subject=self.get_subject(),
            to=list(to),
            template_name=self.template_name,
            context={
                "uid": context.get("uid"),
                "token": context.get("token"),
                "url": context.get("url"),
                "user": _serialize_user(user),
            },
        )
        logger.info(
            "Queued %s for %s (user_id=%s)",
            self.__class__.__name__,
            to,
            getattr(user, "pk", None),
        )


class AsyncActivationEmail(_AsyncDjoserEmailMixin, djoser_email.ActivationEmail):
    subject_key = "activation"
    default_subject = "Activate your account"


class AsyncPasswordResetEmail(_AsyncDjoserEmailMixin, djoser_email.PasswordResetEmail):
    subject_key = "password_reset"
    default_subject = "Reset your password"


class AsyncPasswordChangedConfirmationEmail(
    _AsyncDjoserEmailMixin, djoser_email.PasswordChangedConfirmationEmail
):
    subject_key = "password_changed"
    default_subject = "Your password has been changed"
