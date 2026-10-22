from datetime import date
from decimal import Decimal

from elab_galvez.domain.models import (
    PeriodoLiquidacion,
    Empleador,
    Empleado,
    ContribucionPatronal,
    ConceptoLiquidacion,
    ReciboSueldo,
    TipoConcepto
)
    
def test_modelo_recibo_57():
    periodo = PeriodoLiquidacion(mes=10, anio=2026)
    
    empleador = Empleador(
        id_empleador='073',
        nombre="COOPERATIVA 1",
        cuit="30-20000000-8",
        domicilio="SAN MARTIN 100 - Santa Fe - Santa Fe",
    )
    
    empleado = Empleado(
        id_empleador='073',
        id_empleado='057',
        legajo='015',
        nombre="TANKIAN SERJ",
        documento="20000000",
        cuil="20-20000000-0",
        fecha_ingreso=date(2020, 12, 10),
        categoria_profesional="B"
    )

    contribuciones = [
        ContribucionPatronal(descripcion="Jubilación (Contrib.)", monto=Decimal("230624.06")),
        ContribucionPatronal(descripcion="LEY 19032 (Contrib.)", monto=Decimal("34047.56")),
        ContribucionPatronal(descripcion="CASFEC (Contrib.)", monto=Decimal("120772.49")),
        ContribucionPatronal(descripcion="OBRA SOCIAL (Contrib.)", monto=Decimal("128901.59")),
        ContribucionPatronal(descripcion="OBRA SOCIAL CON.ADICIONAL", monto=Decimal("8189.75")),
        ContribucionPatronal(descripcion="CONTRIBUCION OSECAC.", monto=Decimal("28000.00")),
        ContribucionPatronal(descripcion="Costo Sindical", monto=Decimal("34373.76")),
    ]

    conceptos = [
        # Haberes Remunerativos
        ConceptoLiquidacion(descripcion="SUELDO BASICO", tipo_concepto=TipoConcepto.REMUNERATIVO, monto=Decimal("1209365.00")),
        ConceptoLiquidacion(descripcion="BONIFIC.POR ANTIGUEDAD", tipo_concepto=TipoConcepto.REMUNERATIVO, monto=Decimal("60468.25")),
        ConceptoLiquidacion(descripcion="PRESENTISMO SEPELIO", tipo_concepto=TipoConcepto.REMUNERATIVO, monto=Decimal("105777.11")),
        ConceptoLiquidacion(descripcion="PREMIO ASIST/PUNT.SEPELIO", tipo_concepto=TipoConcepto.REMUNERATIVO, monto=Decimal("105777.11")),
        ConceptoLiquidacion(descripcion="ADIC.ART.6 INC.D.", tipo_concepto=TipoConcepto.REMUNERATIVO, monto=Decimal("240.00")),
        ConceptoLiquidacion(descripcion="GUARDIA PASIVA SEPELIOS", tipo_concepto=TipoConcepto.REMUNERATIVO, monto=Decimal("666732.36")),
        
        # Haberes No Remunerativos
        ConceptoLiquidacion(descripcion="SUMA FIJA NO REM.6-12/25", tipo_concepto=TipoConcepto.NO_REMUNERATIVO, monto=Decimal("113746.50")),
        ConceptoLiquidacion(descripcion="SUMA FIJA NO REMUN.04/26", tipo_concepto=TipoConcepto.NO_REMUNERATIVO, monto=Decimal("22749.30")),
        
        # Descuentos / Deducciones
        ConceptoLiquidacion(descripcion="CAJA DE JUBILACION", tipo_concepto=TipoConcepto.DESCUENTO, monto=Decimal("236319.58")),
        ConceptoLiquidacion(descripcion="LEY 19032", tipo_concepto=TipoConcepto.DESCUENTO, monto=Decimal("64450.79")),
        ConceptoLiquidacion(descripcion="OSECAC 3%", tipo_concepto=TipoConcepto.DESCUENTO, monto=Decimal("64450.79")),
        ConceptoLiquidacion(descripcion="APORTE ADIC.O.SOCIAL NO.R", tipo_concepto=TipoConcepto.DESCUENTO, monto=Decimal("4094.87")),
        ConceptoLiquidacion(descripcion="C.U.E.C. GALVEZ", tipo_concepto=TipoConcepto.DESCUENTO, monto=Decimal("12000.00")),
        ConceptoLiquidacion(descripcion="RET.SINDICAL (EMP.COM) 2%", tipo_concepto=TipoConcepto.DESCUENTO, monto=Decimal("42967.20")),
        ConceptoLiquidacion(descripcion="FAECYS 0,50%", tipo_concepto=TipoConcepto.DESCUENTO, monto=Decimal("10741.80")),
        ConceptoLiquidacion(descripcion="RET.SIND.2% S/AC.NO REM.", tipo_concepto=TipoConcepto.DESCUENTO, monto=Decimal("2729.92")),
        ConceptoLiquidacion(descripcion="RET.FAECYS 0.5% S/NO REM.", tipo_concepto=TipoConcepto.DESCUENTO, monto=Decimal("682.48")),
        ConceptoLiquidacion(descripcion="DTO.CUOTA ALIMENTOS", tipo_concepto=TipoConcepto.DESCUENTO, monto=Decimal("461604.55")),
    ]

    recibo = ReciboSueldo(
        periodo=periodo,
        empleador=empleador,
        empleado=empleado,
        sueldo_basico=Decimal("1209365.00"),
        conceptos=conceptos,
        contribuciones_patronales=contribuciones
    )

    assert recibo.total_remunerativo == Decimal("2148359.83"), f"Error en Total Remunerativo: {recibo.total_remunerativo}"
    assert recibo.total_no_remunerativo == Decimal("136495.80"), f"Error en Total No Remunerativo: {recibo.total_no_remunerativo}"
    assert recibo.total_descuentos == Decimal("900041.98"), f"Error en Total Descuentos: {recibo.total_descuentos}"
    
    assert recibo.sueldo_bruto == Decimal("2284855.63"), f"Error en Sueldo Bruto: {recibo.sueldo_bruto}"
    assert recibo.sueldo_neto == Decimal("1384813.65"), f"Error en Sueldo Neto: {recibo.sueldo_neto}"
    
    assert recibo.total_contribuciones_patronales == Decimal("584909.21"), f"Error en Contrib. Patronales: {recibo.total_contribuciones_patronales}"
    assert recibo.costo_total_empleador == Decimal("2869764.84"), f"Error en Costo Total: {recibo.costo_total_empleador}"
    

if __name__ == "__main__":
    test_modelo_recibo_57()