from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal


class GastoCreate(BaseModel):
    importacion_id: int
    tipo_gasto_id: int
    proveedor_gasto: str | None = None
    numero_documento: str | None = None
    fecha_documento: date | None = None
    moneda: str = "PEN"
    monto: Decimal
    tipo_cambio: Decimal | None = None
    igv: Decimal | None = None
    total: Decimal | None = None
    notas: str | None = None


class GastoUpdate(GastoCreate):
    importacion_id: int | None = None


class GastoOut(BaseModel):
    id: int
    importacion_id: int
    tipo_gasto_id: int
    tipo_gasto_nombre: str | None = None
    tipo_gasto_categoria: str | None = None
    proveedor_gasto: str | None = None
    numero_documento: str | None = None
    fecha_documento: date | None = None
    moneda: str
    monto: Decimal
    monto_usd: Decimal | None = None
    tipo_cambio: Decimal | None = None
    igv: Decimal | None = None
    total: Decimal | None = None
    notas: str | None = None
    created_at: datetime | None = None


class GastoResumen(BaseModel):
    tipo_gasto_nombre: str
    categoria: str | None = None
    total_monto: Decimal
    total_monto_usd: Decimal | None = None
    cantidad: int
