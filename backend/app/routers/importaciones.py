from fastapi import APIRouter, Depends, HTTPException
from app.database import call_sp, call_sp_multi
from app.auth.dependencies import get_current_user
from app.schemas.operaciones import ImportacionCreate, ImportacionUpdate, ImportacionAsociarOC

router = APIRouter(prefix="/importaciones", tags=["Importaciones"])


@router.get("/")
async def listar(
    search: str | None = None,
    estado: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user: dict = Depends(get_current_user),
):
    eid = user["empresa_id"]
    data = await call_sp("sp_importacion_listar", (eid, search, estado, page, per_page))
    count = await call_sp("sp_importacion_contar", (eid, search, estado))
    total = count[0]["total"] if count else 0
    return {"data": data, "total": total, "page": page, "per_page": per_page}


@router.get("/{id}")
async def obtener(id: int, user: dict = Depends(get_current_user)):
    results = await call_sp_multi("sp_importacion_obtener", (id, user["empresa_id"]))
    if not results or not results[0]:
        raise HTTPException(404, "Importacion no encontrada")
    return {
        "cabecera": results[0][0],
        "ocs": results[1] if len(results) > 1 else [],
        "duas": results[2] if len(results) > 2 else [],
        "gastos": results[3] if len(results) > 3 else [],
    }


@router.post("/")
async def crear(data: ImportacionCreate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_importacion_crear", (
        eid, data.numero_importacion, data.descripcion, data.via_transporte,
        data.bl_number, data.container_number, data.nombre_nave, data.numero_viaje,
        data.fecha_embarque, data.fecha_arribo_estimada,
        data.agente_aduanero, data.agente_carga, data.notas, uid
    ))
    return rows[0] if rows else {"id": None}


@router.put("/{id}")
async def actualizar(id: int, data: ImportacionUpdate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_importacion_actualizar", (
        id, eid, data.descripcion, data.via_transporte,
        data.bl_number, data.container_number, data.nombre_nave, data.numero_viaje,
        data.fecha_embarque, data.fecha_arribo_estimada, data.fecha_arribo_real,
        data.fecha_desaduanaje, data.agente_aduanero, data.agente_carga,
        data.estado, data.notas, uid
    ))
    return rows[0] if rows else {"affected": 0}


@router.post("/{id}/asociar-oc")
async def asociar_oc(id: int, data: ImportacionAsociarOC, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_importacion_asociar_oc", (id, data.oc_id))
    return rows[0] if rows else {"id": None}


@router.delete("/{id}/desasociar-oc/{oc_id}")
async def desasociar_oc(id: int, oc_id: int, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_importacion_desasociar_oc", (id, oc_id))
    return rows[0] if rows else {"affected": 0}
