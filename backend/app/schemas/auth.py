from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=255)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)

class UserPublic(BaseModel):
    id: int
    email: EmailStr
    name: str
    email_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# Token schemas (for email verification and password reset)
class TokenBase(BaseModel):
    token: str

class EmailVerificationRequest(TokenBase):
    pass

class PasswordResetRequest(TokenBase):
    new_password: str = Field(..., min_length=8, max_length=255)

# Resend verification schema
class ResendVerificationRequest(BaseModel):
    email: EmailStr

# Forgot password schema
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

# Change password schema
class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=255)
    new_password: str = Field(..., min_length=8, max_length=255)

# Response messages
class Message(BaseModel):
    detail: str

# Session schemas (for session management)
class SessionInfo(BaseModel):
    id: int
    created_at: datetime
    expires_at: datetime
    last_used_at: Optional[datetime]
    user_agent: Optional[str]
    ip_address: Optional[str]

    class Config:
        orm_mode = True

class SessionList(BaseModel):
    sessions: list[SessionInfo]