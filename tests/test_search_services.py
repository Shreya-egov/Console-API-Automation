import pytest
import uuid
import json
import os
import time
from utils.api_client import APIClient
from utils.data_loader import load_payload, apply_dynamic_dates
from utils.auth import get_auth_token
from utils.config import (
    tenantId, locale,
    SERVICE_PROJECT, SERVICE_PROJECT_FACILITY, SERVICE_PROJECT_STAFF, SERVICE_PROJECT_FACTORY
)


# --- Configuration ---
PROJECT_FACTORY_BASE = SERVICE_PROJECT_FACTORY
PROJECT_BASE = SERVICE_PROJECT
PROJECT_FACILITY_BASE = SERVICE_PROJECT_FACILITY
PROJECT_STAFF_BASE = SERVICE_PROJECT_STAFF


# --- Request Info Helper for Campaign Manager ---
def get_campaign_request_info(token: str) -> dict:
    """Get request info with Campaign Manager role."""
    return {
        "apiId": "Rainmaker",
        "authToken": token,
        "userInfo": {
            "id": 31582,
            "uuid": "4687260d-1b70-4262-b280-31a61534583e",
            "userName": "ACM11",
            "name": "ACM11",
            "mobileNumber": "9678012445",
            "emailId": "acm@gmail.com",
            "locale": None,
            "type": "EMPLOYEE",
            "roles": [
                {
                    "name": "Campaign Manager",
                    "code": "CAMPAIGN_MANAGER",
                    "tenantId": tenantId
                }
            ],
            "active": True,
            "tenantId": tenantId,
            "permanentCity": None
        },
        "msgId": f"{uuid.uuid4()}|en_MZ",
        "plainAccessRequest": {}
    }


# --- Helper Functions ---

def load_campaign_ids():
    """Load campaign IDs from the output file."""
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "outputs", "campaign_ids.json")
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            return json.load(f)
    return None


def search_campaign(token, client, campaign_number=None, campaign_id=None):
    """Search for a campaign by campaign number or ID."""
    payload = load_payload("campaign", "search_campaign.json")
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["tenantId"] = tenantId

    if campaign_number:
        payload["CampaignDetails"]["campaignNumber"] = campaign_number
    elif "campaignNumber" in payload["CampaignDetails"]:
        # Remove empty campaignNumber when searching by ID only
        del payload["CampaignDetails"]["campaignNumber"]

    if campaign_id:
        payload["CampaignDetails"]["ids"] = [campaign_id]

    url = f"{PROJECT_FACTORY_BASE}/search"
    response = client.post(url, payload)
    return response


def search_project(token, client, campaign_number):
    """Search for projects by campaign number (referenceID)."""
    payload = load_payload("campaign", "search_project.json")
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["Projects"][0]["referenceID"] = campaign_number
    payload["Projects"][0]["tenantId"] = tenantId
    payload["tenantId"] = tenantId

    url = f"{PROJECT_BASE}/_search?limit=100&offset=0&tenantId={tenantId}"
    response = client.post(url, payload)
    return response


def search_project_facility(token, client, project_ids):
    """Search for project facilities by project IDs."""
    payload = load_payload("campaign", "search_project_facility.json")
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["ProjectFacility"]["projectId"] = project_ids

    url = f"{PROJECT_FACILITY_BASE}/_search?tenantId={tenantId}&offset=0&limit=100"
    response = client.post(url, payload)
    return response


def search_project_staff(token, client, project_ids):
    """Search for project staff by project IDs."""
    payload = load_payload("campaign", "search_project_staff.json")
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["ProjectStaff"]["projectId"] = project_ids

    url = f"{PROJECT_STAFF_BASE}/_search?tenantId={tenantId}&offset=0&limit=100"
    response = client.post(url, payload)
    return response


# --- Retry/Polling Configuration ---
SEARCH_RETRY_MAX_ATTEMPTS = 30
SEARCH_RETRY_DELAY_SECONDS = 2


