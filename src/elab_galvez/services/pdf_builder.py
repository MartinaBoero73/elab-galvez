from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from elab_galvez.domain.models import ReciboSueldo
from elab_galvez.services.pdf_utils import construir_estilos
from elab_galvez.services.pdf_sections import (
    generar_cabecera,
    generar_seccion_costo_empleador,
    generar_seccion_detalle_haberes,
    generar_seccion_final
)

def generar_pdf(recibo: ReciboSueldo, logo_filename=None, firma_emp_filename=None, firma_trab_filename=None) -> BytesIO:
    """Entry point for PDF generation. Orchestrates document flow and concatenates layout sections."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=15, bottomMargin=15
    )
    
    estilos = construir_estilos()
    (estilo_normal, estilo_negrita, estilo_titulo, estilo_tabla, estilo_tabla_negrita, 
     estilo_tabla_der, estilo_tabla_negrita_der, estilo_tabla_negrita_blanco, 
     estilo_tabla_negrita_der_blanco) = estilos
    
    story = []
    
    # 1. Headers & Employee Info
    story.extend(generar_cabecera(
        recibo, estilo_normal, estilo_negrita, estilo_titulo, estilo_tabla, logo_filename
    ))
    
    # 2. Employer Costs
    story.extend(generar_seccion_costo_empleador(
        recibo, estilo_tabla, estilo_tabla_negrita, estilo_tabla_der, 
        estilo_tabla_negrita_der, estilo_tabla_negrita_blanco, estilo_tabla_negrita_der_blanco
    ))
    
    # 3. Earnings & Deductions
    story.extend(generar_seccion_detalle_haberes(
        recibo, estilo_tabla, estilo_tabla_negrita, estilo_tabla_der, 
        estilo_tabla_negrita_der, estilo_tabla_negrita_blanco, estilo_tabla_negrita_der_blanco
    ))
    
    # 4. Data Visualization & Signatures
    story.extend(generar_seccion_final(
        recibo, estilo_normal, estilo_negrita, estilo_titulo, firma_emp_filename, firma_trab_filename
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer