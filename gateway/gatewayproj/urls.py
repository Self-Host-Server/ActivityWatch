from django.urls import path, re_path

from proxyauth import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("login/authentik/", views.authentik_login, name="authentik_login"),
    path(
        "login/authentik/callback/",
        views.authentik_callback,
        name="authentik_callback",
    ),
    path("logout/", views.logout_view, name="logout"),
    re_path(r"^(?P<path>.*)$", views.proxy_view, name="proxy"),
]
