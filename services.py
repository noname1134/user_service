from schemas import UserCreate, UserUpdate
from repositories import UserRepository
from clients import PollClient


class UserService:
    def __init__(self):
        self.repository = UserRepository()
        self.poll_client = PollClient()

    def create_user(self, user: UserCreate):
        return self.repository.create_user(user)

    def get_user(self, user_id: int):
        return self.repository.get_user(user_id)

    def update_user(self, user_id: int, update: UserUpdate):
        changes = update.model_dump(exclude_unset=True)
        if any(value is None for value in changes.values()):
            raise ValueError("User fields cannot be null")
        return self.repository.update_user(user_id, changes)

    def delete_user(self, user_id: int):
        user = self.repository.get_user(user_id)
        if user is None:
            return None

        self.poll_client.delete_user_answers(user_id)
        return self.repository.delete_user(user_id)


    def register_user(self, user_id: int):
        return self.repository.update_user(user_id, {"is_registered": True})