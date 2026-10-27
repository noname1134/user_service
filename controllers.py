from fastapi import APIRouter, HTTPException

from schemas import UserCreate, UserUpdate
from services import UserService


router = APIRouter(prefix="/users")
user_service = UserService()


@router.get("/{user_id}")
def get_user(user_id: int):
    res = user_service.get_user(user_id)
    if res is None:
        raise HTTPException(status_code=404, detail="User not found")
    return res


@router.post("")
def create_user(user: UserCreate):
    return user_service.create_user(user)


@router.patch("/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    try:
        res = user_service.update_user(user_id, user)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if res is None:
        raise HTTPException(status_code=404, detail="User not found")
    return res


@router.delete("/{user_id}")
def delete_user(user_id: int):
    if user_service.delete_user(user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}


@router.post("/{user_id}/register")
def register_user(user_id: int):
    res = user_service.register_user(user_id)
    if res is None:
        raise HTTPException(status_code=404, detail="User not found")
    return res