from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.database import close_db
from src.routers import (
    auth,
    companies,
    dashboard,
    evaluations,
    job_roles,
    profile,
    submissions,
    tasks,
    threads,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_db()


app = FastAPI(
    title="TaskFit API",
    description="기업 맞춤형 실무 과제 체험 플랫폼",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(job_roles.router)
app.include_router(tasks.router)
app.include_router(submissions.router)
app.include_router(threads.router)
app.include_router(evaluations.router)
app.include_router(dashboard.router)
app.include_router(profile.router)

# dev 라우터: production이 아닐 때만 포함
settings = get_settings()
if settings.environment != "production":
    from src.routers import dev

    app.include_router(dev.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
