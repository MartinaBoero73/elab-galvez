import os
from fastapi import FastAPI
from elab_galvez.api.routers.routes import web_router, api_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.abspath(os.path.join(BASE_DIR, "assets"))

# Ensure asset directories exist on server startup
os.makedirs(os.path.join(ASSETS_DIR, "logos"), exist_ok=True)
os.makedirs(os.path.join(ASSETS_DIR, "firmas"), exist_ok=True)


# ==========================================
# FASTAPI APPLICATION INSTANCE
# ==========================================
app = FastAPI(
    title="eLab Gálvez - Payroll API (Local Deploy)",
    description="Microservice for parsing and generating Argentine payslips on a traditional server.",
    version="0.1.0"
)

# Attach isolated routers
app.include_router(web_router)
app.include_router(api_router)