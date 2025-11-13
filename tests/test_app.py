"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the activities endpoint"""

    def test_get_all_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Verify structure of an activity
        first_activity = list(activities.values())[0]
        assert "description" in first_activity
        assert "schedule" in first_activity
        assert "max_participants" in first_activity
        assert "participants" in first_activity

    def test_activities_have_required_fields(self):
        """Test that all activities have required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for name, details in activities.items():
            assert isinstance(name, str)
            assert isinstance(details["description"], str)
            assert isinstance(details["schedule"], str)
            assert isinstance(details["max_participants"], int)
            assert isinstance(details["participants"], list)


class TestSignupEndpoint:
    """Tests for the signup endpoint"""

    def test_signup_for_activity(self):
        """Test signing up for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_already_registered(self):
        """Test signing up when already registered"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Programming%20Class/signup?email=" + email
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Programming%20Class/signup?email=" + email
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds participant to activity"""
        email = "newstudent@mergington.edu"
        
        # Get initial participant count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Art Studio"]["participants"])
        
        # Sign up
        signup_response = client.post(
            "/activities/Art%20Studio/signup?email=" + email
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        response2 = client.get("/activities")
        new_count = len(response2.json()["Art Studio"]["participants"])
        assert new_count == initial_count + 1
        assert email in response2.json()["Art Studio"]["participants"]


class TestUnregisterEndpoint:
    """Tests for the unregister endpoint"""

    def test_unregister_from_activity(self):
        """Test unregistering from an activity"""
        email = "unreg@mergington.edu"
        
        # First signup
        client.post("/activities/Tennis%20Club/signup?email=" + email)
        
        # Then unregister
        response = client.post(
            "/activities/Tennis%20Club/unregister?email=" + email
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_activity_not_found(self):
        """Test unregister for non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_registered(self):
        """Test unregistering when not registered"""
        response = client.post(
            "/activities/Drama%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes participant from activity"""
        email = "removeme@mergington.edu"
        
        # Sign up
        client.post("/activities/Debate%20Team/signup?email=" + email)
        
        # Get participant count before unregister
        response1 = client.get("/activities")
        count_before = len(response1.json()["Debate Team"]["participants"])
        
        # Unregister
        unregister_response = client.post(
            "/activities/Debate%20Team/unregister?email=" + email
        )
        assert unregister_response.status_code == 200
        
        # Verify participant was removed
        response2 = client.get("/activities")
        count_after = len(response2.json()["Debate Team"]["participants"])
        assert count_after == count_before - 1
        assert email not in response2.json()["Debate Team"]["participants"]

    def test_unregister_same_participant_twice(self):
        """Test that unregistering the same participant twice fails"""
        email = "twice@mergington.edu"
        
        # Sign up
        client.post("/activities/Science%20Club/signup?email=" + email)
        
        # First unregister should succeed
        response1 = client.post(
            "/activities/Science%20Club/unregister?email=" + email
        )
        assert response1.status_code == 200
        
        # Second unregister should fail
        response2 = client.post(
            "/activities/Science%20Club/unregister?email=" + email
        )
        assert response2.status_code == 400
        assert "not registered" in response2.json()["detail"]
