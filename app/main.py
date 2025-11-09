import logging
import time
import traceback
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv, find_dotenv

from app.config import init_db, app_logger
from app.controllers.content_controller import ContentController
from app.controllers.auth_controller import AuthController
from app.controllers.mentee_profile_controller import MenteeProfileController
from app.controllers.user_controller import UserController
from app.controllers.workouts_controller import WorkoutsController
from app.controllers.physical_data_controller import PhysicalDataController
from app.schemas.response_schemas import ResponsePayload
from app.controllers.macronutrients_controller import MacronutrientsController
from app.controllers.meal_plan_controller import MealPlanController

load_dotenv(find_dotenv())

app = FastAPI(title="DreamFit App API")

origins = [
    "http://localhost:3000",
    "https://www.fitconnectpro.co"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    app_logger.info(
        f"REQUEST | {request.method} {request.url.path} | "
        f"IP: {client_ip} | User-Agent: {user_agent[:50]}..."
    )

    if request.query_params:
        app_logger.info(f"QUERY_PARAMS | {dict(request.query_params)}")

    try:
        response = await call_next(request)

        process_time = time.time() - start_time

        app_logger.info(
            f"RESPONSE | {request.method} {request.url.path} | "
            f"Status: {response.status_code} | Time: {process_time:.3f}s"
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time

        app_logger.error(
            f"UNHANDLED_ERROR | {request.method} {request.url.path} | "
            f"Time: {process_time:.3f}s | Error: {str(e)}"
        )
        app_logger.error(f"TRACEBACK | {traceback.format_exc()}")

        return JSONResponse(
            status_code=500,
            content=ResponsePayload.create("Internal server error", {})
        )


@app.middleware("http")
async def auth_error_middleware(request: Request, call_next):
    try:
        response = await call_next(request)

        if response.status_code == 401:
            app_logger.warning(
                f"AUTH_FAILED | {request.method} {request.url.path} | "
                f"IP: {request.client.host if request.client else 'unknown'}"
            )
        elif response.status_code == 403:
            app_logger.warning(
                f"FORBIDDEN | {request.method} {request.url.path} | "
                f"IP: {request.client.host if request.client else 'unknown'}"
            )

        return response
    except Exception as e:
        return await call_next(request)


app.include_router(ContentController.router)
app.include_router(AuthController.router)
app.include_router(MenteeProfileController.router)
app.include_router(WorkoutsController.router)
app.include_router(PhysicalDataController.router)
app.include_router(MacronutrientsController.router)
app.include_router(MealPlanController.router)
app.include_router(UserController.router)

@app.on_event("startup")
async def on_startup():
    app_logger.info("=== INICIANDO DREAMFIT API ===")
    try:
        await init_db()
        app_logger.info("=== API INICIADA CORRECTAMENTE ===")
    except Exception as e:
        app_logger.critical(f"CRITICAL ERROR AL INICIAR LA API: {str(e)}")
        raise e


@app.on_event("shutdown")
async def on_shutdown():
    app_logger.info("=== CERRANDO DREAMFIT API ===")


@app.get("/health")
async def health_check():
    app_logger.info("HEALTH_CHECK requested")
    return {"status": "healthy", "service": "dreamfit-api"}