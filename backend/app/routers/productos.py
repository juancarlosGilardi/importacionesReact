from fastapi import APIRouter, Depends, HTTPException
from app.database import call_sp
from app.auth.dependencies import get_current_user
from app.schemas.catalogos import ProductoCreate, ProductoUpdate

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.get("/")
async def listar(
    search: str | None = None,
    categoria_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user: dict = Depends(get_current_user),
):
    eid = user["empresa_id"]
    data = await call_sp("sp_producto_listar", (eid, search, categoria_id, status, page, per_page))
    count = await call_sp("sp_producto_contar", (eid, search, categoria_id, status))
    total = count[0]["total"] if count else 0
    return {"data": data, "total": total, "page": page, "per_page": per_page}


@router.get("/{id}")
async def obtener(id: int, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_producto_obtener", (id, user["empresa_id"]))
    if not rows:
        raise HTTPException(404, "Producto no encontrado")
    return rows[0]


@router.post("/")
async def crear(data: ProductoCreate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_producto_crear", (
        eid, data.sku, data.nombre, data.descripcion, data.codigo_hs,
        data.categoria_id, data.unidad_medida, data.peso_kg, data.volumen_m3,
        data.proveedor_default_id, data.color_ui, data.icono_ui, uid
    ))
    return rows[0] if rows else {"id": None}


@router.put("/{id}")
async def actualizar(id: int, data: ProductoUpdate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_producto_actualizar", (
        id, eid, data.sku, data.nombre, data.descripcion, data.codigo_hs,
        data.categoria_id, data.unidad_medida, data.peso_kg, data.volumen_m3,
        data.proveedor_default_id, data.color_ui, data.icono_ui, data.status, uid
    ))
    return rows[0] if rows else {"affected": 0}


@router.delete("/{id}")
async def eliminar(id: int, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_producto_eliminar", (id, user["empresa_id"]))
    return rows[0] if rows else {"result": "error"}
