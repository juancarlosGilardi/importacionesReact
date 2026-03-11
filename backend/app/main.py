from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_pool, close_pool

from app.auth.router import router as auth_router
from app.routers.catalogos import router as catalogos_router
from app.routers.proveedores import router as proveedores_router
from app.routers.productos import router as productos_router
from app.routers.almacenes import router as almacenes_router
from app.routers.ordenes_compra import router as oc_router
from app.routers.importaciones import router as importaciones_router
from app.routers.documentos import router as documentos_router
from app.routers.costeo import router as costeo_router
from app.routers.inventario import router as inventario_router
from app.routers.dashboard import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: crear pool de conexiones
    await get_pool()
    yield
    # Shutdown: cerrar pool
    await close_pool()


app = FastAPI(
    title="ImportCost Pro API",
    description="Sistema de Importaciones y Costeo para PYMES peruanas",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prefijo /api para todos los routers
app.include_router(auth_router, prefix="/api")
app.include_router(catalogos_router, prefix="/api")
app.include_router(proveedores_router, prefix="/api")
app.include_router(productos_router, prefix="/api")
app.include_router(almacenes_router, prefix="/api")
app.include_router(oc_router, prefix="/api")
app.include_router(importaciones_router, prefix="/api")
app.include_router(documentos_router, prefix="/api")
app.include_router(costeo_router, prefix="/api")
app.include_router(inventario_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ImportCost Pro API"}
