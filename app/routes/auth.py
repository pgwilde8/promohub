from fastapi import APIRouter, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-for-authentication-2025")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Replace with real user validation
    if username == "admin" and password == "password":
        token = jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="access_token", value=token, httponly=True)
        return response
    return templates.TemplateResponse("index.html", {"request": request, "error": "Invalid credentials"})
