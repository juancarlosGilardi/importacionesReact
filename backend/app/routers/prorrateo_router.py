from fastapi import APIRouter, Depends
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


@router.post("/calcular")
async def calcular(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_prorrateo_calcular",
        (
            user["empresa_id"],
            data["importacion_id"],
            data["oc_id"],
            data.get("metodo", "valor_fob"),
            user["user_id"],
        ),
        fetch_one=True,
    )


@router.post("/{id}/aplicar")
async def aplicar(id: int, user=Depends(get_current_user)):
    return await call_sp(
        "sp_prorrateo_aplicar",
        (id, user["empresa_id"], user["user_id"]),
        fetch_one=True,
    )


@router.get("/{id}")
async def obtener(id: int, user=Depends(get_current_user)):
    results = await call_sp("sp_prorrateo_obtener", (id, user["empresa_id"]), multi=True)
    return {
        "cabecera": results[0][0] if results and results[0] else None,
        "detalle": results[1] if len(results) > 1 else [],
    }


@router.get("/ficha-costeo/{oc_id}")
async def ficha_costeo(oc_id: int, user=Depends(get_current_user)):
    results = await call_sp("sp_ficha_costeo_oc", (oc_id, user["empresa_id"]), multi=True)
    return {
        "cabecera": results[0][0] if results and results[0] else None,
        "items": results[1] if len(results) > 1 else [],
        "gastos": results[2] if len(results) > 2 else [],
    }