def wait_for_search(search_func, check_func, max_attempts=SEARCH_RETRY_MAX_ATTEMPTS, delay=SEARCH_RETRY_DELAY_SECONDS):
    """
    Generic polling function for search operations.

    Args:
        search_func: Function to call for search (returns response)
        check_func: Function to check if results are found (takes response, returns bool)
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        tuple: (response, found) where found is True if results were found
    """
    for attempt in range(1, max_attempts + 1):
        response = search_func()

        if response.status_code == 200 and check_func(response):
            print(f"Results found after {attempt} attempt(s)")
            return response, True

        if attempt < max_attempts:
            print(f"Results not found yet, retrying... (attempt {attempt}/{max_attempts})")
            time.sleep(delay)

    print(f"Results not found after {max_attempts} attempts")
    return response, False


# --- Test Cases for Campaign Search ---

class TestCampaignSearchService:
    """Test cases for campaign search API."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)
        self.campaign_data = load_campaign_ids()

    def test_search_campaign_by_number(self):
        """Test searching campaign by campaign number."""
        assert self.campaign_data is not None, "No campaign data found. Run campaign creation test first."

        campaign_number = self.campaign_data.get("campaignNumber")
        assert campaign_number, "Campaign number not found in saved data"

        print(f"\nSearching for campaign: {campaign_number}")

        # Use polling to wait for campaign to be searchable
        def do_search():
            return search_campaign(self.token, self.client, campaign_number=campaign_number)

        def check_found(resp):
            if resp.status_code != 200:
                return False
            data = resp.json()
            campaigns = data.get("CampaignDetails", [])
            if isinstance(campaigns, list):
                return any(c.get("campaignNumber") == campaign_number for c in campaigns)
            return campaigns.get("campaignNumber") == campaign_number

        response, found = wait_for_search(do_search, check_found)
        assert found, f"Campaign {campaign_number} not found after polling"
        assert response.status_code == 200, f"Campaign search failed: {response.text}"

        data = response.json()
        assert "CampaignDetails" in data, "Response missing CampaignDetails"

        campaigns = data.get("CampaignDetails", [])
        if isinstance(campaigns, list):
            assert len(campaigns) > 0, "No campaigns found"
            found = any(c.get("campaignNumber") == campaign_number for c in campaigns)
            assert found, f"Campaign {campaign_number} not found in results"
            print(f"Found {len(campaigns)} campaign(s)")
        else:
            assert campaigns.get("campaignNumber") == campaign_number
            print("Campaign found")

    def test_search_campaign_by_id(self):
        """Test searching campaign by campaign ID."""
        assert self.campaign_data is not None, "No campaign data found. Run campaign creation test first."

        campaign_id = self.campaign_data.get("campaignId")
        assert campaign_id, "Campaign ID not found in saved data"

        print(f"\nSearching for campaign by ID: {campaign_id}")

        # Use polling to wait for campaign to be searchable
        def do_search():
            return search_campaign(self.token, self.client, campaign_id=campaign_id)

        def check_found(resp):
            if resp.status_code != 200:
                return False
            data = resp.json()
            campaigns = data.get("CampaignDetails", [])
            if isinstance(campaigns, list):
                return any(c.get("id") == campaign_id for c in campaigns)
            return campaigns.get("id") == campaign_id

        response, found = wait_for_search(do_search, check_found)
        assert found, f"Campaign {campaign_id} not found after polling"
        assert response.status_code == 200, f"Campaign search failed: {response.text}"

        data = response.json()
        assert "CampaignDetails" in data, "Response missing CampaignDetails"
        print("Campaign found by ID")

    def test_search_campaign_invalid_number(self):
        """Test searching campaign with non-existent campaign number."""
        invalid_number = "INVALID-CAMPAIGN-NUMBER-12345"

        print(f"\nSearching for invalid campaign: {invalid_number}")
        response = search_campaign(self.token, self.client, campaign_number=invalid_number)

        assert response.status_code == 200, f"Search request failed: {response.text}"

        data = response.json()
        campaigns = data.get("CampaignDetails", [])

        # Should return empty results for non-existent campaign
        if isinstance(campaigns, list):
            assert len(campaigns) == 0, "Expected no campaigns for invalid number"
        print("Correctly returned empty results for invalid campaign number")

    def test_search_campaign_validates_response_structure(self):
        """Test that campaign search response has expected structure."""
        assert self.campaign_data is not None, "No campaign data found. Run campaign creation test first."

        campaign_number = self.campaign_data.get("campaignNumber")
        response = search_campaign(self.token, self.client, campaign_number=campaign_number)

        assert response.status_code == 200
        data = response.json()

        assert "CampaignDetails" in data
        campaigns = data.get("CampaignDetails", [])

        if isinstance(campaigns, list) and len(campaigns) > 0:
            campaign = campaigns[0]
            # Validate expected fields exist
            expected_fields = ["id", "campaignNumber", "campaignName", "tenantId", "status"]
            for field in expected_fields:
                assert field in campaign, f"Missing expected field: {field}"
            print(f"Response structure validated. Campaign status: {campaign.get('status')}")


# --- Test Cases for Project Search ---

class TestProjectSearchService:
    """Test cases for project search API."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)
        self.campaign_data = load_campaign_ids()

    def test_search_project_by_campaign_number(self):
        """Test searching projects by campaign number (referenceID)."""
        assert self.campaign_data is not None, "No campaign data found. Run campaign creation test first."

        campaign_number = self.campaign_data.get("campaignNumber")
        assert campaign_number, "Campaign number not found in saved data"

        print(f"\nSearching for projects with referenceID: {campaign_number}")
        response = search_project(self.token, self.client, campaign_number)

        assert response.status_code == 200, f"Project search failed: {response.text}"

        data = response.json()
        total_count = data.get("TotalCount", 0)
        projects = data.get("Project", [])

        print(f"TotalCount: {total_count}, Projects returned: {len(projects)}")

        # Verify response structure
        assert "TotalCount" in data, "Response missing TotalCount"
        assert "Project" in data, "Response missing Project array"

    def test_search_project_returns_correct_reference_id(self):
        """Test that returned projects have correct referenceID."""
        assert self.campaign_data is not None, "No campaign data found. Run campaign creation test first."

        campaign_number = self.campaign_data.get("campaignNumber")
        response = search_project(self.token, self.client, campaign_number)

        assert response.status_code == 200
        data = response.json()

        projects = data.get("Project", [])
        for project in projects:
            assert project.get("referenceID") == campaign_number, \
                f"Project referenceID mismatch: expected {campaign_number}, got {project.get('referenceID')}"

        print(f"All {len(projects)} projects have correct referenceID")

    def test_search_project_validates_response_structure(self):
        """Test that project search response has expected structure."""
        assert self.campaign_data is not None, "No campaign data found. Run campaign creation test first."

        campaign_number = self.campaign_data.get("campaignNumber")
        response = search_project(self.token, self.client, campaign_number)

        assert response.status_code == 200
        data = response.json()

        projects = data.get("Project", [])
        if len(projects) > 0:
            project = projects[0]
            # Validate expected fields exist
            expected_fields = ["id", "tenantId", "referenceID", "address"]
            for field in expected_fields:
                assert field in project, f"Missing expected field: {field}"

            # Validate address structure
            address = project.get("address", {})
            assert "boundaryType" in address, "Missing boundaryType in address"
            print(f"Response structure validated. First project boundaryType: {address.get('boundaryType')}")

    def test_search_project_invalid_reference_id(self):
        """Test searching projects with non-existent referenceID."""
        invalid_reference = "INVALID-REFERENCE-ID-12345"

        print(f"\nSearching for projects with invalid referenceID: {invalid_reference}")
        response = search_project(self.token, self.client, invalid_reference)

        assert response.status_code == 200, f"Search request failed: {response.text}"

        data = response.json()
        total_count = data.get("TotalCount", 0)

        assert total_count == 0, "Expected no projects for invalid referenceID"
        print("Correctly returned zero projects for invalid referenceID")

    def test_search_project_groups_by_boundary_type(self):
        """Test grouping projects by boundaryType."""
        assert self.campaign_data is not None, "No campaign data found. Run campaign creation test first."

        campaign_number = self.campaign_data.get("campaignNumber")
        response = search_project(self.token, self.client, campaign_number)

        assert response.status_code == 200
        data = response.json()

        projects = data.get("Project", [])

        # Group by boundaryType
        projects_by_boundary = {}
        for project in projects:
            boundary_type = project.get("address", {}).get("boundaryType", "UNKNOWN")
            if boundary_type not in projects_by_boundary:
                projects_by_boundary[boundary_type] = []
            projects_by_boundary[boundary_type].append(project.get("id"))

        print(f"Projects grouped by boundaryType:")
        for boundary_type, ids in projects_by_boundary.items():
            print(f"  {boundary_type}: {len(ids)} project(s)")

        # Store project IDs for facility and staff tests
        self.__class__.project_ids = [p.get("id") for p in projects]


