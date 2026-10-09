from pathlib import Path
from typing import Optional
import mimetypes
import shutil
import subprocess
import sys
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from agent.reviewer import review_implementation
from agent.context import build_context
from agent.analyzer import analyze_context
from agent.planner import create_plan
from agent.preview import create_change_preview
from agent.validator import validate_code
from agent.tools.files import list_files, read_file, modify_file, write_file
from agent.agent import run_agent


# ============================================================
# CONFIGURATION — WORKSPACE ROOT
# ============================================================

WORKSPACE_ROOT = (Path(__file__).resolve().parent / "workspace").resolve()
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

IGNORED_PREVIEW_DIRS = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".cache",
}


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Devora",
    description="AI Software Engineering Agent",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://devora-devora-frontend.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    allow_origins=[
        "https://devora-devora-frontend.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class AgentRequest(BaseModel):
    query: Optional[str] = None
    code: Optional[str] = None
    error: Optional[str] = None
    project_name: Optional[str] = None


class WorkspaceSaveRequest(BaseModel):
    path: str
    content: str


class RunFileRequest(BaseModel):
    path: str


# ============================================================
# BASIC ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Devora backend is running",
        "status": "ready",
        "preview_url": "/api/workspace/preview",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/test")
def test_connection():
    return {
        "success": True,
        "message": "Frontend and backend are connected",
        "agent": "Devora",
    }


# ============================================================
# WORKSPACE FILES
# ============================================================

@app.get("/api/workspace/files")
def get_workspace_files():
    result = list_files()
    return {
        "success": True,
        "workspace": result["workspace"],
        "items": result["items"],
        "count": result.get("count", 0),
    }


@app.get("/api/workspace/read")
def read_workspace_file(path: str):
    try:
        result = read_file(path)
        return {
            "success": True,
            "path": result["path"],
            "content": result["content"],
        }
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Unable to read the requested file.",
        )


@app.put("/api/workspace/save")
def save_workspace_file(request: WorkspaceSaveRequest):
    try:
        result = write_file(request.path, request.content)
        return {
            "success": True,
            "path": result["path"],
            "message": "File saved successfully.",
        }
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/api/workspace/clear")
def clear_workspace():
    """Clear all user files from workspace for a clean slate."""
    for item in WORKSPACE_ROOT.iterdir():
        if item.name in {".git", ".venv", "venv", "__pycache__"}:
            continue
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            item.unlink(missing_ok=True)
    return {"success": True, "message": "Workspace cleared."}


# ============================================================
# LIVE PREVIEW — STATIC HTML, CSS, JS, IMAGES
# ============================================================

def find_primary_html() -> Optional[Path]:
    """Find the best HTML file to serve in the preview."""
    # 1. Root index.html
    root_index = WORKSPACE_ROOT / "index.html"
    if root_index.is_file():
        return root_index

    # 2. public/index.html or dist/index.html
    for sub in ["public", "dist", "build"]:
        cand = WORKSPACE_ROOT / sub / "index.html"
        if cand.is_file():
            return cand

    # 3. Any .html file in root
    for p in sorted(WORKSPACE_ROOT.glob("*.html")):
        if p.is_file():
            return p

    # 4. Any .html anywhere in workspace
    for p in sorted(WORKSPACE_ROOT.rglob("*.html")):
        if any(ign in p.parts for ign in IGNORED_PREVIEW_DIRS):
            continue
        if p.is_file():
            return p

    return None


@app.api_route("/api/workspace/preview-status", methods=["GET", "HEAD"])
def preview_status():
    primary = find_primary_html()
    if primary:
        rel = primary.relative_to(WORKSPACE_ROOT).as_posix()
        return {
            "has_preview": True,
            "primary_file": rel,
            "size": primary.stat().st_size,
        }
    return {
        "has_preview": False,
        "primary_file": None,
    }


@app.api_route("/api/workspace/preview", methods=["GET", "HEAD"])
def preview_workspace():
    """Render the generated application HTML."""
    primary = find_primary_html()

    if not primary:
        placeholder_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Devora Preview</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #0f1117;
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      padding: 24px;
      text-align: center;
    }
    .card {
      background: rgba(255, 255, 255, 0.04);
      border: 1px dashed rgba(255, 255, 255, 0.15);
      border-radius: 16px;
      padding: 40px 28px;
      max-width: 460px;
      width: 100%;
    }
    .icon {
      font-size: 38px;
      margin-bottom: 14px;
      color: #7928ca;
    }
    h2 {
      font-size: 19px;
      font-weight: 600;
      margin-bottom: 8px;
      letter-spacing: -0.02em;
    }
    p {
      font-size: 13px;
      color: #94a3b8;
      line-height: 1.6;
      margin-bottom: 20px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      font-size: 11px;
      font-weight: 500;
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.1);
      border-radius: 9999px;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✦</div>
    <h2>Application Preview Ready</h2>
    <p>Ask Devora to build an app (for example: <em>"Create a Todo app in React"</em> or <em>"Create an XO game"</em>). The live interactive application will immediately display here.</p>
    <div class="pill">Waiting for task execution</div>
  </div>
