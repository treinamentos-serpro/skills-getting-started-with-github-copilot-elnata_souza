from copy import deepcopy

import pytest


def test_root_redirects_to_static_page(client):
    path = "/"

    response = client.get(path, follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client, activity_data):
    expected_activities = deepcopy(activity_data)
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == expected_activities
    assert "Chess Club" in response.json()
    for details in response.json().values():
        assert expected_fields <= details.keys()
        assert isinstance(details["participants"], list)


def test_signup_adds_participant(client, activity_data):
    email = "New.Student@mergington.edu"
    expected_activities = deepcopy(activity_data)
    expected_activities["Chess Club"]["participants"].append(email)

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert activity_data == expected_activities
    assert activity_data["Chess Club"]["participants"].count(email) == 1


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_signup_endpoint_rejects_unknown_activity(client, activity_data, method):
    original_activities = deepcopy(activity_data)
    email = "student@mergington.edu"

    response = client.request(
        method, "/activities/Unknown Club/signup", params={"email": email}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_data == original_activities


@pytest.mark.parametrize(
    "email", ["michael@mergington.edu", "MICHAEL@MERGINGTON.EDU"]
)
def test_signup_rejects_duplicate_email(client, activity_data, email):
    original_activities = deepcopy(activity_data)

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activity_data == original_activities


@pytest.mark.parametrize(
    "email", ["michael@mergington.edu", "MICHAEL@MERGINGTON.EDU"]
)
def test_cancel_signup_removes_participant(client, activity_data, email):
    expected_activities = deepcopy(activity_data)
    expected_activities["Chess Club"]["participants"].remove("michael@mergington.edu")

    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Cancelled signup for {email} in Chess Club"
    }
    assert activity_data == expected_activities


def test_cancel_signup_rejects_unenrolled_participant(client, activity_data):
    original_activities = deepcopy(activity_data)
    email = "unenrolled@mergington.edu"

    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert activity_data == original_activities


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_signup_endpoint_requires_email(client, activity_data, method):
    original_activities = deepcopy(activity_data)

    response = client.request(method, "/activities/Chess Club/signup")

    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"]
        for error in response.json()["detail"]
    )
    assert activity_data == original_activities