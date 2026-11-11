from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from app.config import settings
from app.schemas import Token, UserLogin

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token", auto_error=False)

# Dedicated Accounts for Admin and Approver
SYSTEM_USERS: Dict[str, Dict[str, Any]] = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "full_name": "Cloud Operations Admin",
        "permissions": ["all", "scan", "seed", "remediate", "approve", "view_audit"]
    },
    "approver": {
        "password": "approver123",
        "role": "approver",
        "full_name": "Governance & Security Approver",
        "permissions": ["approve", "reject", "view_findings", "test_sandbox"]
    }
}

class UserProfileOut(BaseModel):
    username: str
    role: str
    full_name: str
    permissions: List[str]

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileOut

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.post("/login", response_model=LoginResponse)
def login_with_json(login_req: UserLogin):
    """JSON-based login endpoint for the frontend dashboard."""
    username = login_req.username.strip().lower()
    user_info = SYSTEM_USERS.get(username)

    if not user_info or user_info["password"] != login_req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Use 'admin'/'admin123' or 'approver'/'approver123'."
        )

    token = create_access_token(data={
        "sub": username,
        "role": user_info["role"],
        "full_name": user_info["full_name"]
    })

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfileOut(
            username=username,
            role=user_info["role"],
            full_name=user_info["full_name"],
            permissions=user_info["permissions"]
        )
    )

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 Form Data compatibility endpoint."""
    username = form_data.username.strip().lower()
    user_info = SYSTEM_USERS.get(username)

    if not user_info or user_info["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={
        "sub": username,
        "role": user_info["role"],
        "full_name": user_info["full_name"]
    })

    return Token(
        access_token=token,
        token_type="bearer",
        username=username,
        role=user_info["role"]
    )

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Dependency to retrieve and validate authenticated user."""
    if not token:
        # Fallback to default admin in demo mode if unauthenticated
        return {"username": "admin", "role": "admin", "full_name": "Cloud Admin"}

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        role = payload.get("role", "admin")
        full_name = payload.get("full_name", username)
        return {"username": username, "role": role, "full_name": full_name}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials token")

@router.get("/me", response_model=UserProfileOut)
def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_info = SYSTEM_USERS.get(current_user["username"], {
        "role": current_user.get("role", "admin"),
        "full_name": current_user.get("full_name", current_user["username"]),
        "permissions": ["all"]
    })
    return UserProfileOut(
        username=current_user["username"],
        role=user_info["role"],
        full_name=user_info["full_name"],
        permissions=user_info.get("permissions", ["all"])
    )
