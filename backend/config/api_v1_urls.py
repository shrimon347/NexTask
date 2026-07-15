from django.urls import include, path

urlpatterns = [
    path("", include("users.urls")),
    path("", include("workspaces.urls")),
    path("", include("projects.urls")),
]