</body>
</html>"""
        return HTMLResponse(
            content=placeholder_html,
            status_code=200,
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
        )

    return FileResponse(
        primary,
        media_type="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@app.get("/api/workspace/preview/{file_path:path}")
def preview_workspace_asset(file_path: str):
    """Serve assets (CSS, JS, images) referenced by the generated HTML page."""
    requested = Path(file_path.strip().lstrip("/\\"))

    if requested.is_absolute() or ".." in requested.parts:
        raise HTTPException(status_code=400, detail="Invalid preview path.")

    if any(part in IGNORED_PREVIEW_DIRS for part in requested.parts):
        raise HTTPException(status_code=403, detail="Access not allowed.")

    # 1. Check directly in workspace root
    target = (WORKSPACE_ROOT / requested).resolve()
    if not (target.is_file() and target.is_relative_to(WORKSPACE_ROOT)):
        # 2. Check in public/
        cand = (WORKSPACE_ROOT / "public" / requested).resolve()
        if cand.is_file() and cand.is_relative_to(WORKSPACE_ROOT):
            target = cand
        else:
            # 3. Check in dist/
            cand2 = (WORKSPACE_ROOT / "dist" / requested).resolve()
            if cand2.is_file() and cand2.is_relative_to(WORKSPACE_ROOT):
                target = cand2
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Preview asset not found: {file_path}",
                )

    media_type, _ = mimetypes.guess_type(str(target))
    if not media_type:
        if target.suffix.lower() in [".js", ".jsx", ".mjs"]:
            media_type = "application/javascript"
        elif target.suffix.lower() == ".css":
            media_type = "text/css"
        else:
            media_type = "application/octet-stream"

    return FileResponse(
        target,
        media_type=media_type,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


# ============================================================
# AGENT EXECUTION
# ============================================================

@app.post("/api/agent/run")
def run_software_engineering_agent(request: AgentRequest):
    query = (request.query or "").strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Please provide a software engineering task.",
        )

    try:
        print("\n" + "=" * 60)
        print("DEVORA AGENT: Request received")
        print(f"Task: {query}")
        print("=" * 60)

        result = run_agent(query)
        files_info = list_files()

        print("DEVORA AGENT: Execution finished")
        print(f"Status: {result.get('status')}")

        return {
            "success": result.get("status") == "completed",
            "agent": "Devora",
            "status": result.get("status"),
            "response": result.get("response"),
            "tool_calls": result.get("tool_calls", []),
            "files": files_info.get("items", []),
        }

    except Exception as error:
        print("\nDEVORA AGENT ERROR")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {type(error).__name__}: {str(error)}",
        ) from error


# ============================================================
# ADDITIONAL PIPELINE ENDPOINTS
# ============================================================

@app.post("/api/context")
def create_context(request: AgentRequest):
    context = build_context(
        query=request.query,
        code=request.code,
        error=request.error,
        project_name=request.project_name,
    )
    return {"success": True, "context": context}


@app.post("/api/analyze")
def analyze(request: AgentRequest):
    context = build_context(
        query=request.query,
        code=request.code,
        error=request.error,
        project_name=request.project_name,
    )
    analysis = analyze_context(context)
    return {"success": True, "context": context, "analysis": analysis}


@app.post("/api/plan")
def create_implementation_plan(request: AgentRequest):
    context = build_context(
        query=request.query,
        code=request.code,
        error=request.error,
        project_name=request.project_name,
    )
    analysis = analyze_context(context)
    plan = create_plan(context=context, analysis=analysis)
    return {"success": True, "context": context, "analysis": analysis, "plan": plan}


@app.post("/api/preview")
def create_preview(request: AgentRequest):
    context = build_context(
        query=request.query,
        code=request.code,
        error=request.error,
        project_name=request.project_name,
    )
    analysis = analyze_context(context)
    plan = create_plan(context=context, analysis=analysis)
    preview = create_change_preview(context=context, analysis=analysis, plan=plan)
    return {
        "success": True,
        "context": context,
        "analysis": analysis,
        "plan": plan,
        "preview": preview,
    }


@app.post("/api/approve")
def approve_changes(request: AgentRequest):
    return {
        "success": True,
        "status": "approved",
        "message": "Changes approved.",
    }


@app.post("/api/validate")
def validate_implementation(request: AgentRequest):
    result = validate_code(request.code or "")
    return {"success": True, "validator": result}


@app.post("/api/review")
def review_implementation_endpoint(request: AgentRequest):
    validation = validate_code(request.code or "")
    review = review_implementation(code=request.code or "", validation=validation)
    return {"success": True, "review": review}


# ============================================================
# RUN PYTHON FILE
# ============================================================

@app.post("/api/workspace/run")
def run_workspace_file(request: RunFileRequest):
    relative_path = Path(request.path)

    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise HTTPException(status_code=400, detail="Invalid workspace path.")

    target = (WORKSPACE_ROOT / relative_path).resolve()

    if not target.is_relative_to(WORKSPACE_ROOT):
        raise HTTPException(status_code=400, detail="File must remain inside workspace.")

    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    if target.suffix.lower() != ".py":
        raise HTTPException(status_code=400, detail="Only Python files can be run.")

    try:
        result = subprocess.run(
            [sys.executable, "-I", str(target)],
            cwd=str(target.parent),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return {
            "success": result.returncode == 0,
            "path": str(relative_path),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Execution timed out after 10 seconds.")