# --- Test Cases for Project Facility Search ---

class TestProjectFacilitySearchService:
    """Test cases for project facility search API."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)
        self.campaign_data = load_campaign_ids()
        self.project_ids = self._get_project_ids()

    def _get_project_ids(self):
        """Get project IDs from campaign data or by searching."""
        if self.campaign_data:
            projects_by_boundary = self.campaign_data.get("projectsByBoundaryType", {})
            all_ids = []
            for ids in projects_by_boundary.values():
                all_ids.extend(ids)
            if all_ids:
                return all_ids

        # If no IDs in file, try to search for them
        if self.campaign_data and self.campaign_data.get("campaignNumber"):
            response = search_project(self.token, self.client, self.campaign_data["campaignNumber"])
            if response.status_code == 200:
                projects = response.json().get("Project", [])
                return [p.get("id") for p in projects]

        return []

    def test_search_project_facility_by_project_ids(self):
        """Test searching project facilities by project IDs."""
        assert len(self.project_ids) > 0, "No project IDs available. Run project search test first."

        print(f"\nSearching for facilities for {len(self.project_ids)} project(s)")
        response = search_project_facility(self.token, self.client, self.project_ids)

        assert response.status_code == 200, f"Facility search failed: {response.text}"

        data = response.json()
        facilities = data.get("ProjectFacilities", [])

        print(f"Found {len(facilities)} facility mapping(s)")

        # Verify response structure
        assert "ProjectFacilities" in data, "Response missing ProjectFacilities array"

    def test_search_project_facility_validates_response_structure(self):
        """Test that project facility search response has expected structure."""
        if len(self.project_ids) == 0:
            pytest.skip("No project IDs available for testing")

        response = search_project_facility(self.token, self.client, self.project_ids)

        assert response.status_code == 200
        data = response.json()

        facilities = data.get("ProjectFacilities", [])
        if len(facilities) > 0:
            facility = facilities[0]
            # Validate expected fields exist
            expected_fields = ["id", "projectId", "facilityId"]
            for field in expected_fields:
                assert field in facility, f"Missing expected field: {field}"
            print(f"Response structure validated. Found {len(facilities)} facility mapping(s)")

    def test_search_project_facility_single_project_id(self):
        """Test searching facilities for a single project ID."""
        if len(self.project_ids) == 0:
            pytest.skip("No project IDs available for testing")

        single_id = [self.project_ids[0]]
        print(f"\nSearching for facilities for project: {single_id[0]}")

        response = search_project_facility(self.token, self.client, single_id)

        assert response.status_code == 200, f"Facility search failed: {response.text}"

        data = response.json()
        facilities = data.get("ProjectFacilities", [])

        # Verify all returned facilities belong to the searched project
        for facility in facilities:
            assert facility.get("projectId") == single_id[0], \
                f"Facility projectId mismatch: expected {single_id[0]}, got {facility.get('projectId')}"

        print(f"Found {len(facilities)} facility(s) for project")

    def test_search_project_facility_invalid_project_id(self):
        """Test searching facilities with non-existent project ID."""
        invalid_ids = ["invalid-project-id-12345"]

        print(f"\nSearching for facilities with invalid project ID")
        response = search_project_facility(self.token, self.client, invalid_ids)

        assert response.status_code == 200, f"Search request failed: {response.text}"

        data = response.json()
        facilities = data.get("ProjectFacilities", [])

        assert len(facilities) == 0, "Expected no facilities for invalid project ID"
        print("Correctly returned empty results for invalid project ID")

    def test_search_project_facility_empty_project_ids(self):
        """Test searching facilities with empty project ID list."""
        empty_ids = []

        print("\nSearching for facilities with empty project ID list")
        response = search_project_facility(self.token, self.client, empty_ids)

        # Should return 200 with empty results or handle gracefully
        assert response.status_code == 200, f"Search request failed: {response.text}"
        print("Empty project ID list handled correctly")


# --- Test Cases for Project Staff Search ---

class TestProjectStaffSearchService:
    """Test cases for project staff search API."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)
        self.campaign_data = load_campaign_ids()
        self.project_ids = self._get_project_ids()

    def _get_project_ids(self):
        """Get project IDs from campaign data or by searching."""
        if self.campaign_data:
            projects_by_boundary = self.campaign_data.get("projectsByBoundaryType", {})
            all_ids = []
            for ids in projects_by_boundary.values():
                all_ids.extend(ids)
            if all_ids:
                return all_ids

        # If no IDs in file, try to search for them
        if self.campaign_data and self.campaign_data.get("campaignNumber"):
            response = search_project(self.token, self.client, self.campaign_data["campaignNumber"])
            if response.status_code == 200:
                projects = response.json().get("Project", [])
                return [p.get("id") for p in projects]

        return []

    def test_search_project_staff_by_project_ids(self):
        """Test searching project staff by project IDs."""
        assert len(self.project_ids) > 0, "No project IDs available. Run project search test first."

        print(f"\nSearching for staff for {len(self.project_ids)} project(s)")
        response = search_project_staff(self.token, self.client, self.project_ids)

        assert response.status_code == 200, f"Staff search failed: {response.text}"

        data = response.json()
        staff = data.get("ProjectStaff", [])

        print(f"Found {len(staff)} staff assignment(s)")

        # Verify response structure
        assert "ProjectStaff" in data, "Response missing ProjectStaff array"

    def test_search_project_staff_validates_response_structure(self):
        """Test that project staff search response has expected structure."""
        if len(self.project_ids) == 0:
            pytest.skip("No project IDs available for testing")

        response = search_project_staff(self.token, self.client, self.project_ids)

        assert response.status_code == 200
        data = response.json()

        staff_list = data.get("ProjectStaff", [])
        if len(staff_list) > 0:
            staff = staff_list[0]
            # Validate expected fields exist
            expected_fields = ["id", "projectId", "userId"]
            for field in expected_fields:
                assert field in staff, f"Missing expected field: {field}"
            print(f"Response structure validated. Found {len(staff_list)} staff assignment(s)")

    def test_search_project_staff_single_project_id(self):
        """Test searching staff for a single project ID."""
        if len(self.project_ids) == 0:
            pytest.skip("No project IDs available for testing")

        single_id = [self.project_ids[0]]
        print(f"\nSearching for staff for project: {single_id[0]}")

        response = search_project_staff(self.token, self.client, single_id)

        assert response.status_code == 200, f"Staff search failed: {response.text}"

        data = response.json()
        staff_list = data.get("ProjectStaff", [])

        # Verify all returned staff belong to the searched project
        for staff in staff_list:
            assert staff.get("projectId") == single_id[0], \
                f"Staff projectId mismatch: expected {single_id[0]}, got {staff.get('projectId')}"

        print(f"Found {len(staff_list)} staff member(s) for project")

    def test_search_project_staff_invalid_project_id(self):
        """Test searching staff with non-existent project ID."""
        invalid_ids = ["invalid-project-id-12345"]

        print(f"\nSearching for staff with invalid project ID")
        response = search_project_staff(self.token, self.client, invalid_ids)

        assert response.status_code == 200, f"Search request failed: {response.text}"

        data = response.json()
        staff_list = data.get("ProjectStaff", [])

        assert len(staff_list) == 0, "Expected no staff for invalid project ID"
        print("Correctly returned empty results for invalid project ID")

    def test_search_project_staff_empty_project_ids(self):
        """Test searching staff with empty project ID list."""
        empty_ids = []

        print("\nSearching for staff with empty project ID list")
        response = search_project_staff(self.token, self.client, empty_ids)

        # Should return 200 with empty results or handle gracefully
        assert response.status_code == 200, f"Search request failed: {response.text}"
        print("Empty project ID list handled correctly")


