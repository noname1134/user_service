import pytest

from exceptions import PollServiceUnavailableError


def test_create_user(user_api, user_payload):
    client, repository, _ = user_api

    response = client.post("/users", json=user_payload)

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["email"] == user_payload["email"]
    assert response.json()["is_registered"] is False

    repository.create_user.assert_called_once()
    submitted = repository.create_user.call_args.args[0]
    assert submitted.email == user_payload["email"]
    assert submitted.age == user_payload["age"]


@pytest.mark.parametrize(
    "changes",
    [
        {"age": -1},
        {"age": 120},
        {"first_name": ""},
        {"joining_date": "2026-11-02T10:00:00"},
    ],
)
def test_invalid_user_is_rejected(user_api, user_payload, changes):
    client, repository, _ = user_api

    response = client.post(
        "/users",
        json={**user_payload, **changes},
    )

    assert response.status_code == 422
    repository.create_user.assert_not_called()


def test_get_missing_user(user_api):
    client, repository, _ = user_api
    repository.get_user.return_value = None

    response = client.get("/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_register_user(user_api):
    client, repository, _ = user_api

    response = client.post("/users/1/register")

    assert response.status_code == 200
    assert response.json()["is_registered"] is True
    repository.update_user.assert_called_once_with(1, {"is_registered": True})


def test_register_missing_user(user_api):
    client, repository, _ = user_api
    repository.update_user.return_value = None

    response = client.post("/users/999/register")

    assert response.status_code == 404


def test_delete_cleans_up_answers_before_deleting_user(user_api):
    client, repository, poll_client = user_api

    def check_cleanup_order(user_id):
        assert user_id == 1
        repository.delete_user.assert_not_called()

    poll_client.delete_user_answers.side_effect = check_cleanup_order

    response = client.delete("/users/1")

    assert response.status_code == 200
    assert response.json() == {"message": "User deleted"}
    poll_client.delete_user_answers.assert_called_once_with(1)
    repository.delete_user.assert_called_once_with(1)


def test_poll_failure_prevents_user_deletion(user_api):
    client, repository, poll_client = user_api

    poll_client.delete_user_answers.side_effect = PollServiceUnavailableError(
        "Could not reach the poll service"
    )

    response = client.delete("/users/1")

    assert response.status_code == 503
    poll_client.delete_user_answers.assert_called_once_with(1)
    repository.delete_user.assert_not_called()


def test_delete_missing_user_does_not_call_poll_service(user_api):
    client, repository, poll_client = user_api
    repository.get_user.return_value = None

    response = client.delete("/users/999")

    assert response.status_code == 404
    poll_client.delete_user_answers.assert_not_called()
    repository.delete_user.assert_not_called()


def test_null_update_is_rejected(user_api):
    client, repository, _ = user_api

    response = client.patch(
        "/users/1",
        json={"first_name": None},
    )

    assert response.status_code == 422
    repository.update_user.assert_not_called()
