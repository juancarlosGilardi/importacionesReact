from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    empresa_id: int
    email: str
    nombre: str
    apellido: str
    rol: str


class LoginResponse(BaseModel):
    token: str
    user: UserOut


class RegisterRequest(BaseModel):
    empresa_id: int
    email: EmailStr
    password: str
    nombre: str
    apellido: str
    rol: str | None = "usuario"
