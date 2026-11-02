from datetime import datetime, timezone
from importlib import import_module
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def user_payload():
    return {
        "first_name": "Alex",
        "last_name": "Cohen",
        "email": "alex@example.com",
        "age": 25,
        "address": "Tel Aviv",
        "joining_date": "2026-11-02T10:00:00+00:00",
    }


@pytest.fixture
def user_record(user_payload):
    return {
        **user_payload,
        "id": 1,
        "joining_date": datetime(2026, 11, 2, 10, tzinfo=timezone.utc),
        "is_registered": False,
    }


@pytest.fixture
def user_api(monkeypatch, user_record):
    monkeypatch.setenv("POLL_SERVICE_URL", "http://poll-service.test")

    main = import_module("main")
    controllers = import_module("controllers")
    service = controllers.user_service

    repository = Mock(spec=import_module("repositories").UserRepository)
    poll_client = Mock(spec=import_module("clients").PollClient)

    monkeypatch.setattr(service, "repository", repository)
    monkeypatch.setattr(service, "poll_client", poll_client)

    repository.get_user.return_value = user_record.copy()
    repository.create_user.return_value = user_record.copy()
    repository.delete_user.return_value = True
    repository.update_user.return_value = {
        **user_record,
        "is_registered": True,
    }

    with TestClient(main.app) as client:
        yield client, repository, poll_client
