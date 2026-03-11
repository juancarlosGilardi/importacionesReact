from pydantic import BaseModel
from datetime import datetime


class AlmacenCreate(BaseModel):
    nombre: str
    codigo: str | None = None
    direccion: str | None = None
    tipo: str = "propio"


class AlmacenUpdate(AlmacenCreate):
    pass


class AlmacenOut(BaseModel):
    id: int
    empresa_id: int
    nombre: str
    codigo: str | None = None
    direccion: str | None = None
    tipo: str
    status: str = "active"
    total_productos: int | None = 0
    total_stock: int | None = 0
    created_at: datetime | None = None
