import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import Settings, get_settings

basic_auth = HTTPBasic(auto_error=False, realm="LeadForm admin")


def require_admin(
    credentials: HTTPBasicCredentials | None = Depends(basic_auth),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.admin_username.strip() or not settings.admin_password.strip():
        raise HTTPException(503, "Доступ администратора не настроен.")

    username = credentials.username if credentials else ""
    password = credentials.password if credentials else ""
    username_ok = secrets.compare_digest(username.encode(), settings.admin_username.encode())
    password_ok = secrets.compare_digest(password.encode(), settings.admin_password.encode())
    if not (username_ok and password_ok):
        raise HTTPException(
            401,
            "Требуется вход администратора.",
            headers={"WWW-Authenticate": 'Basic realm="LeadForm admin"'},
        )
