from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal


class OCItemCreate(BaseModel):
    producto_id: int
    cantidad: Decimal
    precio_unitario_fob: Decimal
    peso_total_kg: Decimal | None = None
    volumen_total_m3: Decimal | None = None
    notas: str | None = None


class OCItemUpdate(BaseModel):
    cantidad: Decimal
    precio_unitario_fob: Decimal
    peso_total_kg: Decimal | None = None
    volumen_total_m3: Decimal | None = None
    notas: str | None = None


class OCItemOut(BaseModel):
    id: int
    oc_id: int
    producto_id: int
    producto_codigo: str | None = None
    producto_nombre: str | None = None
    cantidad: Decimal
    precio_unitario_fob: Decimal
    total_fob: Decimal
    peso_total_kg: Decimal | None = None
    volumen_total_m3: Decimal | None = None
    notas: str | None = None


class OCCreate(BaseModel):
    proveedor_id: int
    fecha_orden: date | None = None
    moneda: str = "USD"
    tipo_cambio: Decimal | None = None
    incoterm: str = "FOB"
    notas: str | None = None


class OCUpdate(BaseModel):
    proveedor_id: int | None = None
    fecha_orden: date | None = None
    moneda: str | None = None
    tipo_cambio: Decimal | None = None
    incoterm: str | None = None
    notas: str | None = None


class OCOut(BaseModel):
    id: int
    empresa_id: int
    numero_oc: str
    proveedor_id: int
    proveedor: str | None = None
    proveedor_comercial: str | None = None
    pais_codigo: str | None = None
    pais_origen: str | None = None
    fecha_orden: date | None = None
    moneda: str
    moneda_simbolo: str | None = None
    tipo_cambio: Decimal | None = None
    incoterm: str
    estado: str
    estado_nombre: str | None = None
    estado_color: str | None = None
    total_fob: Decimal = Decimal(0)
    total_cif: Decimal | None = None
    total_costo_importacion: Decimal | None = None
    total_items: int | None = 0
    total_cantidad: Decimal | None = None
    notas: str | None = None
    items: list[OCItemOut] | None = None
    created_at: datetime | None = None
