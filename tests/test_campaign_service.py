import pytest
import uuid
import json
import os
from utils.api_client import APIClient
from utils.data_loader import load_payload, apply_dynamic_dates
from utils.auth import get_auth_token
from utils.request_info import get_request_info
from utils.config import tenantId, locale


def save_campaign_output(campaign_id, campaign_number, campaign_name):
    """Save campaign details to output file."""
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "outputs")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "campaign_ids.json")
    with open(output_path, "w") as f:
        json.dump({
            "campaignId": campaign_id,
            "campaignNumber": campaign_number,
            "campaignName": campaign_name
        }, f, indent=2)


# --- Configuration ---
PROJECT_FACTORY_BASE = "/project-factory/v1/project-type"


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


# --- Reusable Functions ---

def create_campaign_setup(token, client, campaign_name=None):
    """
    Create a new campaign setup (draft).
    Returns the campaign details from response.
    """
    payload = load_payload("campaign", "create_setup.json")
    payload = apply_dynamic_dates(payload)
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["locale"] = locale

    if campaign_name:
        payload["CampaignDetails"]["campaignName"] = campaign_name
    else:
        payload["CampaignDetails"]["campaignName"] = f"Test_Campaign_{uuid.uuid4().hex[:8]}"

    url = f"{PROJECT_FACTORY_BASE}/create"
    response = client.post(url, payload)
    return response


def update_campaign_boundary(token, client, campaign_id, campaign_number, campaign_name, hierarchy_type):
    """
    Update campaign with boundary information.
    """
    payload = load_payload("campaign", "update_boundary.json")
    payload = apply_dynamic_dates(payload)
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["id"] = campaign_id
    payload["CampaignDetails"]["campaignNumber"] = campaign_number
    payload["CampaignDetails"]["campaignName"] = campaign_name
    payload["CampaignDetails"]["hierarchyType"] = hierarchy_type
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["locale"] = locale

    url = f"{PROJECT_FACTORY_BASE}/update"
    response = client.post(url, payload)
    return response


def update_campaign_delivery(token, client, campaign_id, campaign_number, campaign_name, hierarchy_type):
    """
    Update campaign with delivery rules.
    """
    payload = load_payload("campaign", "update_delivery.json")
    payload = apply_dynamic_dates(payload)
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["id"] = campaign_id
    payload["CampaignDetails"]["campaignNumber"] = campaign_number
    payload["CampaignDetails"]["campaignName"] = campaign_name
    payload["CampaignDetails"]["hierarchyType"] = hierarchy_type
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["locale"] = locale

    url = f"{PROJECT_FACTORY_BASE}/update"
    response = client.post(url, payload)
    return response


def update_campaign_files(token, client, campaign_id, campaign_number, campaign_name, hierarchy_type):
    """
    Update campaign with resource files (user, facility, boundary).
    """
    payload = load_payload("campaign", "update_files.json")
    payload = apply_dynamic_dates(payload)
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["id"] = campaign_id
    payload["CampaignDetails"]["campaignNumber"] = campaign_number
    payload["CampaignDetails"]["campaignName"] = campaign_name
    payload["CampaignDetails"]["hierarchyType"] = hierarchy_type
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["locale"] = locale

    url = f"{PROJECT_FACTORY_BASE}/update"
    response = client.post(url, payload)
    return response


def create_campaign(token, client, campaign_id, campaign_number, campaign_name):
    """
    Finalize and create the campaign (change action to 'create').
    """
    payload = load_payload("campaign", "create_campaign.json")
    payload = apply_dynamic_dates(payload)
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["id"] = campaign_id
    payload["CampaignDetails"]["campaignNumber"] = campaign_number
    payload["CampaignDetails"]["campaignName"] = campaign_name
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["locale"] = locale

    url = f"{PROJECT_FACTORY_BASE}/update"
    response = client.post(url, payload)
    return response


def search_campaign(token, client, campaign_number=None, campaign_id=None):
    """
    Search for a campaign by campaign number or ID.
    """
    payload = load_payload("campaign", "search_campaign.json")
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["tenantId"] = tenantId

    if campaign_number:
        payload["CampaignDetails"]["campaignNumber"] = campaign_number
    if campaign_id:
        payload["CampaignDetails"]["ids"] = [campaign_id]

    url = f"{PROJECT_FACTORY_BASE}/search"
    response = client.post(url, payload)
    return response


# --- Test Cases ---

