from django.utils.timezone import now
from djoser import signals
from djoser.compat import get_user_email
from djoser.conf import settings as djoser_settings
from djoser.views import UserViewSet
from social_core import exceptions as social_exceptions
from social_django.utils import load_backend, load_strategy

from core.exceptions import NotFound, ValidationError
from users.serializers import UserSerializer

SOCIAL_PROVIDERS = {
    "google": "google-oauth2",
    "github": "github",
}


class AuthService:
    """Thin service layer delegating to Djoser's built-in user lifecycle logic."""

    @staticmethod
    def _user_viewset(request) -> UserViewSet:
        viewset = UserViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        viewset.kwargs = {}
        return viewset

    @staticmethod
    def register(serializer, request):
        viewset = AuthService._user_viewset(request)
        viewset.perform_create(serializer)
        return serializer.instance

    @staticmethod
    def activate_account(serializer, request):
        user = serializer.user
        user.is_active = True
        user.save(update_fields=["is_active"])

        signals.user_activated.send(
            sender=UserViewSet, user=user, request=request
        )

        if djoser_settings.SEND_CONFIRMATION_EMAIL:
            djoser_settings.EMAIL.confirmation(request, {"user": user}).send(
                [get_user_email(user)]
            )

        if hasattr(user, "is_email_verified"):
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])

    @staticmethod
    def resend_activation(serializer, request):
        user = serializer.get_user(is_active=False)

        if user and djoser_settings.SEND_ACTIVATION_EMAIL:
            djoser_settings.EMAIL.activation(request, {"user": user}).send(
                [get_user_email(user)]
            )

    @staticmethod
    def request_password_reset(serializer, request):
        user = serializer.get_user()

        if user:
            djoser_settings.EMAIL.password_reset(request, {"user": user}).send(
                [get_user_email(user)]
            )

    @staticmethod
    def confirm_password_reset(serializer, request):
        user = serializer.user
        user.set_password(serializer.validated_data["new_password"])
        if hasattr(user, "last_login"):
            user.last_login = now()
        user.save()

        if djoser_settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
            djoser_settings.EMAIL.password_changed_confirmation(
                request, {"user": user}
            ).send([get_user_email(user)])

    @staticmethod
    def update_profile(user, serializer, request):
        serializer.save()
        signals.user_updated.send(sender=UserViewSet, user=user, request=request)
        return user

    @staticmethod
    def social_login(request, provider, validated_data):
        backend_name = SOCIAL_PROVIDERS.get(provider)
        if not backend_name:
            raise NotFound(detail="Unsupported social provider.")

        redirect_uri = (validated_data.get("redirect_uri") or "").strip()
        if validated_data.get("code"):
            allowed = djoser_settings.SOCIAL_AUTH_ALLOWED_REDIRECT_URIS
            if redirect_uri and redirect_uri not in allowed:
                raise ValidationError(
                    detail="Invalid redirect_uri.",
                    extra_payload={"redirect_uri": ["redirect_uri is not allowed."]},
                )

        strategy = load_strategy(request)
        backend = load_backend(
            strategy, backend_name, redirect_uri=redirect_uri or None
        )

        oauth_data = {}
        if validated_data.get("access_token"):
            oauth_data["access_token"] = validated_data["access_token"]
        if validated_data.get("code"):
            oauth_data["code"] = validated_data["code"]
        backend._data = oauth_data

        try:
            user = backend.auth_complete()
        except social_exceptions.AuthException as exc:
            raise ValidationError(
                detail="Social authentication failed.",
                extra_payload={"non_field_errors": [str(exc)]},
            ) from exc

        if not user:
            raise ValidationError(
                detail="Social authentication failed.",
                extra_payload={"non_field_errors": ["Authentication failed."]},
            )

        token_data = djoser_settings.SOCIAL_AUTH_TOKEN_STRATEGY.obtain(user)
        return {
            "access": token_data["access"],
            "refresh": token_data["refresh"],
            "user": UserSerializer(user).data,
        }
