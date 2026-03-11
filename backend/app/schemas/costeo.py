from pydantic import BaseModel
from decimal import Decimal


# --- GASTOS ---
class GastoCreate(BaseModel):
    importacion_id: int | None = None
    oc_id: int | None = None
    tipo_gasto_codigo: str
    descripcion: str | None = None
    proveedor_ruc: str | None = None
    proveedor_nombre: str | None = None
    moneda_id: int | None = 1
    monto: Decimal
    tipo_cambio: Decimal | None = Decimal("1.0000")
    numero_comprobante: str | None = None
    fecha_gasto: str | None = None
    comprobante_path: str | None = None
    notas: str | None = None

class GastoUpdate(BaseModel):
    tipo_gasto_codigo: str | None = None
    descripcion: str | None = None
    proveedor_ruc: str | None = None
    proveedor_nombre: str | None = None
    moneda_id: int | None = None
    monto: Decimal | None = None
    tipo_cambio: Decimal | None = None
    numero_comprobante: str | None = None
    fecha_gasto: str | None = None
    estado: str | None = None
    notas: str | None = None


# --- PRORRATEO ---
class ProrrateoCalcular(BaseModel):
    importacion_id: int
    oc_id: int
    metodo: str | None = "valor_fob"

class ProrrateoAplicar(BaseModel):
    prorrateo_id: int