class TestCampaignSetup:
    """Test cases for campaign setup creation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)

    def test_create_campaign_setup_success(self):
        """Test successful creation of campaign setup."""
        campaign_name = f"Test_Campaign_{uuid.uuid4().hex[:8]}"
        response = create_campaign_setup(self.token, self.client, campaign_name)

        assert response.status_code == 200, f"Failed to create campaign setup: {response.text}"

        data = response.json()
        assert "CampaignDetails" in data
        assert data["CampaignDetails"]["campaignName"] == campaign_name
        assert data["CampaignDetails"]["status"] == "drafted"
        assert "id" in data["CampaignDetails"]
        assert "campaignNumber" in data["CampaignDetails"]

    def test_create_campaign_setup_with_default_name(self):
        """Test campaign setup creation with auto-generated name."""
        response = create_campaign_setup(self.token, self.client)

        assert response.status_code == 200, f"Failed to create campaign setup: {response.text}"

        data = response.json()
        assert "CampaignDetails" in data
        assert data["CampaignDetails"]["campaignName"].startswith("Test_Campaign_")


class TestCampaignBoundary:
    """Test cases for campaign boundary updates."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)

    def test_update_campaign_boundary_success(self):
        """Test successful update of campaign boundary."""
        # First create a campaign setup
        setup_response = create_campaign_setup(self.token, self.client)
        assert setup_response.status_code == 200, f"Failed to create campaign setup: {setup_response.text}"

        setup_data = setup_response.json()
        campaign_id = setup_data["CampaignDetails"]["id"]
        campaign_number = setup_data["CampaignDetails"]["campaignNumber"]
        campaign_name = setup_data["CampaignDetails"]["campaignName"]
        hierarchy_type = setup_data["CampaignDetails"]["hierarchyType"]

        # Update with boundary
        response = update_campaign_boundary(
            self.token, self.client,
            campaign_id, campaign_number, campaign_name, hierarchy_type
        )

        assert response.status_code == 200, f"Failed to update campaign boundary: {response.text}"

        data = response.json()
        assert "CampaignDetails" in data
        assert data["CampaignDetails"]["boundaryCode"] == "MICROPLAN_MO"
        assert len(data["CampaignDetails"]["boundaries"]) > 0


class TestCampaignDelivery:
    """Test cases for campaign delivery updates."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)

    def test_update_campaign_delivery_success(self):
        """Test successful update of campaign delivery rules."""
        # First create a campaign setup
        setup_response = create_campaign_setup(self.token, self.client)
        assert setup_response.status_code == 200, f"Failed to create campaign setup: {setup_response.text}"

        setup_data = setup_response.json()
        campaign_id = setup_data["CampaignDetails"]["id"]
        campaign_number = setup_data["CampaignDetails"]["campaignNumber"]
        campaign_name = setup_data["CampaignDetails"]["campaignName"]
        hierarchy_type = setup_data["CampaignDetails"]["hierarchyType"]

        # Update with boundary first
        boundary_response = update_campaign_boundary(
            self.token, self.client,
            campaign_id, campaign_number, campaign_name, hierarchy_type
        )
        assert boundary_response.status_code == 200

        # Update with delivery rules
        response = update_campaign_delivery(
            self.token, self.client,
            campaign_id, campaign_number, campaign_name, hierarchy_type
        )

        assert response.status_code == 200, f"Failed to update campaign delivery: {response.text}"

        data = response.json()
        assert "CampaignDetails" in data
        assert "deliveryRules" in data["CampaignDetails"]
        assert len(data["CampaignDetails"]["deliveryRules"]) > 0


class TestCampaignCreate:
    """Test cases for finalizing campaign creation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)

    def test_create_campaign_full_flow(self):
        """Test full campaign creation flow."""
        # Step 1: Create campaign setup
        setup_response = create_campaign_setup(self.token, self.client)
        assert setup_response.status_code == 200, f"Failed to create campaign setup: {setup_response.text}"

        setup_data = setup_response.json()
        campaign_id = setup_data["CampaignDetails"]["id"]
        campaign_number = setup_data["CampaignDetails"]["campaignNumber"]
        campaign_name = setup_data["CampaignDetails"]["campaignName"]
        hierarchy_type = setup_data["CampaignDetails"]["hierarchyType"]

        # Step 2: Update boundary
        boundary_response = update_campaign_boundary(
            self.token, self.client,
            campaign_id, campaign_number, campaign_name, hierarchy_type
        )
        assert boundary_response.status_code == 200, f"Failed to update boundary: {boundary_response.text}"

        # Step 3: Update delivery
        delivery_response = update_campaign_delivery(
            self.token, self.client,
            campaign_id, campaign_number, campaign_name, hierarchy_type
        )
        assert delivery_response.status_code == 200, f"Failed to update delivery: {delivery_response.text}"

        # Step 4: Update files (resources)
        files_response = update_campaign_files(
            self.token, self.client,
            campaign_id, campaign_number, campaign_name, hierarchy_type
        )
        assert files_response.status_code == 200, f"Failed to update files: {files_response.text}"

        # Step 5: Create (finalize) campaign
        create_response = create_campaign(
            self.token, self.client,
            campaign_id, campaign_number, campaign_name
        )
        assert create_response.status_code == 200, f"Failed to create campaign: {create_response.text}"


