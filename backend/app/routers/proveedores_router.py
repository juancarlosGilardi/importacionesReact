import math
from fastapi import APIRouter, Depends, Query
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


@router.get("/")
async def listar(
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    items = await call_sp(
        "sp_proveedor_listar",
        (user["empresa_id"], search, status, page, per_page),
    )
    total = await call_sp(
        "sp_proveedor_contar",
        (user["empresa_id"], search, status),
        fetch_one=True,
    )
    total_count = total["total"]
    return {
        "items": items,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total_count / per_page) if per_page > 0 else 0,
    }


@router.get("/{id}")
async def obtener(id: int, user=Depends(get_current_user)):
    row = await call_sp("sp_proveedor_obtener", (id, user["empresa_id"]), fetch_one=True)
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return row


@router.post("/")
async def crear(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_proveedor_crear",
        (
            user["empresa_id"],
            data.get("ruc"),
            data.get("razon_social"),
            data.get("nombre_comercial"),
            data.get("pais_id"),
            data.get("direccion"),
            data.get("email"),
            data.get("telefono"),
            data.get("contacto_nombre"),
            data.get("moneda_id"),
            data.get("incoterm_default"),
            data.get("es_extranjero", 1),
            user["user_id"],
        ),
        fetch_one=True,
    )


@router.put("/{id}")
async def actualizar(id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_proveedor_actualizar",
        (
            id,
            user["empresa_id"],
            data.get("ruc"),
            data.get("razon_social"),
            data.get("nombre_comercial"),
            data.get("pais_id"),
            data.get("direccion"),
            data.get("email"),
            data.get("telefono"),
            data.get("contacto_nombre"),
            data.get("moneda_id"),
            data.get("incoterm_default"),
            data.get("es_extranjero"),
            data.get("status"),
            user["user_id"],
        ),
        fetch_one=True,
    )


@router.delete("/{id}")
async def eliminar(id: int, user=Depends(get_current_user)):
    return await call_sp("sp_proveedor_eliminar", (id, user["empresa_id"]), fetch_one=True)
