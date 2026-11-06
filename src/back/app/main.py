from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import models  # noqa: F401  (테이블 등록)
from app.api.routers import auth, courses, enrollments
from app.core.config import CORS_ORIGINS
from app.core.database import Base, SessionLocal, engine
from app.core.exceptions import AppError
from app.seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="myAIEdu API", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                       allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    for module in (auth, courses, enrollments):
        app.include_router(module.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
