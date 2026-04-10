from pydantic import BaseModel


class Token(BaseModel):
    """Returned after successful login."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """What lives inside the JWT payload."""
    user_id: str
    email: str
    is_admin: bool