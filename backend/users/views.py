from django.contrib.auth.tokens import default_token_generator
from djoser.serializers import (
    ActivationSerializer,
    PasswordResetConfirmRetypeSerializer,
    SendEmailResetSerializer,
)
from djoser.social.views import ProviderAuthView
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
    TokenVerifySerializer,
)

from core.responses import APIResponse
from users.serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)
from users.services import AuthService
from users.utils import build_token_response, clear_auth_cookies, set_auth_cookies


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "register"
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.register(serializer, request)
        return APIResponse.created(
            data=UserSerializer(user).data,
            message="Registration successful. Check your email to activate your account.",
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return build_token_response(
            serializer.validated_data,
            message="Login successful.",
        )


class RefreshView(APIView):
    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer

    def post(self, request):
        data = request.data.copy()
        if not data.get("refresh"):
            refresh_token = request.COOKIES.get("refresh")
            if refresh_token:
                data["refresh"] = refresh_token

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        token_data = {"access": serializer.validated_data["access"]}
        response = APIResponse.success(
            data=token_data, message="Token refreshed successfully."
        )
        set_auth_cookies(response, token_data["access"])
        return response


class VerifyView(APIView):
    permission_classes = [AllowAny]
    serializer_class = TokenVerifySerializer

    def post(self, request):
        data = request.data.copy()
        if not data.get("token"):
            access_token = request.COOKIES.get("access")
            if access_token:
                data["token"] = access_token

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        return APIResponse.success(data=None, message="Token is valid.")


class LogoutView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.Serializer

    def post(self, request):
        response = APIResponse.no_content(message="Logged out successfully.")
        clear_auth_cookies(response)
        return response


class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"
    serializer_class = SendEmailResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.request_password_reset(serializer, request)
        return APIResponse.success(
            data=None,
            message="If an account exists for that email, a reset link has been sent.",
        )


class PasswordResetConfirmView(GenericAPIView):
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"
    serializer_class = PasswordResetConfirmRetypeSerializer
    token_generator = default_token_generator

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthService.confirm_password_reset(serializer, request)

        return APIResponse.success(
            data=None,
            message="Password reset successful.",
        )


class ActivationView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "email_verify"
    serializer_class = ActivationSerializer
    token_generator = default_token_generator

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"view": self})
        serializer.is_valid(raise_exception=True)
        AuthService.activate_account(serializer, request)
        return APIResponse.success(data=None, message="Account activated successfully.")


class ResendActivationView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "email_verify"
    serializer_class = SendEmailResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.resend_activation(serializer, request)
        return APIResponse.success(
            data=None,
            message="If an inactive account exists for that email, an activation link has been sent.",
        )


class MeView(APIView):
    serializer_class = UserSerializer

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return APIResponse.success(
            data=serializer.data, message="Profile retrieved successfully."
        )


class ProfileUpdateView(APIView):
    serializer_class = UserProfileUpdateSerializer

    def patch(self, request):
        serializer = self.serializer_class(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        user = AuthService.update_profile(request.user, serializer, request)
        return APIResponse.success(
            data=UserSerializer(user).data,
            message="Profile updated successfully.",
        )


class CustomProviderAuthView(ProviderAuthView):
    """
    Wrapper around Djoser's ProviderAuthView.

    Preserves Djoser's social authentication flow while automatically
    setting authentication cookies for both new and existing users.
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code not in (200, 201):
            return response

        payload = response.data if isinstance(response.data, dict) else {}
        access = payload.get("access")
        refresh = payload.get("refresh")

        api_response = APIResponse.success(
            data=payload,
            message=payload.get("detail") or "Social login successful.",
            status_code=response.status_code,
        )

        if access:
            set_auth_cookies(api_response, access, refresh)

        return api_response
