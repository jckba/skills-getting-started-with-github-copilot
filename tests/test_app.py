import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def test_activities(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Test activity",
            "schedule": "Mondays",
            "max_participants": 2,
            "participants": ["first@example.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(test_activities):
    return TestClient(app_module.app)


def test_get_activities_returns_activities(client, test_activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == test_activities


def test_signup_adds_participant(client, test_activities):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "second@example.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up second@example.edu for Chess Club"
    }
    assert test_activities["Chess Club"]["participants"] == [
        "first@example.edu",
        "second@example.edu",
    ]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "first@example.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_full_activity_without_changing_participants(
    client, test_activities
):
    participants = test_activities["Chess Club"]["participants"]
    participants.append("second@example.edu")
    original_participants = participants.copy()

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "third@example.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert participants == original_participants


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "student@example.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client, test_activities):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "first@example.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered first@example.edu from Chess Club"
    }
    assert test_activities["Chess Club"]["participants"] == []


def test_unregister_returns_404_for_unregistered_participant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "missing@example.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/signup",
        params={"email": "student@example.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_frees_a_spot_for_another_signup(client, test_activities):
    client.post(
        "/activities/Chess Club/signup",
        params={"email": "second@example.edu"},
    )

    unregister_response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "first@example.edu"},
    )
    signup_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "third@example.edu"},
    )

    assert unregister_response.status_code == 200
    assert signup_response.status_code == 200
    assert test_activities["Chess Club"]["participants"] == [
        "second@example.edu",
        "third@example.edu",
    ]