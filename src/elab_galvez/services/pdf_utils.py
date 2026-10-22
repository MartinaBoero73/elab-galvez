import os
from io import BytesIO
import matplotlib.pyplot as plt
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib import colors

from elab_galvez.domain.models import ReciboSueldo

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

def obtener_imagen_servidor(tipo: str, filename: str | None, max_width: int, max_height: int):
    """Fetches static image assets (logos, signatures) from the local directory."""
    if not filename:
        return None
    ruta_archivo = os.path.join(ASSETS_DIR, tipo, filename)
    if os.path.exists(ruta_archivo):
        return Image(ruta_archivo, width=max_width, height=max_height, kind='proportional')
    return None

def formatear_moneda(valor) -> str:
    """Formats numeric values to the Argentine currency standard (e.g., $1.000,00)."""
    if valor is None:
        return ""
    texto = f"${valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")

def construir_estilos():
    """Initializes and returns the ReportLab stylesheet configurations."""
    styles = getSampleStyleSheet()
    estilo_normal = styles["Normal"]
    estilo_normal.fontName = "Helvetica"
    estilo_normal.fontSize = 8
    estilo_normal.leading = 10 
    
    estilo_negrita = ParagraphStyle("Bold", parent=estilo_normal, fontName="Helvetica-Bold")
    estilo_titulo = ParagraphStyle("Title", parent=estilo_normal, fontName="Helvetica-Bold", fontSize=10, alignment=1)
    estilo_tabla = ParagraphStyle("TablaNormal", parent=estilo_normal, fontSize=7, leading=8)
    estilo_tabla_negrita = ParagraphStyle("TablaBold", parent=estilo_tabla, fontName="Helvetica-Bold")
    estilo_tabla_der = ParagraphStyle("TablaNormalDer", parent=estilo_tabla, alignment=TA_RIGHT)
    estilo_tabla_negrita_der = ParagraphStyle("TablaBoldDer", parent=estilo_tabla_der, fontName="Helvetica-Bold")
    
    # Styles for white text on dark ribbon rows
    estilo_tabla_negrita_blanco = ParagraphStyle("TablaBoldBlanco", parent=estilo_tabla_negrita, textColor=colors.white)
    estilo_tabla_negrita_der_blanco = ParagraphStyle("TablaBoldDerBlanco", parent=estilo_tabla_negrita_der, textColor=colors.white)
    
    return (estilo_normal, estilo_negrita, estilo_titulo, estilo_tabla, 
            estilo_tabla_negrita, estilo_tabla_der, estilo_tabla_negrita_der, 
            estilo_tabla_negrita_blanco, estilo_tabla_negrita_der_blanco)

def generar_grafico_torta(recibo: ReciboSueldo) -> BytesIO:
    """Generates an in-memory pie chart mapping the salary composition."""
    comp = recibo.composicion_salarial
    agrupaciones = {
        'Seguridad Social': comp.seguridad_social.total,
        'Obra Social': comp.obra_social.total,
        'Costo INSSJP': comp.inssjp.total,
        'Costo Sindical': comp.sindical.total,
        'Costo ART/SCVO': comp.art.total + comp.scvo.total
    }
    
    labels = ['Sueldo Neto'] + list(agrupaciones.keys())
    sizes = [float(recibo.sueldo_neto_bolsillo)] + [float(v) for v in agrupaciones.values()]
    
    labels_filtrados = [l for l, s in zip(labels, sizes) if s > 0]
    sizes_filtrados = [s for s in sizes if s > 0]
    
    fig, ax = plt.subplots(figsize=(3.5, 2.0)) 
    colores_base = ['#2ECC71', '#3498DB', '#F1C40F', '#E67E22', '#9B59B6', '#E74C3C', '#1ABC9C', '#34495E']
    colores = [colores_base[i % len(colores_base)] for i in range(len(sizes_filtrados))]
    
    separacion = [0.03] * len(sizes_filtrados)
    
    wedges, texts, autotexts = ax.pie(
        sizes_filtrados, autopct='%1.0f%%', startangle=140, 
        colors=colores, explode=separacion,
        textprops={'fontsize': 6, 'color': 'black'},
        wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'}
    )
    
    ax.axis('equal') 
    ax.legend(
        wedges, labels_filtrados, title="Referencias",
        loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), 
        fontsize=6, title_fontsize=7, frameon=False 
    )
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf