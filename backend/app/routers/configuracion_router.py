from fastapi import APIRouter, Depends, HTTPException

from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


@router.get("/secciones")
async def obtener_secciones(user=Depends(get_current_user)):
    return await call_sp(
        "sp_configuracion_obtener_secciones",
        (user["empresa_id"],),
    )


@router.get("")
async def obtener_configuracion(
    seccion: str | None = None,
    user=Depends(get_current_user),
):
    return await call_sp(
        "sp_configuracion_obtener",
        (user["empresa_id"], seccion),
    )


@router.put("")
async def actualizar_configuracion(data: dict, user=Depends(get_current_user)):
    """Actualiza una clave de configuracion. Body: { seccion, clave, valor }"""
    if user.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden modificar la configuracion")
    try:
        return await call_sp(
            "sp_configuracion_actualizar",
            (
                user["empresa_id"],
                data["seccion"],
                data["clave"],
                data["valor"],
            ),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/batch")
async def actualizar_configuracion_batch(data: dict, user=Depends(get_current_user)):
    """Actualiza multiples claves. Body: { seccion, valores: { clave: valor, ... } }"""
    if user.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    seccion = data.get("seccion")
    valores = data.get("valores", {})
    results = []
    for clave, valor in valores.items():
        try:
            r = await call_sp(
                "sp_configuracion_actualizar",
                (user["empresa_id"], seccion, clave, str(valor)),
                fetch_one=True,
            )
            results.append(r)
        except Exception:
            pass
    return {"updated": len(results), "seccion": seccion}
