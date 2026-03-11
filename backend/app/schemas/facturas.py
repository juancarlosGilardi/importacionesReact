from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal


class FacturaItemCreate(BaseModel):
    oc_item_id: int | None = None
    producto_id: int | None = None
    descripcion: str | None = None
    cantidad: Decimal
    precio_unitario: Decimal
    notas: str | None = None


class FacturaCreate(BaseModel):
    importacion_id: int | None = None
    proveedor_id: int
    numero_factura: str
    fecha_factura: date | None = None
    moneda: str = "USD"
    tipo_cambio: Decimal | None = None
    notas: str | None = None


class FacturaItemOut(BaseModel):
    id: int
    factura_id: int
    oc_item_id: int | None = None
    producto_id: int | None = None
    producto_nombre: str | None = None
    descripcion: str | None = None
    cantidad: Decimal
    precio_unitario: Decimal
    total: Decimal | None = None


class FacturaOut(BaseModel):
    id: int
    importacion_id: int | None = None
    proveedor_id: int
    proveedor_nombre: str | None = None
    numero_factura: str
    fecha_factura: date | None = None
    moneda: str
    tipo_cambio: Decimal | None = None
    subtotal: Decimal | None = None
    total: Decimal | None = None
    notas: str | None = None
    items: list[FacturaItemOut] | None = None
    created_at: datetime | None = None
