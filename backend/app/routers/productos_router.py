from fastapi import APIRouter, Depends, Query
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


@router.get("/")
async def listar(
    search: str | None = None,
    categoria_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    items = await call_sp(
        "sp_producto_listar",
        (user["empresa_id"], search, categoria_id, status, page, per_page),
    )
    total = await call_sp(
        "sp_producto_contar",
        (user["empresa_id"], search, categoria_id, status),
        fetch_one=True,
    )
    return {"items": items, "total": total["total"], "page": page, "per_page": per_page}


@router.get("/{id}")
async def obtener(id: int, user=Depends(get_current_user)):
    row = await call_sp("sp_producto_obtener", (id, user["empresa_id"]), fetch_one=True)
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return row


@router.post("/")
async def crear(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_producto_crear",
        (
            user["empresa_id"],
            data.get("sku"),
            data.get("nombre"),
            data.get("descripcion"),
            data.get("codigo_hs"),
            data.get("categoria_id"),
            data.get("unidad_medida"),
            data.get("peso_kg"),
            data.get("volumen_m3"),
            data.get("proveedor_default_id"),
            data.get("color_ui"),
            data.get("icono_ui"),
            user["user_id"],
        ),
        fetch_one=True,
    )


@router.put("/{id}")
async def actualizar(id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_producto_actualizar",
        (
            id,
            user["empresa_id"],
            data.get("sku"),
            data.get("nombre"),
            data.get("descripcion"),
            data.get("codigo_hs"),
            data.get("categoria_id"),
            data.get("unidad_medida"),
            data.get("peso_kg"),
            data.get("volumen_m3"),
            data.get("proveedor_default_id"),
            data.get("color_ui"),
            data.get("icono_ui"),
            data.get("status"),
            user["user_id"],
        ),
        fetch_one=True,
    )


@router.delete("/{id}")
async def eliminar(id: int, user=Depends(get_current_user)):
    return await call_sp("sp_producto_eliminar", (id, user["empresa_id"]), fetch_one=True)


@router.get("/categorias/lista")
async def listar_categorias(user=Depends(get_current_user)):
    return await call_sp("sp_categoria_listar", (user["empresa_id"],))


@router.post("/categorias")
async def crear_categoria(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_categoria_crear",
        (user["empresa_id"], data.get("nombre"), data.get("descripcion"), data.get("color_ui"), data.get("icono_ui")),
        fetch_one=True,
    )
