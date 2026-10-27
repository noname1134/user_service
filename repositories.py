from schemas import UserCreate
from database import get_connection
from datetime import timezone

class UserRepository:
    def create_user(self, user: UserCreate):
        joining_date_utc = (user.joining_date.astimezone(timezone.utc).replace(tzinfo=None))
        connection = get_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute("INSERT INTO users (first_name, last_name, email, age, address, joining_date) VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        user.first_name,
                        user.last_name,
                        user.email,
                        user.age,
                        user.address,
                        joining_date_utc,
                    )
                )
                connection.commit()
                user_id = cursor.lastrowid
            finally:
                cursor.close()
        finally:
            connection.close()

        return self.get_user(user_id)

    @staticmethod
    def get_user(user_id: int):
        connection = get_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                result = cursor.fetchone()
                return result
            finally:
                cursor.close()
        finally:
            connection.close()


    def update_user(self, user_id: int, changes: dict):
        allowed_fields = {
            "first_name", "last_name", "email", "age",
            "address", "joining_date", "is_registered"
        }

        if not changes:
            return self.get_user(user_id)

        if not set(changes).issubset(allowed_fields):
            raise ValueError("Unsupported update field")

        changes = changes.copy()
        if "joining_date" in changes:
            changes["joining_date"] = (changes["joining_date"].astimezone(timezone.utc).replace(tzinfo=None))

        set_clause = ", ".join(f"{column} = %s" for column in changes)
        values = tuple(changes.values()) + (user_id,)

        connection = get_connection()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute("UPDATE users SET " + set_clause + " WHERE id = %s", values)
                connection.commit()
            finally:
                cursor.close()
        finally:
            connection.close()

        return self.get_user(user_id)


    @staticmethod
    def delete_user(user_id: int):
        connection = get_connection()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute("DELETE FROM users WHERE id = %s",(user_id,))
                deleted_count = cursor.rowcount
                connection.commit()
            finally:
                cursor.close()
        finally:
            connection.close()
        if deleted_count == 0:
            return None
        return True