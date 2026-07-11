"""
Custom step for SOCIAL_AUTH_PIPELINE.

Djoser's ProviderAuthView runs the standard python-social-auth pipeline to
authenticate the user (via social_django's own storage). This step is
appended at the END of that pipeline to additionally mirror the
provider/uid/raw-response into our own `OAuthAccount` table, so the rest
of the app can query it directly instead of reaching into
social_django's internal tables.

Wire it up in settings:

    SOCIAL_AUTH_PIPELINE = (
        "social_core.pipeline.social_auth.social_details",
        "social_core.pipeline.social_auth.social_uid",
        "social_core.pipeline.social_auth.auth_allowed",
        "social_core.pipeline.social_auth.social_user",
        "social_core.pipeline.user.get_username",
        "social_core.pipeline.user.create_user",
        "social_core.pipeline.social_auth.associate_user",
        "social_core.pipeline.social_auth.load_extra_data",
        "social_core.pipeline.user.user_details",
        "users.social_pipeline.save_oauth_account",  # <- add this line
    )
"""

from __future__ import annotations

import logging
import mimetypes
from urllib.error import URLError
from urllib.request import urlopen

from django.core.files.base import ContentFile

from .models import OAuthAccount, OAuthProvider

logger = logging.getLogger(__name__)

# Map python-social-auth backend names -> your OAuthProvider choices.
# Adjust the left-hand values to match whatever backend names you use in
# AUTHENTICATION_BACKENDS / SOCIAL_PROVIDERS (e.g. "google-oauth2", "github").
BACKEND_TO_PROVIDER = {
    "google-oauth2": OAuthProvider.GOOGLE,
    "google": OAuthProvider.GOOGLE,
    "github": OAuthProvider.GITHUB,
}


def _get_profile_name(response):
    for key in ("name", "full_name", "display_name", "given_name"):
        value = (response or {}).get(key)
        if value:
            return str(value).strip()
    return ""


def _get_avatar_url(response):
    for key in ("picture", "avatar_url", "avatar", "image", "profile_image_url"):
        value = (response or {}).get(key)
        if value:
            return str(value).strip()
    return ""


def _save_avatar_from_url(user, avatar_url):
    if not avatar_url:
        return False

    try:
        with urlopen(avatar_url) as remote_file:
            content = remote_file.read()
            content_type = remote_file.headers.get_content_type()
    except (URLError, OSError, ValueError):
        logger.warning("Unable to fetch social avatar from %s", avatar_url)
        return False

    extension = mimetypes.guess_extension(content_type or "") or ".jpg"
    filename = f"social-avatar{extension}"
    user.avatar.save(filename, ContentFile(content), save=False)
    return True


def _sync_social_profile(user, response):
    updates = []

    profile_name = _get_profile_name(response)
    if profile_name and not (user.name or "").strip():
        user.name = profile_name
        updates.append("name")

    avatar_url = _get_avatar_url(response)
    if avatar_url and not user.avatar:
        if _save_avatar_from_url(user, avatar_url):
            updates.append("avatar")

    if hasattr(user, "is_email_verified") and not user.is_email_verified:
        user.is_email_verified = True
        updates.append("is_email_verified")

    if hasattr(user, "is_active") and not user.is_active:
        user.is_active = True
        updates.append("is_active")

    if updates:
        user.save(update_fields=updates)


def save_oauth_account(backend, user, response, uid=None, *args, **kwargs):
    """
    Runs after the user is authenticated/created by the standard pipeline.
    `user` is guaranteed to be set by this point.
    """
    if user is None:
        return

    provider = BACKEND_TO_PROVIDER.get(backend.name)
    if provider is None:
        logger.warning(
            "No OAuthProvider mapping for backend %r; skipping", backend.name
        )
        return

    _sync_social_profile(user, response)

    provider_user_id = uid or backend.get_user_id(response)

    OAuthAccount.objects.update_or_create(
        provider=provider,
        provider_user_id=provider_user_id,
        defaults={
            "user": user,
            "extra_data": response or {},
        },
    )
