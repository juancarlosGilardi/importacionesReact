from fastapi import APIRouter, HTTPException, status
from passlib.hash import bcrypt
from app.database import execute_query
from app.auth.jwt import create_token
from app.schemas.auth import LoginRequest, LoginResponse, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    rows = await execute_query(
        "SELECT id, empresa_id, email, password_hash, nombre, apellido, rol, status "
        "FROM usuarios WHERE email = %s LIMIT 1",
        (data.email,),
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")

    user = rows[0]
    if user["status"] != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo o bloqueado")

    if not bcrypt.verify(data.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")

    # Actualizar ultimo_login
    await execute_query("UPDATE usuarios SET ultimo_login = NOW() WHERE id = %s", (user["id"],))

    token = create_token(user["id"], user["empresa_id"], user["email"], user["rol"])
    return LoginResponse(
        token=token,
        user=UserOut(
            id=user["id"],
            empresa_id=user["empresa_id"],
            email=user["email"],
            nombre=user["nombre"],
            apellido=user["apellido"],
            rol=user["rol"],
        ),
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = __import__("fastapi").Depends(
    __import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user
)):
    rows = await execute_query(
        "SELECT id, empresa_id, email, nombre, apellido, rol FROM usuarios WHERE id = %s",
        (current_user["sub"],),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    u = rows[0]
    return UserOut(**u)
