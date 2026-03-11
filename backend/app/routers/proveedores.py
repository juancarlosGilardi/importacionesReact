from fastapi import APIRouter, Depends, Query
from app.database import call_sp
from app.auth.dependencies import get_current_user
from app.schemas.catalogos import ProveedorCreate, ProveedorUpdate

router = APIRouter(prefix="/proveedores", tags=["Proveedores"])


@router.get("/")
async def listar(
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user: dict = Depends(get_current_user),
):
    eid = user["empresa_id"]
    data = await call_sp("sp_proveedor_listar", (eid, search, status, page, per_page))
    count = await call_sp("sp_proveedor_contar", (eid, search, status))
    total = count[0]["total"] if count else 0
    return {"data": data, "total": total, "page": page, "per_page": per_page}


@router.get("/{id}")
async def obtener(id: int, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_proveedor_obtener", (id, user["empresa_id"]))
    if not rows:
        from fastapi import HTTPException
        raise HTTPException(404, "Proveedor no encontrado")
    return rows[0]


@router.post("/")
async def crear(data: ProveedorCreate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_proveedor_crear", (
        eid, data.ruc, data.razon_social, data.nombre_comercial,
        data.pais_id, data.direccion, data.email, data.telefono,
        data.contacto_nombre, data.moneda_id, data.incoterm_default,
        data.es_extranjero, uid
    ))
    return rows[0] if rows else {"id": None}


@router.put("/{id}")
async def actualizar(id: int, data: ProveedorUpdate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_proveedor_actualizar", (
        id, eid, data.ruc, data.razon_social, data.nombre_comercial,
        data.pais_id, data.direccion, data.email, data.telefono,
        data.contacto_nombre, data.moneda_id, data.incoterm_default,
        data.es_extranjero, data.status, uid
    ))
    return rows[0] if rows else {"affected": 0}


@router.delete("/{id}")
async def eliminar(id: int, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_proveedor_eliminar", (id, user["empresa_id"]))
    return rows[0] if rows else {"result": "error"}
