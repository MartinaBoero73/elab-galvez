from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

Dinero = Decimal

class PeriodoLiquidacion(BaseModel):
    """Receipt billing period (month and year)."""
    mes: int = Field(ge=1, le=12)
    anio: int = Field(ge=1900, le=2200)

class Empleador(BaseModel):
    """Employer who issued the receipt."""
    id_empleador: str = Field(pattern=r"^\d{3}$")
    cuit: str
    nombre: str
    domicilio: str

class Empleado(BaseModel):
    """Employee details."""
    cuil: str | None = None
    id_empleador: str = Field(pattern=r"^\d{3}$")
    id_empleado: str = Field(pattern=r"^\d{3}$")
    legajo: str
    nombre: str
    fecha_ingreso: date | None = None
    fecha_ingreso_reconocida: date | None = None # Recognized entry date (FEC.ING.REC.)
    categoria_profesional: str | None = None
    banco_deposito: str | None = None
    documento: str | None = None

class TipoConcepto(StrEnum):
    """The three standard columns of the Argentine salary composition."""
    REMUNERATIVO = "remunerativo"
    NO_REMUNERATIVO = "no_remunerativo"
    DESCUENTO = "descuento"

class ConceptoLiquidacion(BaseModel):
    """An item in the earnings and deductions detail grid."""
    codigo: str | None = None
    descripcion: str
    tipo_concepto: TipoConcepto
    unidad: str | Decimal | None = None # Can be days (e.g., 30), hours, or percentages (11%)
    base_calculo: Dinero | None = None
    
    monto: Dinero

class ContribucionPatronal(BaseModel):
    """An employer contribution or payroll tax exclusively borne by the employer."""
    descripcion: str
    unidad_porcentaje: str | Decimal | None = None
    base_calculo: Dinero | None = None
    monto: Dinero

class DetalleRubro(BaseModel):
    """Represents a single row in the Salary Composition table."""
    total: Decimal = Decimal("0.0")
    empleador: Decimal = Decimal("0.0")
    trabajador: Decimal = Decimal("0.0")

class ComposicionSalarial(BaseModel):
    """
    All categories demanded by the new law.
    """
    sindical: DetalleRubro = Field(default_factory=DetalleRubro)
    seguridad_social: DetalleRubro = Field(default_factory=DetalleRubro)
    obra_social: DetalleRubro = Field(default_factory=DetalleRubro)
    inssjp: DetalleRubro = Field(default_factory=DetalleRubro)
    art: DetalleRubro = Field(default_factory=DetalleRubro)
    scvo: DetalleRubro = Field(default_factory=DetalleRubro)

class ReciboSueldo(BaseModel):
    """Master model that consolidates the entire payslip."""
    model_config = ConfigDict(validate_assignment=True)

    periodo: PeriodoLiquidacion
    empleador: Empleador
    empleado: Empleado

    sueldo_basico: Decimal | None = None
    forma_liquidacion: str = "MENSUAL"
    
    conceptos: list[ConceptoLiquidacion] = Field(default_factory=list)
    contribuciones_patronales: list[ContribucionPatronal] = Field(default_factory=list)
    sueldo_neto_bolsillo: Decimal = Decimal("0.0")
    importe_en_letras: Optional[str] = None
    cbu_acreditacion: Optional[str] = None

    # this is the new component demanded by the new law passed in Argentina
    composicion_salarial: ComposicionSalarial = Field(default_factory=ComposicionSalarial)
    
    fecha_ultimo_aporte: date | None = None
    periodo_ultimo_aporte: PeriodoLiquidacion | None = None

    @property
    def total_remunerativo(self) -> Dinero:
        return sum(
            (c.monto for c in self.conceptos if c.tipo_concepto == TipoConcepto.REMUNERATIVO),
            start=Decimal("0"),
        )
        
    @property
    def total_no_remunerativo(self) -> Dinero:
        return sum(
            (c.monto for c in self.conceptos if c.tipo_concepto == TipoConcepto.NO_REMUNERATIVO),
            start=Decimal("0"),
        )

    @property
    def total_descuentos(self) -> Dinero:
        return sum(
            (c.monto for c in self.conceptos if c.tipo_concepto == TipoConcepto.DESCUENTO),
            start=Decimal("0"),
        )

    @property
    def sueldo_bruto(self) -> Dinero:
        """The sum of all employee earnings before deductions (Gross Salary)."""
        return self.total_remunerativo + self.total_no_remunerativo

    @property
    def sueldo_neto(self) -> Dinero:
        """The actual out-of-pocket amount transferred to the employee (Net Salary)."""
        return self.total_remunerativo + self.total_no_remunerativo - self.total_descuentos

    @property
    def total_contribuciones_patronales(self) -> Dinero:
        return sum(
            (c.monto for c in self.contribuciones_patronales),
            start=Decimal("0"),
        )
        
    @property
    def costo_total_empleador(self) -> Dinero:
        """Required global metric: Gross Salary + Employer Contributions."""
        return self.sueldo_bruto + self.total_contribuciones_patronales