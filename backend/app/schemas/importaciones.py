from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal


class ImportacionCreate(BaseModel):
    descripcion: str
    via_transporte: str = "maritimo"
    bl_number: str | None = None
    container_number: str | None = None
    fecha_embarque: date | None = None
    fecha_arribo_estimada: date | None = None
    fecha_arribo_real: date | None = None
    agente_aduanero: str | None = None
    notas: str | None = None


class ImportacionUpdate(ImportacionCreate):
    estado: str | None = None


class ImportacionOut(BaseModel):
    id: int
    empresa_id: int
    numero_importacion: str
    descripcion: str | None = None
    fecha_creacion: date | None = None
    bl_number: str | None = None
    container_number: str | None = None
    via_transporte: str
    fecha_embarque: date | None = None
    fecha_arribo_estimada: date | None = None
    fecha_arribo_real: date | None = None
    estado: str
    total_fob_importacion: Decimal | None = None
    total_gastos_importacion: Decimal | None = None
    total_costo_importacion: Decimal | None = None
    agente_aduanero: str | None = None
    total_ocs: int | None = 0
    ocs_asociadas: str | None = None
    notas: str | None = None
    created_at: datetime | None = None


class AsociarOCRequest(BaseModel):
    oc_id: int