# --- Combined Search Flow Test ---

class TestSearchServicesE2E:
    """End-to-end tests for all search services."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)
        self.campaign_data = load_campaign_ids()

    def test_complete_search_flow(self):
        """
        Test complete search flow:
        1. Search campaign
        2. Search projects by campaign
        3. Search facilities by projects
        4. Search staff by projects
        """
        assert self.campaign_data is not None, "No campaign data found. Run campaign creation test first."

        campaign_number = self.campaign_data.get("campaignNumber")
        campaign_id = self.campaign_data.get("campaignId")

        # Step 1: Search Campaign
        print(f"\n=== Step 1: Searching Campaign ===")
        campaign_response = search_campaign(self.token, self.client, campaign_number=campaign_number)
        assert campaign_response.status_code == 200, f"Campaign search failed: {campaign_response.text}"

        campaign_data = campaign_response.json()
        campaigns = campaign_data.get("CampaignDetails", [])
        if isinstance(campaigns, list):
            print(f"Found {len(campaigns)} campaign(s)")
        else:
            print("Found 1 campaign")

        # Step 2: Search Projects
        print(f"\n=== Step 2: Searching Projects ===")
        project_response = search_project(self.token, self.client, campaign_number)
        assert project_response.status_code == 200, f"Project search failed: {project_response.text}"

        project_data = project_response.json()
        projects = project_data.get("Project", [])
        total_count = project_data.get("TotalCount", 0)
        print(f"Found {total_count} project(s)")

        if len(projects) == 0:
            print("No projects found. Skipping facility and staff search.")
            return

        project_ids = [p.get("id") for p in projects]

        # Group by boundary type
        projects_by_boundary = {}
        for project in projects:
            boundary_type = project.get("address", {}).get("boundaryType", "UNKNOWN")
            if boundary_type not in projects_by_boundary:
                projects_by_boundary[boundary_type] = []
            projects_by_boundary[boundary_type].append(project.get("id"))

        for boundary_type, ids in projects_by_boundary.items():
            print(f"  {boundary_type}: {len(ids)} project(s)")

        # Step 3: Search Facilities
        print(f"\n=== Step 3: Searching Project Facilities ===")
        facility_response = search_project_facility(self.token, self.client, project_ids)
        assert facility_response.status_code == 200, f"Facility search failed: {facility_response.text}"

        facility_data = facility_response.json()
        facilities = facility_data.get("ProjectFacilities", [])
        print(f"Found {len(facilities)} facility mapping(s)")

        # Step 4: Search Staff
        print(f"\n=== Step 4: Searching Project Staff ===")
        staff_response = search_project_staff(self.token, self.client, project_ids)
        assert staff_response.status_code == 200, f"Staff search failed: {staff_response.text}"

        staff_data = staff_response.json()
        staff = staff_data.get("ProjectStaff", [])
        print(f"Found {len(staff)} staff assignment(s)")

        print(f"\n=== Search Flow Completed Successfully ===")
        print(f"Summary:")
        print(f"  Campaign: {campaign_number}")
        print(f"  Projects: {total_count}")
        print(f"  Facilities: {len(facilities)}")
        print(f"  Staff: {len(staff)}")
