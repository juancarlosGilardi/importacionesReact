from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal


class DocTransporteCreate(BaseModel):
    importacion_id: int
    tipo: str = "BL"
    numero: str
    transportista: str | None = None
    puerto_origen: str | None = None
    puerto_destino: str | None = None
    fecha_emision: date | None = None
    fecha_embarque: date | None = None
    fecha_arribo: date | None = None
    peso_total_kg: Decimal | None = None
    volumen_total_m3: Decimal | None = None
    cantidad_bultos: int | None = None
    tipo_contenedor: str | None = None
    flete_monto: Decimal | None = None
    flete_moneda: str = "USD"
    seguro_monto: Decimal | None = None
    notas: str | None = None


class DocTransporteUpdate(DocTransporteCreate):
    importacion_id: int | None = None


class DocTransporteOut(BaseModel):
    id: int
    importacion_id: int
    tipo: str
    numero: str
    transportista: str | None = None
    puerto_origen: str | None = None
    puerto_destino: str | None = None
    fecha_emision: date | None = None
    fecha_embarque: date | None = None
    fecha_arribo: date | None = None
    peso_total_kg: Decimal | None = None
    volumen_total_m3: Decimal | None = None
    cantidad_bultos: int | None = None
    tipo_contenedor: str | None = None
    flete_monto: Decimal | None = None
    flete_moneda: str | None = None
    seguro_monto: Decimal | None = None
    notas: str | None = None
    created_at: datetime | None = None
