from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from app.core.config import settings

bearer_scheme = HTTPBearer()
# Prefer settings (dotenv already loaded there)
SUPABASE_JWT_SECRET = settings.SUPABASE_JWT
# Supabase access tokens typically use aud="authenticated"
EXPECTED_AUD = os.getenv("SUPABASE_JWT_AUD", "authenticated")

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> str:
    token = credentials.credentials
    if not SUPABASE_JWT_SECRET:
        # Misconfiguration: backend cannot verify tokens
        raise HTTPException(status_code=500, detail="Auth misconfigured: SUPABASE_JWT is missing")
    try:
        # Inspect header for easier debugging (alg/kid)
        try:
            header = jwt.get_unverified_header(token)
            print("JWT header:", header)
        except Exception:
            pass
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=EXPECTED_AUD,
            options={"require": ["sub", "aud", "exp"]},
        )
        print(
            "JWT payload:",
            {k: payload[k] for k in ("sub", "aud", "exp", "iss") if k in payload},
        )
        return payload["sub"]
    except jwt.PyJWTError as e:
        print("JWT error:", e)
        raise HTTPException(status_code=403, detail="Invalid token: signature/claims")
