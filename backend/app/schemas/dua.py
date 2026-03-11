from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal


class DUAItemCreate(BaseModel):
    serie: int
    oc_item_id: int | None = None
    producto_id: int | None = None
    descripcion_arancel: str | None = None
    partida_arancelaria_id: int | None = None
    cantidad: Decimal
    peso_kg: Decimal | None = None
    valor_fob: Decimal
    flete: Decimal = Decimal(0)
    seguro: Decimal = Decimal(0)


class DUACreate(BaseModel):
    importacion_id: int
    numero_dua: str
    fecha_numeracion: date | None = None
    aduana: str | None = None
    regimen: str = "10"
    canal: str | None = None
    fecha_levante: date | None = None
    agente_aduanero: str | None = None
    notas: str | None = None


class DUAUpdate(BaseModel):
    numero_dua: str | None = None
    fecha_numeracion: date | None = None
    aduana: str | None = None
    regimen: str | None = None
    canal: str | None = None
    fecha_levante: date | None = None
    agente_aduanero: str | None = None
    notas: str | None = None


class DUAItemOut(BaseModel):
    id: int
    dua_id: int
    serie: int
    oc_item_id: int | None = None
    producto_id: int | None = None
    producto_nombre: str | None = None
    descripcion_arancel: str | None = None
    partida_arancelaria_id: int | None = None
    partida_codigo: str | None = None
    cantidad: Decimal
    peso_kg: Decimal | None = None
    valor_fob: Decimal
    flete: Decimal
    seguro: Decimal
    cif: Decimal | None = None
    ad_valorem: Decimal | None = None
    igv: Decimal | None = None
    ipm: Decimal | None = None
    isc: Decimal | None = None
    percepcion: Decimal | None = None
    total_tributos: Decimal | None = None


class DUAOut(BaseModel):
    id: int
    importacion_id: int
    numero_dua: str
    fecha_numeracion: date | None = None
    aduana: str | None = None
    regimen: str | None = None
    canal: str | None = None
    fecha_levante: date | None = None
    agente_aduanero: str | None = None
    total_fob: Decimal | None = None
    total_flete: Decimal | None = None
    total_seguro: Decimal | None = None
    total_cif: Decimal | None = None
    total_ad_valorem: Decimal | None = None
    total_igv: Decimal | None = None
    total_ipm: Decimal | None = None
    total_percepcion: Decimal | None = None
    total_tributos: Decimal | None = None
    notas: str | None = None
    items: list[DUAItemOut] | None = None
    created_at: datetime | None = None
