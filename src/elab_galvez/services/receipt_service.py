import logging

from elab_galvez.domain.models import ReciboSueldo, TipoConcepto
from elab_galvez.parsers.regex_rules import ARCHIVO_METADATA_PATTERN
from elab_galvez.parsers.legacy_parser import parsear_recibo_completo

logger = logging.getLogger(__name__)


def _extraer_metadata_archivo(nombre_archivo: str) -> tuple[str, str]:
    """
    Uses the regex rule to extract the Employer ID and Employee ID from the filename.
    """
    match = ARCHIVO_METADATA_PATTERN.search(nombre_archivo)
    if not match:
        raise ValueError(
            f"File '{nombre_archivo}' does not match the expected format: "
            "CAxxxYYY.txt or DExxxYYY.txt"
        )
    return match.group(1), match.group(2)


def procesar_archivos_recibo(
    nombre_cabecera: str, 
    bytes_cabecera: bytes, 
    nombre_detalle: str, 
    bytes_detalle: bytes
) -> ReciboSueldo:
    """
    Orchestrates cross-validation, decoding, and logical parsing of the payslip files.
    Returns the consolidated domain model.
    """
    
    # 1. Metadata extraction from filenames (e.g., CA074001.txt)
    emp_id_cab, leg_id_cab = _extraer_metadata_archivo(nombre_cabecera)
    emp_id_det, leg_id_det = _extraer_metadata_archivo(nombre_detalle)

    # 2. Consistency validation and file pairing
    if emp_id_cab != emp_id_det or leg_id_cab != leg_id_det:
        raise ValueError(
            f"Cross-file inconsistency: "
            f"Header belongs to Emp {emp_id_cab}-Leg {leg_id_cab}, "
            f"but Detail belongs to Emp {emp_id_det}-Leg {leg_id_det}."
        )

    # 3. Legacy file decoding (Handling encoding issues)
    try:
        texto_cabecera = bytes_cabecera.decode("utf-8", errors="replace")
        texto_detalle = bytes_detalle.decode("utf-8", errors="replace")
    except Exception as e:
        logger.error(f"Failed to decode bytes: {e}")
        raise ValueError("Decoding error. Files do not appear to be valid text.")

    # 4. Parser injection and Pydantic model construction
    try:
        recibo = parsear_recibo_completo(
            texto_cabecera=texto_cabecera,
            texto_detalle=texto_detalle,
            id_empleador=emp_id_cab,
            id_empleado=leg_id_cab
        )
        logger.info(f"Payslip successfully processed: {nombre_cabecera} -> Net: ${recibo.sueldo_neto}")
        return recibo
        
    except Exception as e:
        logger.exception("Internal failure while parsing payslip structure.")
        raise RuntimeError(f"File content does not match the expected payroll layout: {e}")