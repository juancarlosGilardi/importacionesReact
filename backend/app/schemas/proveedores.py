from pydantic import BaseModel
from datetime import datetime


class ProveedorCreate(BaseModel):
    razon_social: str
    nombre_comercial: str | None = None
    ruc: str | None = None
    tax_id: str | None = None
    pais_id: int | None = None
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None
    contacto_nombre: str | None = None
    contacto_telefono: str | None = None
    contacto_email: str | None = None
    moneda_default: str | None = "USD"
    notas: str | None = None


class ProveedorUpdate(ProveedorCreate):
    pass


class ProveedorOut(BaseModel):
    id: int
    empresa_id: int
    razon_social: str
    nombre_comercial: str | None = None
    ruc: str | None = None
    tax_id: str | None = None
    pais_id: int | None = None
    pais_nombre: str | None = None
    pais_codigo: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None
    contacto_nombre: str | None = None
    contacto_telefono: str | None = None
    contacto_email: str | None = None
    moneda_default: str | None = None
    notas: str | None = None
    status: str = "active"
    total_ocs: int | None = 0
    created_at: datetime | None = None
