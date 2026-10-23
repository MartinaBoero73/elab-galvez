from datetime import datetime, date
from decimal import Decimal
import re

from elab_galvez.domain.models import (
    ReciboSueldo,
    Empleador,
    Empleado,
    PeriodoLiquidacion,
    ConceptoLiquidacion,
    TipoConcepto,
    ContribucionPatronal,
    ComposicionSalarial,
    DetalleRubro
)
from elab_galvez.parsers.regex_rules import (
    CABECERA_PATTERN,
    MONTO_DETALLE_PATTERN,
    LIMITE_REMUNERATIVO,
    LIMITE_DESCUENTO,
)


def _parsear_decimal(valor: str) -> Decimal:
    """Converts an Argentine formatted numeric string to Decimal."""
    if not valor or valor.strip() == "":
        return Decimal("0")
    return Decimal(valor.strip().replace(".", "").replace(",", "."))


def _parsear_fecha(valor: str) -> date | None:
    """Parses dates in DD/MM/YYYY format."""
    if not valor or not valor.strip():
        return None
    try:
        return datetime.strptime(valor.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _parsear_periodo(valor: str) -> PeriodoLiquidacion:
    """Converts strings like 'OCTUBRE 2026' into PeriodoLiquidacion(10, 2026)."""
    meses = {
        "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
        "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
        "SEPTIEMBRE": 9, "SETIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12,
    }

    texto = valor.strip().upper()
    
    match_anio = re.search(r'\b(19|20)\d{2}\b', texto)
    anio = int(match_anio.group()) if match_anio else 1900
    
    # Safe name extraction (works for annual licenses and other with month not specificated)
    mes = 1 
    for nombre_mes, numero_mes in meses.items():
        if nombre_mes in texto:
            mes = numero_mes
            break
            
    return PeriodoLiquidacion(mes=mes, anio=anio)


def parsear_cabecera(texto_cabecera: str) -> dict:
    datos = {"contribuciones": []}
    buffer_multilinea = ""

    for linea in texto_cabecera.splitlines():
        if not linea.strip():
            continue

        # 1. Split by multiple spaces
        partes_crudas = re.split(r'\s{2,}', linea)
        
        # 2. VITAL FILTER: Remove empty strings caused by left margin indentation
        partes = [p.strip() for p in partes_crudas if p.strip()]

        if not partes:
            continue

        if len(partes) >= 2:
            # Standard case: [Value, Key]
            valor = " ".join(partes[:-1])
            # Strip trailing colons in case they are attached to the key
            clave = partes[-1].rstrip(":") 

            if buffer_multilinea:
                valor = (buffer_multilinea + " " + valor).strip()
                buffer_multilinea = ""

            clave_upper = clave.upper()
            if clave_upper.startswith("CONTRIBUCIONES") and clave_upper != "SUBTOTAL CONTRIBUCIONES EMPLEADOR":
                descripcion_limpia = re.sub(r'^CONTRIBUCIONES\s*', '', clave, flags=re.IGNORECASE).strip()
                datos["contribuciones"].append(
                    ContribucionPatronal(
                        descripcion=descripcion_limpia,
                        monto=_parsear_decimal(valor)
                    )
                )
            else:
                datos[clave_upper] = valor

        elif len(partes) == 1:
            texto = partes[0]
            
            # Calculate the visual starting position of the text
            espacios_izq = len(linea) - len(linea.lstrip())
            
            if espacios_izq > 20:
                # Right-aligned: It's a KEY without a value (e.g., "ACREDITADO EN CBU:")
                clave = texto.rstrip(":")
                datos[clave.upper()] = ""
            else:
                # Left-aligned: It's the start of a multi-line VALUE
                if buffer_multilinea:
                    buffer_multilinea += " " + texto
                else:
                    buffer_multilinea = texto

    return datos


def parsear_detalle(texto_detalle: str) -> list[ConceptoLiquidacion]:
    conceptos = []

    for linea in texto_detalle.splitlines():
        if not linea.strip():
            continue

        linea = linea.expandtabs(8)
        match_monto = MONTO_DETALLE_PATTERN.search(linea)
        
        if not match_monto:
            continue

        monto_str = match_monto.group(1)
        pos_monto = match_monto.start()

        if pos_monto < LIMITE_REMUNERATIVO:
            tipo = TipoConcepto.REMUNERATIVO
        elif pos_monto < LIMITE_DESCUENTO:
            tipo = TipoConcepto.DESCUENTO
        else:
            tipo = TipoConcepto.NO_REMUNERATIVO

        resto_linea = linea[:pos_monto].rstrip()
        partes = resto_linea.split(maxsplit=2)

        if len(partes) >= 3:
            conceptos.append(
                ConceptoLiquidacion(
                    codigo=partes[0],
                    unidad=partes[1],
                    descripcion=partes[2],
                    tipo_concepto=tipo,
                    monto=_parsear_decimal(monto_str),
                )
            )

    return conceptos


def parsear_recibo_completo(
    texto_cabecera: str, 
    texto_detalle: str, 
    id_empleador: str, 
    id_empleado: str
) -> ReciboSueldo:
    cab = parsear_cabecera(texto_cabecera)
    det = parsear_detalle(texto_detalle)

    empleador = Empleador(
        id_empleador=id_empleador,
        cuit=cab.get("CUIT", ""),
        nombre=cab.get("EMPLEADOR", ""),
        domicilio=cab.get("DOMICILIO", ""),
    )

    empleado = Empleado(
        id_empleador=id_empleador,
        id_empleado=id_empleado,
        legajo=cab.get("LEGAJO", ""),
        nombre=cab.get("NOMBRE", ""),
        cuil=cab.get("CUIL", ""),
        fecha_ingreso=_parsear_fecha(cab.get("FECHA INGRESO", "")),
        fecha_ingreso_reconocida=_parsear_fecha(cab.get("FECHA REAL", "")),
        categoria=cab.get("CATEGORIA", ""),
        calificacion_profesional=cab.get("CALIFICAC.PROFESIONAL", ""),
        banco_deposito=cab.get("BANCO DEPOSITO", ""),
        documento=cab.get("DOCUMENTO", "")
    )

    # Structured extraction block for the Salary Composition
    comp_salarial = ComposicionSalarial(
        sindical=DetalleRubro(
            total=_parsear_decimal(cab.get("TOTAL COSTO SINDICAL", "")),
            empleador=_parsear_decimal(cab.get("COSTO SINDICAL EMPLEADOR", "")),
            trabajador=_parsear_decimal(cab.get("COSTO SINDICAL TRABAJADOR", ""))
        ),
        seguridad_social=DetalleRubro(
            total=_parsear_decimal(cab.get("TOTAL SEGURIDAD SOCIAL", "")),
            empleador=_parsear_decimal(cab.get("SEG.SOCIAL EMPLEADOR", "")),
            trabajador=_parsear_decimal(cab.get("SEG.SOCIAL TRABAJADOR", ""))
        ),
        obra_social=DetalleRubro(
            total=_parsear_decimal(cab.get("TOTAL OBRA SOCIAL", "")),
            empleador=_parsear_decimal(cab.get("OBRA SOCIAL EMPLEADOR", "")),
            trabajador=_parsear_decimal(cab.get("OBRA SOCIAL TRABAJADOR", ""))
        ),
        inssjp=DetalleRubro(
            total=_parsear_decimal(cab.get("TOTAL COSTO INSSJP", "")),
            empleador=_parsear_decimal(cab.get("INSSJP. EMPLEADOR", "")),
            trabajador=_parsear_decimal(cab.get("INSSJP. TRABAJADOR", ""))
        ),
        art=DetalleRubro(
            total=_parsear_decimal(cab.get("TOTAL COSTO ART.", "")),
            empleador=_parsear_decimal(cab.get("ART. EMPLEADOR", "")),
            # If the TXT omits the worker's ART, the _parsear_decimal helper receives "" and returns 0.
            trabajador=_parsear_decimal(cab.get("ART. TRABAJADOR", "")) 
        ),
        scvo=DetalleRubro(
            total=_parsear_decimal(cab.get("TOTAL COSTO SCVO.", "")),
            empleador=_parsear_decimal(cab.get("SCVO. EMPLEADOR", "")),
            trabajador=_parsear_decimal(cab.get("SCVO. TRABAJADOR", ""))
        )
    )

    return ReciboSueldo(
        periodo=_parsear_periodo(cab.get("PERIODO", "ENERO 1900")),
        empleador=empleador,
        empleado=empleado,
        sueldo_basico=_parsear_decimal(cab.get("BASICO POR MES", "")),
        forma_liquidacion=cab.get("FORMA LIQUIDACION", ""),
        fecha_ultimo_aporte=_parsear_fecha(cab.get("FECHA ULTIMO APORTE", "")),
        periodo_ultimo_aporte=_parsear_periodo(cab.get("ULTIMO PERIODO", "ENERO 1900")),
        conceptos=det,
        contribuciones_patronales=cab.get("contribuciones", []),
        
        # New fields
        sueldo_neto_bolsillo=_parsear_decimal(cab.get("SUELDO NETO DE BOLSILLO", "")),
        importe_en_letras=cab.get("IMPORTE EN LETRAS", None),
        cbu_acreditacion=cab.get("ACREDITADO EN CBU", None),
        composicion_salarial=comp_salarial
    )