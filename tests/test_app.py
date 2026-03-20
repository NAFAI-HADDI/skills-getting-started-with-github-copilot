"""Comprehensive test suite for the Mergington High School Activities API.

Tests cover all endpoints and use the AAA (Arrange-Act-Assert) pattern.
"""

from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for the GET / endpoint."""

    def test_root_redirects_to_static_index(self, client: TestClient) -> None:
        """Test that the root endpoint redirects to the static index page.
        
        Arrange: Set up the test client
        Act: Make a GET request to /
        Assert: Verify redirect status and location
        """
        # Arrange
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_location


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client: TestClient) -> None:
        """Test that GET /activities returns all available activities.
        
        Arrange: Set up the test client
        Act: Make a GET request to /activities
        Assert: Verify response contains all expected activities
        """
        # Arrange
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Tennis Club",
            "Basketball Team",
            "Art Studio",
            "Drama Club",
            "Debate Team",
            "Science Club",
        ]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        for activity in expected_activities:
            assert activity in data

    def test_get_activities_returns_activity_structure(self, client: TestClient) -> None:
        """Test that each activity has the required fields.
        
        Arrange: Set up the test client
        Act: Make a GET request to /activities
        Assert: Verify each activity has description, schedule, max_participants, and participants
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys())
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success_for_existing_activity(self, client: TestClient) -> None:
        """Test successful signup for an existing activity.
        
        Arrange: Set up an email and activity name
        Act: POST a signup request
        Assert: Verify status 200 and success message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_verifies_participant_added(self, client: TestClient) -> None:
        """Test that a signed-up student appears in the activities list.
        
        Arrange: Set up an email and activity name
        Act: POST a signup and then GET activities
        Assert: Verify the participant is in the participants list
        """
        # Arrange
        activity_name = "Programming Class"
        email = "newprogrammer@mergington.edu"
        
        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        
        # Assert
        assert signup_response.status_code == 200
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_fails_for_nonexistent_activity(self, client: TestClient) -> None:
        """Test that signup fails for a non-existent activity with 404.
        
        Arrange: Set up a non-existent activity name
        Act: POST a signup request
        Assert: Verify status 404 and error detail
        """
        # Arrange
        nonexistent_activity = "Nonexistent Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_fails_for_duplicate_enrollment(self, client: TestClient) -> None:
        """Test that duplicate signup returns 400 error.
        
        Arrange: Set up an email that's already signed up for an activity
        Act: POST a signup request with an already enrolled student
        Assert: Verify status 400 and error detail
        """
        # Arrange
        activity_name = "Chess Club"
        already_enrolled_email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": already_enrolled_email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()


class TestCapacityValidation:
    """Tests for capacity validation (currently a bug - activities can over-enroll)."""

    def test_signup_fails_when_activity_is_full(self, client: TestClient) -> None:
        """Test that signup fails when activity reaches max capacity.
        
        This test will FAIL initially, revealing that the capacity validation
        is missing from the POST /activities/{activity_name}/signup endpoint.
        
        Arrange: Get the first activity and sign up enough students to fill it
        Act: Try to sign up beyond capacity
        Assert: Expect 400 error for capacity exceeded
        """
        # Arrange
        activities = client.get("/activities").json()
        # Find an activity with only 1 participant slot available
        activity_name = "Debate Team"
        activity = activities[activity_name]
        current_participants = activity["participants"]
        max_capacity = activity["max_participants"]
        available_slots = max_capacity - len(current_participants)
        
        # Sign up students to fill remaining slots
        for i in range(available_slots):
            email = f"student{i}@mergington.edu"
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Act: Try to signup when activity is full
        overfull_email = "overfull@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": overfull_email}
        )
        
        # Assert: Expect the request to fail (currently fails - missing validation!)
        # This test demonstrates the bug where activities can over-enroll
        assert response.status_code == 400, (
            "Activity should reject signup when at max capacity. "
            "This test revealed that capacity validation is missing!"
        )
        data = response.json()
        assert "capacity" in data["detail"].lower() or "full" in data["detail"].lower()


class TestDeleteEndpoint:
    """Tests for the DELETE /activities/{activity_name}/signup endpoint (if implemented)."""

    def test_delete_signup_removes_participant(self, client: TestClient) -> None:
        """Test that DELETE removes a participant from an activity.
        
        Arrange: Sign up a student and verify they're enrolled
        Act: DELETE the signup
        Assert: Verify participant is removed and participant count decreases
        """
        # Arrange
        activity_name = "Tennis Club"
        email = "tennis_dropout@mergington.edu"
        
        # First, sign up the student
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Verify they're signed up
        activities_before = client.get("/activities").json()
        initial_count = len(activities_before[activity_name]["participants"])
        assert email in activities_before[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"] or "unregistered" in data["message"].lower()
        
        # Verify participant was removed
        activities_after = client.get("/activities").json()
        final_count = len(activities_after[activity_name]["participants"])
        assert email not in activities_after[activity_name]["participants"]
        assert final_count == initial_count - 1

    def test_delete_fails_for_not_enrolled_student(self, client: TestClient) -> None:
        """Test that DELETE fails for a student not enrolled in the activity.
        
        Arrange: Set up an email not enrolled in the activity
        Act: DELETE the signup
        Assert: Verify status 400 and error detail
        """
        # Arrange
        activity_name = "Art Studio"
        not_enrolled_email = "nothere@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": not_enrolled_email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
