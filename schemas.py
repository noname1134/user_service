from pydantic import BaseModel, Field, AwareDatetime


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str
    age: int = Field(ge=0, lt=120)
    address: str
    joining_date: AwareDatetime


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = None
    age: int | None = Field(default=None, ge=0, lt=120)
    address: str | None = None
    joining_date: AwareDatetime | None = None