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

from .models import OAuthAccount, OAuthProvider

logger = logging.getLogger(__name__)

# Map python-social-auth backend names -> your OAuthProvider choices.
# Adjust the left-hand values to match whatever backend names you use in
# AUTHENTICATION_BACKENDS / SOCIAL_PROVIDERS (e.g. "google-oauth2", "github").
BACKEND_TO_PROVIDER = {
    "google-oauth2": OAuthProvider.GOOGLE,
    "github": OAuthProvider.GITHUB,
}


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

    provider_user_id = uid or backend.get_user_id(response)

    OAuthAccount.objects.update_or_create(
        provider=provider,
        provider_user_id=provider_user_id,
        defaults={
            "user": user,
            "extra_data": response or {},
        },
    )
