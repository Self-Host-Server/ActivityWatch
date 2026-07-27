import httpx
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from .models import BackendMapping

# Headers that must not be copied across a proxy hop as-is (RFC 7230 6.1 + friends).
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "host",
}

_http_client = httpx.Client()

oauth = OAuth()
if settings.AUTHENTIK_ISSUER:
    oauth.register(
        name="authentik",
        client_id=settings.AUTHENTIK_CLIENT_ID,
        client_secret=settings.AUTHENTIK_CLIENT_SECRET,
        server_metadata_url=f"{settings.AUTHENTIK_ISSUER.rstrip('/')}/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile email"},
    )


def _user_is_provisioned(user: User) -> bool:
    return BackendMapping.objects.filter(user=user).exists()


@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    next_url = request.GET.get("next") or request.POST.get("next") or "/"
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and _user_is_provisioned(user):
            login(request, user)
            return redirect(next_url)
        error = "Invalid username or password"

    return render(
        request,
        "proxyauth/login.html",
        {
            "next": next_url,
            "error": error,
            "authentik_enabled": bool(settings.AUTHENTIK_ISSUER),
        },
    )


def authentik_login(request):
    if not settings.AUTHENTIK_ISSUER:
        raise Http404
    request.session["post_login_next"] = request.GET.get("next", "/")
    redirect_uri = request.build_absolute_uri("/login/authentik/callback/")
    return oauth.authentik.authorize_redirect(request, redirect_uri)


def authentik_callback(request):
    if not settings.AUTHENTIK_ISSUER:
        raise Http404

    token = oauth.authentik.authorize_access_token(request)
    userinfo = token.get("userinfo") or {}
    username = userinfo.get("preferred_username") or userinfo.get("sub")
    next_url = request.session.pop("post_login_next", "/")

    if not username:
        return HttpResponse("Authentik did not return a username", status=400)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse(
            f"'{username}' is not provisioned for this ActivityWatch instance",
            status=403,
        )

    if not _user_is_provisioned(user):
        return HttpResponse(
            f"'{username}' is not provisioned for this ActivityWatch instance",
            status=403,
        )

    login(request, user)
    return redirect(next_url)


def logout_view(request):
    logout(request)
    return redirect("/login/")


def proxy_view(request, path):
    if not request.user.is_authenticated:
        if path.startswith("api/"):
            return JsonResponse({"detail": "Not authenticated"}, status=401)
        next_path = f"/{path}"
        if request.META.get("QUERY_STRING"):
            next_path += f"?{request.META['QUERY_STRING']}"
        return redirect(f"/login/?next={next_path}")

    try:
        backend_host = request.user.aw_backend.backend_host
    except BackendMapping.DoesNotExist:
        logout(request)
        return redirect("/login/")

    url = httpx.URL(f"http://{backend_host}/{path}", params=request.GET)
    forward_headers = {
        k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS
    }

    upstream_request = _http_client.build_request(
        request.method, url, headers=forward_headers, content=request.body
    )
    upstream_response = _http_client.send(upstream_request)

    response_headers = {
        k: v
        for k, v in upstream_response.headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS
    }
    return HttpResponse(
        upstream_response.content,
        status=upstream_response.status_code,
        headers=response_headers,
    )
