import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from . import db
from .auth import verify_password

SESSION_SECRET = os.environ["SESSION_SECRET"]
SESSION_HTTPS_ONLY = os.environ.get("SESSION_HTTPS_ONLY", "false").lower() == "true"

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

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    app.state.http = httpx.AsyncClient(follow_redirects=False)
    yield
    await app.state.http.aclose()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    https_only=SESSION_HTTPS_ONLY,
    same_site="lax",
)


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, next: str = "/"):
    return templates.TemplateResponse(
        request, "login.html", {"next": next, "error": None}
    )


@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request):
    form = await request.form()
    username = str(form.get("username", ""))
    password = str(form.get("password", ""))
    next_path = str(form.get("next", "/")) or "/"

    user = db.get_user(username)
    if user is None or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"next": next_path, "error": "Invalid username or password"},
            status_code=401,
        )

    request.session["username"] = username
    return RedirectResponse(url=next_path, status_code=303)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy(request: Request, path: str):
    username = request.session.get("username")
    if username is None:
        if path.startswith("api/"):
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)
        next_path = f"/{path}"
        if request.url.query:
            next_path += f"?{request.url.query}"
        return RedirectResponse(url=f"/login?next={next_path}")

    user = db.get_user(username)
    if user is None:
        request.session.clear()
        return RedirectResponse(url="/login")

    backend_host = user["backend_host"]
    url = httpx.URL(f"http://{backend_host}/{path}", params=request.query_params)

    forward_headers = {
        k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS
    }
    body = await request.body()

    upstream_request = request.app.state.http.build_request(
        request.method, url, headers=forward_headers, content=body
    )
    upstream_response = await request.app.state.http.send(upstream_request)

    response_headers = {
        k: v
        for k, v in upstream_response.headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS
    }
    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
    )
