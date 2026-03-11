from pydantic import BaseModel
from decimal import Decimal


class DashboardMetricas(BaseModel):
    total_ocs: int = 0
    total_importaciones: int = 0
    total_fob: Decimal = Decimal(0)
    total_costo: Decimal = Decimal(0)
    ocs_borrador: int = 0
    ocs_confirmada: int = 0
    ocs_en_transito: int = 0
    ocs_en_aduana: int = 0
    ocs_completada: int = 0
    imp_planificada: int = 0
    imp_en_transito: int = 0
    imp_en_aduana: int = 0
    imp_completada: int = 0


class PipelineItem(BaseModel):
    id: int
    numero: str | None = None
    descripcion: str | None = None
    estado: str
    total_fob: Decimal | None = None
    proveedor: str | None = None
    fecha: str | None = None


class BusquedaGlobalResult(BaseModel):
    tipo: str
    id: int
    titulo: str | None = None
    subtitulo: str | None = None
    estado: str | None = None
