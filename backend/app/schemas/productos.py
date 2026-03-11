from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class ProductoCreate(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None = None
    categoria_id: int | None = None
    unidad_medida: str = "UND"
    peso_unitario_kg: Decimal | None = None
    volumen_unitario_m3: Decimal | None = None
    partida_arancelaria_id: int | None = None
    imagen_path: str | None = None


class ProductoUpdate(ProductoCreate):
    pass


class ProductoOut(BaseModel):
    id: int
    empresa_id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    categoria_id: int | None = None
    categoria_nombre: str | None = None
    unidad_medida: str
    peso_unitario_kg: Decimal | None = None
    volumen_unitario_m3: Decimal | None = None
    partida_arancelaria_id: int | None = None
    partida_codigo: str | None = None
    imagen_path: str | None = None
    status: str = "active"
    stock_total: int | None = 0
    created_at: datetime | None = None
