from fastapi import APIRouter, Depends, HTTPException

from ..database import call_sp
from ..auth import get_current_user, hash_password

router = APIRouter()


def require_admin(user: dict):
    if user.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden realizar esta accion")


@router.get("")
async def listar_usuarios(
    search: str | None = None,
    rol: str | None = None,
    status: str | None = None,
    user=Depends(get_current_user),
):
    require_admin(user)
    return await call_sp(
        "sp_usuario_listar",
        (user["empresa_id"], search, rol, status),
    )


@router.get("/{id}")
async def obtener_usuario(id: int, user=Depends(get_current_user)):
    require_admin(user)
    result = await call_sp(
        "sp_usuario_obtener",
        (id, user["empresa_id"]),
        fetch_one=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return result


@router.post("")
async def crear_usuario(data: dict, user=Depends(get_current_user)):
    require_admin(user)
    try:
        password_hash = hash_password(data["password"])
        return await call_sp(
            "sp_usuario_crear",
            (
                user["empresa_id"],
                data["email"],
                password_hash,
                data["nombre"],
                data["apellido"],
                data.get("rol", "usuario"),
                data.get("almacen_default_id"),
            ),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id}")
async def actualizar_usuario(id: int, data: dict, user=Depends(get_current_user)):
    require_admin(user)
    try:
        return await call_sp(
            "sp_usuario_actualizar",
            (
                id,
                user["empresa_id"],
                data.get("nombre"),
                data.get("apellido"),
                data.get("rol"),
                data.get("status"),
                data.get("almacen_default_id"),
            ),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/reset-password")
async def reset_password(id: int, data: dict, user=Depends(get_current_user)):
    require_admin(user)
    try:
        new_hash = hash_password(data["password"])
        return await call_sp(
            "sp_usuario_reset_password",
            (id, user["empresa_id"], new_hash),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/desactivar")
async def desactivar_usuario(id: int, user=Depends(get_current_user)):
    require_admin(user)
    try:
        return await call_sp(
            "sp_usuario_desactivar",
            (id, user["empresa_id"], user["user_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/activar")
async def activar_usuario(id: int, user=Depends(get_current_user)):
    require_admin(user)
    try:
        return await call_sp(
            "sp_usuario_activar",
            (id, user["empresa_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
