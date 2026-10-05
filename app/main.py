from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import sessionmaker

from app.api.routes import router, templates
from app.core.config import Settings
from app.db.session import init_db


def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "app_name": request.app.state.settings.app_name,
        },
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config = settings if settings is not None else Settings.from_env()
        app.state.settings = config
        engine = init_db(config.database_url)
        app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title=settings.app_name if settings else "LeadForm Demo", lifespan=lifespan)

    @app.middleware("http")
    async def response_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.get("/")(index)
    app.include_router(router)
    return app


app = create_app()
