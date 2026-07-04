from django.conf import settings
from rest_framework.response import Response
from core.responses import APIResponse


def set_auth_cookies(response: Response, access: str, refresh: str | None = None) -> None:
    response.set_cookie(
        settings.AUTH_COOKIE,
        access,
        max_age=settings.AUTH_COOKIE_MAX_AGE,
        path=settings.AUTH_COOKIE_PATH,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=settings.AUTH_COOKIE_HTTP_ONLY,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    if refresh:
        response.set_cookie(
            "refresh",
            refresh,
            max_age=settings.AUTH_COOKIE_MAX_AGE,
            path=settings.AUTH_COOKIE_PATH,
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=settings.AUTH_COOKIE_HTTP_ONLY,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(settings.AUTH_COOKIE)
    response.delete_cookie("refresh")


def build_token_response(token_data: dict, message: str) -> Response:
    response = APIResponse.success(data=token_data, message=message)
    access = token_data.get("access")
    refresh = token_data.get("refresh")
    if access:
        set_auth_cookies(response, access, refresh)
    return response
