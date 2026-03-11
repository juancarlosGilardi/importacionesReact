from fastapi import APIRouter, Depends, HTTPException
from app.database import call_sp
from app.auth.dependencies import get_current_user
from app.schemas.catalogos import AlmacenCreate, AlmacenUpdate

router = APIRouter(prefix="/almacenes", tags=["Almacenes"])


@router.get("/")
async def listar(status: str | None = None, user: dict = Depends(get_current_user)):
    return await call_sp("sp_almacen_listar", (user["empresa_id"], status))


@router.get("/{id}")
async def obtener(id: int, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_almacen_obtener", (id, user["empresa_id"]))
    if not rows:
        raise HTTPException(404, "Almacen no encontrado")
    return rows[0]


@router.post("/")
async def crear(data: AlmacenCreate, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_almacen_crear", (
        user["empresa_id"], data.codigo, data.nombre,
        data.responsable, data.direccion, data.notas
    ))
    return rows[0] if rows else {"id": None}


@router.put("/{id}")
async def actualizar(id: int, data: AlmacenUpdate, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_almacen_actualizar", (
        id, user["empresa_id"], data.codigo, data.nombre,
        data.responsable, data.direccion, data.notas, data.status
    ))
    return rows[0] if rows else {"affected": 0}
