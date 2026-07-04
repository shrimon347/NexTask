from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from core.models import BaseModel

from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """Custom authentication user model using email as the login identifier."""

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=50, blank=True, null=True)

    avatar = models.ImageField(upload_to="uploads/avatars", null=True, blank=True)

    is_email_verified = models.BooleanField(default=False)

    is_2fa_enabled = models.BooleanField(default=False)
    two_fa_otp = models.CharField(max_length=10, null=True, blank=True)
    two_fa_otp_expires = models.DateTimeField(null=True, blank=True)

    # Django auth fields
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        """Return readable identifier for admin and logs."""
        return self.email

    def avatar_url(self):
        """Return absolute avatar URL or an empty string when not set."""
        if self.avatar:
            return f"{settings.WEBSITE_URL}{self.avatar.url}"
        return ""
