import os
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import mysql.connector
import pytest

import repositories
from schemas import UserCreate


@pytest.fixture
def mysql_users(monkeypatch):
    if os.getenv("RUN_MYSQL_TESTS") != "1":
        pytest.skip("Set RUN_MYSQL_TESTS=1 and start compose.test.yaml")

    def connect():
        return mysql.connector.connect(
            host="127.0.0.1",
            port=3310,
            database="users_test",
            user="users_test_user",
            password="local_test_password",
            connection_timeout=10,
        )

    monkeypatch.setattr(repositories, "get_connection", connect)

    repository = repositories.UserRepository()
    created_ids = []

    def create_user():
        user = repository.create_user(
            UserCreate(
                first_name="Alex",
                last_name="Cohen",
                email=f"{uuid4().hex}@example.com",
                age=25,
                address="Tel Aviv",
                joining_date=datetime.fromisoformat("2026-11-02T10:00:00+02:00"),
            )
        )
        created_ids.append(user["id"])
        return user

    try:
        yield SimpleNamespace(
            repository=repository,
            create=create_user,
            connect=connect,
        )
    finally:
        # Delete only records created by this test.
        with connect() as connection:
            with connection.cursor() as cursor:
                for user_id in created_ids:
                    cursor.execute(
                        "DELETE FROM users WHERE id = %s",
                        (user_id,),
                    )
            connection.commit()


def test_create_user_persists_fields_and_default_registration(mysql_users):
    created = mysql_users.create()
    stored = mysql_users.repository.get_user(created["id"])

    assert stored is not None
    assert stored["id"] > 0
    assert stored["first_name"] == "Alex"
    assert stored["last_name"] == "Cohen"
    assert stored["email"] == created["email"]
    assert stored["age"] == 25
    assert stored["address"] == "Tel Aviv"
    assert stored["is_registered"] == 0


def test_joining_date_is_stored_as_utc(mysql_users):
    created = mysql_users.create()

    # Check the raw database value.
    with mysql_users.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT joining_date FROM users WHERE id = %s",
                (created["id"],),
            )
            raw_date = cursor.fetchone()[0]

    # 10:00 at UTC+02:00 must be stored as 08:00 UTC.
    assert raw_date == datetime(2026, 11, 2, 8)

    # Check the repository returns the timezone information too.
    stored = mysql_users.repository.get_user(created["id"])

    assert stored["joining_date"] == datetime(2026, 11, 2, 8, tzinfo=timezone.utc)
    assert stored["joining_date"].utcoffset().total_seconds() == 0


def test_registration_update_persists(mysql_users):
    created = mysql_users.create()
    assert created["is_registered"] == 0

    # This is the repository operation used by register_user.
    mysql_users.repository.update_user(
        created["id"],
        {"is_registered": True},
    )

    stored = mysql_users.repository.get_user(created["id"])

    assert stored["is_registered"] == 1


def test_delete_removes_only_the_requested_user(mysql_users):
    created = mysql_users.create()
    other = mysql_users.create()

    assert mysql_users.repository.delete_user(created["id"]) is True

    assert mysql_users.repository.get_user(created["id"]) is None
    assert mysql_users.repository.get_user(other["id"]) is not None

    # Deleting an already deleted user reports that it does not exist.
    assert mysql_users.repository.delete_user(created["id"]) is None
