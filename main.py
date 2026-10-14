"""Point d'entrée web unique : uvicorn main:app --port 8000."""
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
import config
import securite as S
from boutique.dependencies import csrf, WEB
from boutique import pages, auth, chat, exports, admin, espace


@asynccontextmanager
async def lifespan(app):
    S.init_db()
    yield


app = FastAPI(title="Assistant de données métier", lifespan=lifespan,
              dependencies=[Depends(csrf)])


@app.middleware("http")
async def private_cache(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/") or request.url.path in ("/chat", "/admin", "/carte", "/reinit"):
        response.headers["Cache-Control"] = "no-store"
    return response


app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")
for module in (pages, auth, chat, exports, admin, espace):
    app.include_router(module.router)


@app.get("/health")
def health():
    return {"status": "ok"}
