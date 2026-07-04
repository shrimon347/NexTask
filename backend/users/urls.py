from django.urls import path

from users import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="auth-register"),
    path("auth/login/", views.LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", views.RefreshView.as_view(), name="auth-refresh"),
    path("auth/verify/", views.VerifyView.as_view(), name="auth-verify"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth-logout"),
    path(
        "auth/password/reset/",
        views.PasswordResetView.as_view(),
        name="auth-password-reset",
    ),
    path(
        "auth/password/reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("auth/activation/", views.ActivationView.as_view(), name="auth-activation"),
    path(
        "auth/resend-activation/",
        views.ResendActivationView.as_view(),
        name="auth-resend-activation",
    ),
    path("auth/me/", views.MeView.as_view(), name="auth-me"),
    path("auth/profile/", views.ProfileUpdateView.as_view(), name="auth-profile"),
    path(
        "auth/social/google/",
        views.SocialAuthView.as_view(),
        {"provider": "google"},
        name="auth-social-google",
    ),
    path(
        "auth/social/github/",
        views.SocialAuthView.as_view(),
        {"provider": "github"},
        name="auth-social-github",
    ),
]
