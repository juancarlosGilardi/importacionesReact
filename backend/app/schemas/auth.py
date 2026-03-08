from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    nombre: str
    apellido: str
    empresa_ruc: str | None = None
    empresa_nombre: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    nombre: str
    apellido: str
    rol: str
    empresa_id: int
    empresa_nombre: str | None = None
