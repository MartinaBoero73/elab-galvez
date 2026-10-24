import os
import shutil
import logging
from fastapi import APIRouter, Request, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, Response, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Domain and Service Imports
from elab_galvez.domain.models import ReciboSueldo
from elab_galvez.services.receipt_service import procesar_archivos_recibo
from elab_galvez.services.pdf_builder import generar_pdf

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
ASSETS_DIR = os.path.abspath(os.path.join(BASE_DIR, "assets"))

def _guardar_temp(archivo: UploadFile | None, subcarpeta: str) -> str | None:
    """Helper to safely save an uploaded image to the local filesystem."""
    if not archivo or not archivo.filename:
        return None
    ruta = os.path.join(ASSETS_DIR, subcarpeta, archivo.filename)
    with open(ruta, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
    return archivo.filename

# ==========================================
# ROUTERS DECLARATION
# ==========================================
web_router = APIRouter(tags=["Web UI"])
api_router = APIRouter(prefix="/api/v1", tags=["REST API"])

# ==========================================
# WEB INTERFACE (FRONTEND ENDPOINTS)
# ==========================================
@web_router.get("/", response_class=HTMLResponse)
async def leer_interfaz(request: Request):
    """Serves the main HTML wizard interface."""
    return templates.TemplateResponse(request=request, name="index.html")


@web_router.post("/api/verificar")
async def verificar_modelo(txt_cabecera: UploadFile = File(...), txt_detalle: UploadFile = File(...)):
    """Step 1 (Web): Parses TXT files and returns a summary for the UI validation."""
    try:
        # 1. Validación rápida de nombres
        if not txt_cabecera.filename.upper().startswith("CA"):
            raise ValueError(f"El archivo de cabecera debe comenzar con 'CA' (Recibido: {txt_cabecera.filename})")
        if not txt_detalle.filename.upper().startswith("DE"):
            raise ValueError(f"El archivo de detalle debe comenzar con 'DE' (Recibido: {txt_detalle.filename})")

        bytes_cabecera = await txt_cabecera.read()
        bytes_detalle = await txt_detalle.read()
        
        # 2. Validación cruzada de IDs y parseo (falla si Emp/Leg no coinciden)
        recibo = procesar_archivos_recibo(
            nombre_cabecera=txt_cabecera.filename,
            bytes_cabecera=bytes_cabecera,
            nombre_detalle=txt_detalle.filename,
            bytes_detalle=bytes_detalle
        )
        
        return JSONResponse(content={
            "status": "ok",
            "empleado": recibo.empleado.nombre,
            "empleador": recibo.empleador.nombre,
            "sueldo_neto": float(recibo.sueldo_neto_bolsillo),
            "costo_total": float(recibo.costo_total_empleador),
            "periodo": recibo.periodo.formato_estandar
        })
    except Exception as e:
        logger.error(f"UI Verification failed: {e}")
        return JSONResponse(status_code=400, content={"status": "error", "message": str(e)})


@web_router.post("/api/generar")
async def generar_recibo_pdf(
    txt_cabecera: UploadFile = File(...), 
    txt_detalle: UploadFile = File(...),
    logo: UploadFile = File(None),
    firma_emp: UploadFile = File(None),
    firma_trab: UploadFile = File(None)
):
    """Step 2 (Web): Receives files and images, saves images locally, and streams the PDF."""
    try:
        # 1. Validación rápida de nombres
        if not txt_cabecera.filename.upper().startswith("CA") or not txt_detalle.filename.upper().startswith("DE"):
            raise ValueError("Los archivos subidos no respetan la convención CA/DE esperada.")

        bytes_cabecera = await txt_cabecera.read()
        bytes_detalle = await txt_detalle.read()
        
        # 2. Validación cruzada de IDs y parseo
        recibo = procesar_archivos_recibo(
            nombre_cabecera=txt_cabecera.filename,
            bytes_cabecera=bytes_cabecera,
            nombre_detalle=txt_detalle.filename,
            bytes_detalle=bytes_detalle
        )
        
        # 3. Guardamos imágenes temporales
        logo_filename = _guardar_temp(logo, "logos")
        firma_emp_filename = _guardar_temp(firma_emp, "firmas")
        firma_trab_filename = _guardar_temp(firma_trab, "firmas")
        
        # 4. Compilamos el PDF
        pdf_buffer = generar_pdf(
            recibo, 
            logo_filename=logo_filename, 
            firma_emp_filename=firma_emp_filename, 
            firma_trab_filename=firma_trab_filename
        )
        
        return Response(content=pdf_buffer.getvalue(), media_type="application/pdf")

    except Exception as e:
        logger.error(f"PDF Generation failed: {e}")
        return JSONResponse(status_code=400, content={"status": "error", "message": str(e)})
    

# ==========================================
# REST API (PROGRAMMATIC ENDPOINTS)
# ==========================================
@api_router.get("/assets/logos")
def listar_logos():
    """Returns the list of pre-uploaded logos on the server."""
    ruta = os.path.join(ASSETS_DIR, "logos")
    archivos = [f for f in os.listdir(ruta) if f.endswith(('.png', '.jpg', '.jpeg'))]
    return {"logos": archivos}


@api_router.get("/assets/firmas")
def listar_firmas():
    """Returns the list of pre-uploaded signatures on the server."""
    ruta = os.path.join(ASSETS_DIR, "firmas")
    archivos = [f for f in os.listdir(ruta) if f.endswith(('.png', '.jpg', '.jpeg'))]
    return {"firmas": archivos}


@api_router.post("/recibos/parsear", response_model=ReciboSueldo)
async def parsear_archivos_txt(
    archivo_cabecera: UploadFile = File(...),
    archivo_detalle: UploadFile = File(...)
):
    """Parses legacy files and returns the consolidated JSON domain model."""
    try:
        bytes_cabecera = await archivo_cabecera.read()
        bytes_detalle = await archivo_detalle.read()
        
        return procesar_archivos_recibo(
            nombre_cabecera=archivo_cabecera.filename,
            bytes_cabecera=bytes_cabecera,
            nombre_detalle=archivo_detalle.filename,
            bytes_detalle=bytes_detalle
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Error in file structure.")
        raise HTTPException(status_code=422, detail="Invalid TXT structure.")


class GenerarPdfRequest(BaseModel):
    recibo: ReciboSueldo
    logo_filename: str | None = None
    firma_empleador_filename: str | None = None
    firma_empleado_filename: str | None = None


@api_router.post("/recibos/generar-pdf")
async def generar_pdf_endpoint(payload: GenerarPdfRequest):
    """Receives the validated JSON model and returns the rendered PDF file."""
    try:
        buffer = generar_pdf(
            recibo=payload.recibo,
            logo_filename=payload.logo_filename,
            firma_emp_filename=payload.firma_empleador_filename,
            firma_trab_filename=payload.firma_empleado_filename
        )
        
        id_emp = payload.recibo.empleado.id_empleador
        id_leg = payload.recibo.empleado.id_empleado
        
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=recibo_{id_emp}_{id_leg}.pdf"}
        )
    except Exception as e:
        logger.exception("Failed to build PDF.")
        raise HTTPException(status_code=500, detail="Internal PDF generation error.")