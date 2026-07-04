from django.contrib.auth import get_user_model
from djoser.serializers import UserCreatePasswordRetypeSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "name",
            "avatar_url",
            "is_email_verified",
            "is_2fa_enabled",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_avatar_url(self, obj):
        return obj.avatar_url()


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name", "avatar")


class RegisterSerializer(UserCreatePasswordRetypeSerializer):
    """Registration serializer."""

    class Meta(UserCreatePasswordRetypeSerializer.Meta):
        model = User
        fields = UserCreatePasswordRetypeSerializer.Meta.fields + ("name",)


class LoginSerializer(TokenObtainPairSerializer):
    """SimpleJWT login with user payload in the standard login response."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class SocialAuthSerializer(serializers.Serializer):
    """OAuth credentials accepted by social login endpoints."""

    access_token = serializers.CharField(required=False, allow_blank=True)
    code = serializers.CharField(required=False, allow_blank=True)
    redirect_uri = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        access_token = (attrs.get("access_token") or "").strip()
        code = (attrs.get("code") or "").strip()

        if bool(access_token) == bool(code):
            raise serializers.ValidationError(
                "Provide exactly one of access_token or code."
            )

        attrs["access_token"] = access_token or None
        attrs["code"] = code or None
        return attrs
