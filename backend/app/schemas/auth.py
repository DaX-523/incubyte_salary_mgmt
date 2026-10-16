from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.schemas.common import Email

# Never stripped: spaces are valid password characters. The cap stops huge inputs being hashed.
Password = Annotated[str, StringConstraints(min_length=1, max_length=256)]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Email
    password: Password


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime


class ProfileOut(BaseModel):
    name: str
    email: str
    organization: str
