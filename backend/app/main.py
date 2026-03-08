"""FastAPI application: CORS, security headers, exception handler, routers."""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.exceptions import APIError
from app.routers import auth, users, resumes, skills, roles, jobs, gaps, courses, plan, dev

settings = get_settings()
app = FastAPI(title="SkillGap API", version="0.1.0")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(APIError)
def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {
        400: "BAD_REQUEST",
        401: "AUTH_TOKEN_INVALID",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        429: "TOO_MANY_REQUESTS",
    }
    error_code = code_map.get(exc.status_code, "ERROR")
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": error_code, "message": message},
    )


@app.exception_handler(Exception)
def generic_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error_code": "SYSTEM_INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )


# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(resumes.router)
app.include_router(skills.router)
app.include_router(roles.router)
app.include_router(jobs.router)
app.include_router(gaps.router)
app.include_router(courses.router)
app.include_router(plan.router)
app.include_router(dev.router)
