from fastapi import APIRouter

from app.api.routes import auth, credentials, devices, log_assistant, logs, users

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(credentials.router)
api_router.include_router(devices.router)
api_router.include_router(logs.router)
api_router.include_router(log_assistant.router)
