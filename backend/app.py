"""Loopback-only API. Start with python -m backend (one worker)."""
import asyncio
import hmac
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .models import (AnalysisRequest, ChallengeRequest, Evaluation, ExplanationRequest,
                     OpenProject, PatchView, RunRequest, SessionView)
from .service import (HINTS, Session, commit_patch, open_session, propose_sample_patch,
                      sample_evaluation, start_challenge)
from sandbox.runner import run_validation

logger = logging.getLogger("codeproof.backend")


def create_app(token: str | None = None) -> FastAPI:
    access_token = token or os.environ.get("CODEPROOF_TOKEN", "")
    if len(access_token) < 32:
        raise RuntimeError("Set CODEPROOF_TOKEN to at least 32 characters, or use python -m backend")
    sessions: dict[str, Session] = {}

    @asynccontextmanager
    async def lifespan(app):
        yield
        for session in sessions.values():
            session.close()
        sessions.clear()

    app = FastAPI(title="CodeProof Local API", version="1.0.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])

    @app.middleware("http")
    async def browser_boundary(request: Request, call_next):
        if request.headers.get("origin"):
            return JSONResponse({"detail": "Browser origins cannot access the desktop API"}, status_code=403)
        length = request.headers.get("content-length", "0")
        if not length.isdigit() or int(length) > 256_000 or request.headers.get("transfer-encoding"):
            return JSONResponse({"detail": "Request too large or unsupported transfer encoding"}, status_code=413)
        return await call_next(request)

    def authorized(authorization: str = Header(default="")):
        if not hmac.compare_digest(authorization, "Bearer " + access_token):
            raise HTTPException(401, "Invalid local service token")

    def get_session(session_id: str) -> Session:
        session = sessions.get(session_id)
        if not session:
            raise HTTPException(404, "Session not found. Open the project again.")
        return session

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @app.exception_handler(Exception)
    async def failure(request, exc):
        # Do not log exception strings: providers may include credentials or source.
        logger.error("request_failed", extra={"error_type": type(exc).__name__})
        return JSONResponse({"detail": "Operation failed. Check the local service configuration and try again."}, status_code=500)

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "1.0.0"}

    @app.get("/v1/capabilities", dependencies=[Depends(authorized)])
    def capabilities():
        import shutil
        return {"ai_configured": bool(os.environ.get("OPENROUTER_API_KEY") and os.environ.get("CODEPROOF_MODEL")),
                "docker_installed": bool(shutil.which("docker")),
                "runners": ["python-unittest", "python-pytest", "node-test"]}

    @app.post("/v1/sessions", response_model=SessionView, dependencies=[Depends(authorized)])
    async def open_project(body: OpenProject):
        for key, existing in list(sessions.items()):
            if time.monotonic() - existing.created > 7200 and not existing.lock.locked():
                existing.close()
                del sessions[key]
        if len(sessions) >= 8:
            raise HTTPException(409, "Close an existing session before opening another")
        # Opening is serialized on the local event loop to keep the eight-session cap exact.
        session = open_session(body.path)
        sessions[session.view.id] = session
        return session.view

    @app.delete("/v1/sessions/{session_id}", dependencies=[Depends(authorized)])
    async def close_project(session_id: str):
        session = get_session(session_id)
        async with session.lock:
            session.close()
            sessions.pop(session_id, None)
        return {"closed": True}

    @asynccontextmanager
    async def provider():
        from ai.providers import AIProviderConfig, OpenRouterProvider
        key, model = os.environ.get("OPENROUTER_API_KEY"), os.environ.get("CODEPROOF_MODEL")
        if not key or not model:
            raise HTTPException(503, "AI is not configured. Set OPENROUTER_API_KEY and CODEPROOF_MODEL in the backend environment.")
        instance = OpenRouterProvider(AIProviderConfig(api_key=key, model=model, timeout=60))
        try:
            yield instance
        finally:
            await instance.close()

    def context(session: Session):
        from ai.models import ChallengeContext
        view = session.view
        return ChallengeContext(challenge_id=view.id, title=view.challenge_title,
            description=view.challenge_description, difficulty="medium", target_skill="Debugging",
            problem_statement=view.challenge_description, relevant_files=view.relevant_files,
            relevant_code_excerpts=[view.files[p][:12000] for p in view.relevant_files],
            expected_concepts=["Explain the root cause using the supplied code and observed behavior"],
            project_summary=view.summary)

    @app.post("/v1/sessions/{session_id}/analysis", response_model=SessionView, dependencies=[Depends(authorized)])
    async def analyze(session_id: str, body: AnalysisRequest):
        session = get_session(session_id)
        async with session.lock:
            if session.view.phase != "analyzed":
                raise HTTPException(409, "Analyze before starting an investigation")
            if body.use_ai:
                from ai.services.analyzer import ProjectAnalyzer
                from .models import Skill
                async with provider() as client:
                    engine = ProjectAnalyzer(client)
                    analysis = await engine.analyze(session.snapshot)
                    skill_map = await engine.map_skills(session.snapshot)
                view = session.view
                view.summary = analysis.summary
                view.technologies = analysis.technologies
                view.issues = analysis.issues
                view.skills = [Skill(**skill.model_dump()) for skill in skill_map.skill_estimates]
                view.provider = "AI · OpenRouter"
                view.activity.append("AI analysis completed using the redacted snapshot.")
                session.use_ai = True
            return session.view

    @app.post("/v1/sessions/{session_id}/challenge", response_model=SessionView, dependencies=[Depends(authorized)])
    async def challenge(session_id: str, body: ChallengeRequest):
        session = get_session(session_id)
        async with session.lock:
            start_challenge(session, body.issue, body.target_file)
            return session.view

    @app.post("/v1/sessions/{session_id}/hint", response_model=SessionView, dependencies=[Depends(authorized)])
    async def hint(session_id: str):
        session = get_session(session_id)
        async with session.lock:
            view = session.view
            if view.phase == "analyzed" or len(view.hints) >= 4:
                raise HTTPException(409, "No further hints are available")
            if view.sample:
                content = HINTS[len(view.hints)]
            else:
                if not session.use_ai:
                    raise HTTPException(409, "Enable AI analysis before requesting project coaching")
                from ai.models import HintRequest
                from ai.services.hint_engine import HintEngine
                async with provider() as client:
                    response = await HintEngine(client).generate_hint(HintRequest(
                        challenge_id=view.id, hint_level=len(view.hints) + 1,
                        developer_progress="Inspecting project evidence", challenge_context=context(session)))
                    content = response.hint_content
            view.hints.append(content)
            return view

    @app.post("/v1/sessions/{session_id}/explanation", response_model=SessionView, dependencies=[Depends(authorized)])
    async def explain(session_id: str, body: ExplanationRequest):
        session = get_session(session_id)
        async with session.lock:
            view = session.view
            if view.phase not in ("investigating", "review"):
                raise HTTPException(409, "Start an investigation first")
            if view.sample:
                result = sample_evaluation(body.explanation)
                patch = propose_sample_patch(view) if result.passed else None
            else:
                if not session.use_ai:
                    raise HTTPException(409, "Project coaching requires AI analysis. Reopen the project and enable AI first.")
                from ai.models import ExplanationEvaluationRequest, PatchRequest
                from ai.services.explanation_evaluator import ExplanationEvaluator
                from ai.services.patch_generator import PatchGenerator
                async with provider() as client:
                    evaluation = await ExplanationEvaluator(client).evaluate(ExplanationEvaluationRequest(
                        challenge_context=context(session), developer_explanation=body.explanation,
                        expected_concepts=context(session).expected_concepts))
                    result = Evaluation(passed=evaluation.passed, score=evaluation.score, feedback=evaluation.feedback)
                    patch = None
                    if result.passed:
                        current = session.snapshot.model_copy(update={"files": view.files})
                        proposed = await PatchGenerator(client).generate_patch(PatchRequest(
                            issue_description=view.challenge_description, project_snapshot=current,
                            target_files=view.relevant_files))
                        from .patching import apply_diff
                        apply_diff(view.files, proposed.diff, view.relevant_files)
                        patch = PatchView(**proposed.model_dump())
            view.evaluation = result
            view.patch = patch
            view.phase = "review" if result.passed else "investigating"
            view.activity.append("Explanation reviewed; patch unlocked." if result.passed else "Explanation needs more evidence.")
            return view

    @app.post("/v1/sessions/{session_id}/patch", response_model=SessionView, dependencies=[Depends(authorized)])
    async def patch(session_id: str):
        session = get_session(session_id)
        async with session.lock:
            commit_patch(session)
            return session.view

    @app.post("/v1/sessions/{session_id}/validation", response_model=SessionView, dependencies=[Depends(authorized)])
    async def validate(session_id: str, body: RunRequest):
        session = get_session(session_id)
        async with session.lock:
            result = await asyncio.to_thread(run_validation, session.copy, body.runner)
            result.original_unchanged = session.original_unchanged()
            if not result.original_unchanged:
                result.checks.append("Original project changed externally; refresh the snapshot")
            session.view.validation = result
            if session.view.phase in ("applied", "validated"):
                session.view.phase = "validated" if result.status == "passed" and result.original_unchanged else "applied"
            session.view.activity.append(f"Docker validation: {result.status}.")
            return session.view

    @app.get("/v1/sessions/{session_id}/report", dependencies=[Depends(authorized)])
    async def report(session_id: str):
        session = get_session(session_id)
        async with session.lock:
            view = session.view
            return {"project": view.name, "provider": view.provider, "phase": view.phase,
                    "validation": view.validation.model_dump(), "activity": view.activity,
                    "notice": "Review evidence only. Not a production readiness certification."}

    return app
