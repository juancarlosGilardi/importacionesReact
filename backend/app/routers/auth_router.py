from fastapi import APIRouter, HTTPException, status, Depends
from ..database import call_sp, pool
from ..auth import hash_password, verify_password, create_token, get_current_user
from ..schemas.auth import LoginRequest, RegisterRequest, TokenResponse
import aiomysql

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT u.*, e.razon_social AS empresa_nombre "
                "FROM usuarios u JOIN empresas e ON u.empresa_id = e.id "
                "WHERE u.email = %s AND u.status = 'active'",
                (req.email,),
            )
            user = await cur.fetchone()

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    token = create_token({
        "user_id": user["id"],
        "empresa_id": user["empresa_id"],
        "email": user["email"],
        "nombre": user["nombre"],
        "rol": user["rol"],
    })

    return TokenResponse(
        access_token=token,
        user={
            "id": user["id"],
            "email": user["email"],
            "nombre": user["nombre"],
            "apellido": user["apellido"],
            "rol": user["rol"],
            "empresa_id": user["empresa_id"],
            "empresa_nombre": user.get("empresa_nombre"),
        },
    )


@router.post("/register")
async def register(req: RegisterRequest):
    hashed = hash_password(req.password)

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT id FROM usuarios WHERE email = %s", (req.email,))
            if await cur.fetchone():
                raise HTTPException(status_code=400, detail="Email ya registrado")

            empresa_id = 1
            if req.empresa_ruc and req.empresa_nombre:
                await cur.execute(
                    "INSERT INTO empresas (ruc, razon_social, nombre_comercial) VALUES (%s, %s, %s)",
                    (req.empresa_ruc, req.empresa_nombre, req.empresa_nombre),
                )
                empresa_id = cur.lastrowid

            await cur.execute(
                "INSERT INTO usuarios (empresa_id, email, password_hash, nombre, apellido, rol) "
                "VALUES (%s, %s, %s, %s, %s, 'admin')",
                (empresa_id, req.email, hashed, req.nombre, req.apellido),
            )
            user_id = cur.lastrowid

    token = create_token({
        "user_id": user_id,
        "empresa_id": empresa_id,
        "email": req.email,
        "nombre": req.nombre,
        "rol": "admin",
    })

    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def me(user=Depends(get_current_user)):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT u.id, u.email, u.nombre, u.apellido, u.rol, u.empresa_id, "
                "e.razon_social AS empresa_nombre "
                "FROM usuarios u JOIN empresas e ON u.empresa_id = e.id "
                "WHERE u.id = %s",
                (user["user_id"],),
            )
            row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return row
