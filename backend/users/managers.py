from django.contrib.auth.models import UserManager


class CustomUserManager(UserManager):
    """Manager for creating regular and super users via email login."""

    def _create_user(self, name, email, password, **extra_fields):
        """Create and persist a user with normalized email and hashed password."""
        if not email:
            raise ValueError("You have not specified a valid email address")
        email = self.normalize_email(email)
        email = email.lower()
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return user

    def create_user(self, name=None, email=None, password=None, **extra_fields):
        """Create a standard non-staff user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(name, email, password, **extra_fields)

    def create_superuser(self, name=None, email=None, password=None, **extra_fields):
        """Create a staff superuser account."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(name, email, password, **extra_fields)
