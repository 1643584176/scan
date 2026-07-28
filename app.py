from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from assettrace.config import BASE_DIR, Settings
from assettrace.engine import ScanEngine
from assettrace.knowledge import export_approved_knowledge
from assettrace.storage import Repository
from assettrace.urls import InvalidUrl


class ProjectCreate(BaseModel):
    url: str = Field(min_length=4, max_length=2048)
    name: str = Field(default="", max_length=120)


class ScanRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)
    name: str = Field(default="", max_length=120)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    repository = Repository(resolved_settings)
    engine = ScanEngine(repository, resolved_settings)
    project_locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        resolved_settings.ensure_directories()
        yield

    application = FastAPI(
        title="AssetTrace",
        description="URL and JavaScript incremental security analysis ledger",
        version="0.1.0",
        lifespan=lifespan,
    )
    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
    static_dir = BASE_DIR / "static"
    if static_dir.exists():
        application.mount(
            "/static", StaticFiles(directory=str(static_dir)), name="static"
        )

    application.state.settings = resolved_settings
    application.state.repository = repository
    application.state.engine = engine

    @application.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={},
        )

    @application.get("/health")
    async def health():
        return {"status": "ok", "schema": 1}

    @application.get("/api/projects")
    async def list_projects():
        return {"projects": repository.list_projects()}

    @application.post("/api/projects", status_code=201)
    async def create_project(payload: ProjectCreate):
        try:
            return repository.create_or_get_project(payload.url, payload.name)
        except (InvalidUrl, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @application.get("/api/projects/{project_id}")
    async def project_detail(project_id: int):
        detail = repository.project_detail(project_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Project not found")
        return detail

    @application.post("/api/projects/{project_id}/scans")
    async def scan_project(project_id: int):
        if not repository.get_project(project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        lock = project_locks[project_id]
        if lock.locked():
            raise HTTPException(
                status_code=409,
                detail="A scan is already running for this project",
            )
        async with lock:
            return await engine.scan_project(project_id)

    @application.post("/api/scans")
    async def scan_url(payload: ScanRequest):
        try:
            project = repository.create_or_get_project(payload.url, payload.name)
        except (InvalidUrl, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        lock = project_locks[project["id"]]
        if lock.locked():
            raise HTTPException(
                status_code=409,
                detail="A scan is already running for this project",
            )
        async with lock:
            return await engine.scan_project(project["id"])

    @application.post("/api/findings/{finding_id}/promote", status_code=201)
    async def promote_finding(finding_id: int):
        try:
            return repository.promote_finding(finding_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.get("/api/knowledge")
    async def list_knowledge(status: str | None = None):
        if status not in {None, "draft", "approved"}:
            raise HTTPException(status_code=422, detail="Invalid knowledge status")
        return {"items": repository.list_knowledge(status)}

    @application.post("/api/knowledge/{knowledge_id}/approve")
    async def approve_knowledge(knowledge_id: int):
        try:
            item = repository.approve_knowledge(knowledge_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        output = export_approved_knowledge(
            repository, resolved_settings.skill_dir
        )
        return {"item": item, "exported_to": str(output)}

    return application


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
