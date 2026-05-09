import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import Base, SessionLocal, engine
from .routers import campaigns, customers, search, settings as settings_router, templates, unsubscribe
from .seed import seed_templates


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_templates(db)

    app.include_router(customers.router)
    app.include_router(templates.router)
    app.include_router(search.router)
    app.include_router(campaigns.router)
    app.include_router(settings_router.router)
    app.include_router(unsubscribe.router)

    @app.get("/api/health")
    def health():
        return {"ok": True, "app": settings.app_name}

    # 如果存在前端构建产物，挂载它（生产部署时使用）
    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(frontend_dist / "assets")),
            name="assets",
        )

        @app.get("/")
        def index():
            return FileResponse(str(frontend_dist / "index.html"))

        @app.get("/{path:path}")
        def spa_fallback(path: str):
            # 让前端路由可以刷新
            if path.startswith("api/") or path == "unsubscribe":
                return JSONResponse({"detail": "Not Found"}, status_code=404)
            target = frontend_dist / path
            if target.exists() and target.is_file():
                return FileResponse(str(target))
            return FileResponse(str(frontend_dist / "index.html"))

    return app


app = create_app()
