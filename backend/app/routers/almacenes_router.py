from fastapi import APIRouter, Depends
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


@router.get("/")
async def listar(status: str | None = None, user=Depends(get_current_user)):
    return await call_sp("sp_almacen_listar", (user["empresa_id"], status))


@router.get("/{id}")
async def obtener(id: int, user=Depends(get_current_user)):
    return await call_sp("sp_almacen_obtener", (id, user["empresa_id"]), fetch_one=True)


@router.post("/")
async def crear(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_almacen_crear",
        (user["empresa_id"], data["codigo"], data["nombre"], data.get("responsable"), data.get("direccion"), data.get("notas")),
        fetch_one=True,
    )


@router.put("/{id}")
async def actualizar(id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_almacen_actualizar",
        (id, user["empresa_id"], data.get("codigo"), data.get("nombre"), data.get("responsable"), data.get("direccion"), data.get("notas"), data.get("status")),
        fetch_one=True,
    )