class TestCampaignSearch:
    """Test cases for campaign search."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)

    def test_search_campaign_by_number(self):
        """Test searching campaign by campaign number."""
        # First create a campaign
        setup_response = create_campaign_setup(self.token, self.client)
        assert setup_response.status_code == 200

        campaign_number = setup_response.json()["CampaignDetails"]["campaignNumber"]

        # Search for the campaign
        response = search_campaign(self.token, self.client, campaign_number=campaign_number)

        assert response.status_code == 200, f"Failed to search campaign: {response.text}"

        data = response.json()
        assert "CampaignDetails" in data
        # The response should contain the campaign we just created
        campaigns = data.get("CampaignDetails", [])
        if isinstance(campaigns, list):
            assert len(campaigns) > 0
            assert any(c.get("campaignNumber") == campaign_number for c in campaigns)
        else:
            assert campaigns.get("campaignNumber") == campaign_number

    def test_search_campaign_invalid_number(self):
        """Test searching campaign with non-existent campaign number."""
        response = search_campaign(self.token, self.client, campaign_number="INVALID-CAMPAIGN-NUMBER")

        # Should return 200 with empty results or appropriate message
        assert response.status_code == 200


# --- End-to-End Test ---

class TestCampaignE2E:
    """End-to-end test for complete campaign creation workflow."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)

    def test_complete_campaign_workflow(self):
        """
        Test complete campaign creation workflow:
        1. Create setup
        2. Update boundary
        3. Update delivery
        4. Create campaign
        5. Search and verify
        """
        campaign_name = f"E2E_Test_Campaign_{uuid.uuid4().hex[:8]}"

        # Step 1: Create campaign setup
        print(f"\n--- Step 1: Creating campaign setup: {campaign_name} ---")
        setup_response = create_campaign_setup(self.token, self.client, campaign_name)
        assert setup_response.status_code == 200, f"Setup failed: {setup_response.text}"

        setup_data = setup_response.json()
        campaign_id = setup_data["CampaignDetails"]["id"]
        campaign_number = setup_data["CampaignDetails"]["campaignNumber"]
        hierarchy_type = setup_data["CampaignDetails"]["hierarchyType"]

        print(f"Campaign ID: {campaign_id}")
        print(f"Campaign Number: {campaign_number}")

        # Save campaign output to file
        save_campaign_output(campaign_id, campaign_number, campaign_name)
        print(f"Campaign details saved to data/outputs/campaign_ids.json")

        # Step 2: Update boundary
        print("\n--- Step 2: Updating campaign boundary ---")
        boundary_response = update_campaign_boundary(
            self.token, self.client,
            campaign_id, campaign_number, campaign_name, hierarchy_type
        )
        assert boundary_response.status_code == 200, f"Boundary update failed: {boundary_response.text}"
        print("Boundary updated successfully")

        # Step 3: Update delivery
        print("\n--- Step 3: Updating campaign delivery ---")
        delivery_response = update_campaign_delivery(
            self.token, self.client,
            campaign_id, campaign_number, campaign_name, hierarchy_type
        )
        assert delivery_response.status_code == 200, f"Delivery update failed: {delivery_response.text}"
        print("Delivery rules updated successfully")

        # Step 4: Update files (resources)
        print("\n--- Step 4: Updating campaign files ---")
        files_response = update_campaign_files(
            self.token, self.client,
            campaign_id, campaign_number, campaign_name, hierarchy_type
        )
        assert files_response.status_code == 200, f"Files update failed: {files_response.text}"
        print("Resource files updated successfully")

        # Step 5: Create (finalize) campaign
        print("\n--- Step 5: Finalizing campaign creation ---")
        create_response = create_campaign(
            self.token, self.client,
            campaign_id, campaign_number, campaign_name
        )
        assert create_response.status_code == 200, f"Campaign creation failed: {create_response.text}"
        print("Campaign created successfully")

        # Step 6: Search and verify
        print("\n--- Step 6: Searching and verifying campaign ---")
        search_response = search_campaign(self.token, self.client, campaign_number=campaign_number)
        assert search_response.status_code == 200, f"Search failed: {search_response.text}"

        search_data = search_response.json()
        print(f"Campaign found: {campaign_number}")

        print("\n=== Campaign E2E Test Completed Successfully ===")
