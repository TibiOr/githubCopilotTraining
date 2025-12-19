import copy
import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def isolate_activities():
    # Snapshot and restore the in-memory activities so tests don't leak state
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect at least one known activity
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    email = "test.user@example.com"
    activity = "Chess Club"

    # Ensure email not already present
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email not in resp.json()[activity]["participants"]

    # Sign up (POST)
    post_resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert post_resp.status_code == 200
    post_json = post_resp.json()
    assert "Signed up" in post_json.get("message", "")

    # Verify participant now listed
    after = client.get("/activities").json()
    assert email in after[activity]["participants"]

    # Unregister (DELETE)
    del_resp = client.delete(f"/activities/{activity}/signup?email={email}")
    assert del_resp.status_code == 200
    del_json = del_resp.json()
    assert "Unregistered" in del_json.get("message", "")

    # Verify removal
    final = client.get("/activities").json()
    assert email not in final[activity]["participants"]