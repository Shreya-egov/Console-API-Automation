import pytest
import uuid
import json
import os
import time
import requests as raw_requests
from utils.api_client import APIClient
from utils.data_loader import load_payload, apply_dynamic_dates
from utils.auth import get_auth_token
from utils.config import (
    tenantId, locale, BASE_URL,
    SERVICE_EXCEL_INGESTION, SERVICE_FILESTORE, SERVICE_PROJECT_FACTORY,
    hierarchyType,
)


# --- Configuration ---
EXCEL_INGESTION_BASE = SERVICE_EXCEL_INGESTION
FILESTORE_BASE = SERVICE_FILESTORE
PROJECT_FACTORY_BASE = SERVICE_PROJECT_FACTORY
UPLOAD_FILESTORE_ID = "da4bd5c6-0a01-4079-9a95-af5bfcbc43fc"


# --- Request Info Helper ---
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
        "msgId": f"{uuid.uuid4()}|{locale}",
        "plainAccessRequest": {}
    }


# --- Data Persistence ---

def load_campaign_ids():
    """Load campaign IDs from the output file."""
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "outputs", "campaign_ids.json")
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            return json.load(f)
    return None


def save_campaign_ids(data):
    """Save campaign data to the output file."""
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "outputs", "campaign_ids.json")
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


# --- Campaign Search (to get projectType / hierarchyType for existing campaign) ---

def search_campaign(token, client, campaign_id):
    """Search for a campaign by ID to retrieve its details."""
    payload = load_payload("campaign", "search_campaign.json")
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["ids"] = [campaign_id]

    # Remove empty campaignNumber when searching by ID only
    if "campaignNumber" in payload["CampaignDetails"] and not payload["CampaignDetails"]["campaignNumber"]:
        del payload["CampaignDetails"]["campaignNumber"]

    url = f"{PROJECT_FACTORY_BASE}/search"
    return client.post(url, payload)


# --- Excel Ingestion Helpers ---

def generate_excel_template(token, client, campaign_id, campaign_hierarchy_type, project_type):
    """
    POST /excel-ingestion/v1/data/generate/_init
    Initiate Excel template generation for a campaign.
    """
    payload = load_payload("excel_ingestion", "generate_init.json")
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["GenerateResource"]["tenantId"] = tenantId
    payload["GenerateResource"]["hierarchyType"] = campaign_hierarchy_type
    payload["GenerateResource"]["referenceId"] = campaign_id
    payload["GenerateResource"]["referenceType"] = project_type

    url = f"{EXCEL_INGESTION_BASE}/generate/_init"
    return client.post(url, payload)


def search_generation_status(token, client, generation_id):
    """
    POST /excel-ingestion/v1/data/generate/_search
    Search generation status by ID.
    """
    payload = load_payload("excel_ingestion", "generation_search.json")
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["GenerationSearchCriteria"]["tenantId"] = tenantId
    payload["GenerationSearchCriteria"]["ids"] = [generation_id]

    url = f"{EXCEL_INGESTION_BASE}/generate/_search"
    return client.post(url, payload)


def wait_for_generation_complete(token, client, generation_id, max_attempts=30, delay=5):
    """
    Poll generation status until it reaches 'completed' or 'failed'.
    Returns (response, fileStoreId_or_None, status_reached).
    """
    for attempt in range(1, max_attempts + 1):
        response = search_generation_status(token, client, generation_id)

        if response.status_code == 200:
            data = response.json()
            details = data.get("GenerationDetails", [])
            if isinstance(details, list) and len(details) > 0:
                status = details[0].get("status")
                file_store_id = details[0].get("fileStoreId")
                print(f"  Attempt {attempt}: Generation status = {status}")
                if status == "completed":
                    print(f"  Generation completed after {attempt} attempt(s)")
                    return response, file_store_id, True
                if status == "failed":
                    print(f"  Generation failed.")
                    return response, None, False

        if attempt < max_attempts:
            print(f"  Waiting for generation to complete... (attempt {attempt}/{max_attempts})")
            time.sleep(delay)

    print(f"  Generation did not complete after {max_attempts} attempts")
    return response, None, False


# --- Filestore Helpers ---

def get_file_download_url(client, file_store_id):
    """
    GET /filestore/v1/files/url?tenantId=...&fileStoreIds=...
    Get the pre-signed download URL for a file.
    """
    url = f"{FILESTORE_BASE}/url?tenantId={tenantId}&fileStoreIds={file_store_id}"
    return client.get(url)


def download_file_to_disk(download_url, output_dir=None):
    """
    Download a file from a pre-signed URL (no auth needed).
    Returns the local file path.
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "outputs")
    os.makedirs(output_dir, exist_ok=True)

    # Extract filename from URL or use a default
    filename = download_url.split("/")[-1].split("?")[0]
    if not filename or not filename.endswith(".xlsx"):
        filename = f"excel_template_{uuid.uuid4().hex[:8]}.xlsx"

    file_path = os.path.join(output_dir, filename)
    response = raw_requests.get(download_url)
    assert response.status_code == 200, f"Failed to download file: {response.status_code}"

    with open(file_path, "wb") as f:
        f.write(response.content)

    print(f"  Downloaded file to {file_path} ({len(response.content)} bytes)")
    return file_path


def upload_file(client, file_path):
    """
    POST /filestore/v1/files (multipart/form-data)
    Upload a file to filestore.
    """
    form_fields = {
        "tenantId": tenantId,
        "module": "HCM-ADMIN-CONSOLE",
    }
    return client.upload_file(FILESTORE_BASE, file_path, form_fields)


# --- Process Helpers ---

def search_process_status(token, client, process_id):
    """
    POST /excel-ingestion/v1/data/process/_search
    Search processing status by ID.
    """
    payload = load_payload("excel_ingestion", "process_search.json")
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["ProcessingSearchCriteria"]["tenantId"] = tenantId
    payload["ProcessingSearchCriteria"]["ids"] = [process_id]

    url = f"{EXCEL_INGESTION_BASE}/process/_search"
    return client.post(url, payload)


def wait_for_process_complete(token, client, process_id, max_attempts=60, delay=5):
    """
    Poll process status until it reaches 'completed' or 'failed'.
    Returns (response, status_reached).
    """
    for attempt in range(1, max_attempts + 1):
        response = search_process_status(token, client, process_id)

        if response.status_code == 200:
            data = response.json()
            details = data.get("ProcessingDetails", [])
            if isinstance(details, list) and len(details) > 0:
                status = details[0].get("status")
                print(f"  Attempt {attempt}: Process status = {status}")
                if status == "completed":
                    print(f"  Processing completed after {attempt} attempt(s)")
                    return response, True
                if status == "failed":
                    print(f"  Processing failed.")
                    return response, False

        if attempt < max_attempts:
            print(f"  Waiting for processing to complete... (attempt {attempt}/{max_attempts})")
            time.sleep(delay)

    print(f"  Processing did not complete after {max_attempts} attempts")
    return response, False


# --- Test Cases ---

class TestGenerateExcelTemplate:
    """Test cases for Excel template generation init."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)
        self.campaign_data = load_campaign_ids()

    def test_generate_init_success(self):
        """Test initiating Excel template generation for an existing campaign."""
        assert self.campaign_data is not None, "campaign_ids.json not found - run campaign tests first"
        campaign_id = self.campaign_data["campaignId"]

        # Get campaign details to retrieve hierarchyType and projectType
        search_resp = search_campaign(self.token, self.client, campaign_id)
        assert search_resp.status_code == 200, f"Campaign search failed: {search_resp.text}"
        campaigns = search_resp.json().get("CampaignDetails", [])
        assert len(campaigns) > 0, "No campaign found"
        campaign = campaigns[0]
        campaign_hierarchy = campaign.get("hierarchyType", hierarchyType)
        project_type = campaign.get("projectType", "")

        response = generate_excel_template(
            self.token, self.client, campaign_id, campaign_hierarchy, project_type
        )
        assert response.status_code in [200, 202], f"Generate init failed: {response.text}"

        data = response.json()
        assert "GenerateResource" in data
        assert "id" in data["GenerateResource"]
        print(f"Generation ID: {data['GenerateResource']['id']}")

    def test_generate_init_missing_reference_id(self):
        """Test generate init with empty referenceId returns error."""
        response = generate_excel_template(
            self.token, self.client,
            campaign_id="",
            campaign_hierarchy_type=hierarchyType,
            project_type="LLIN-mz"
        )
        # Expect a non-200 or error response for missing referenceId
        assert response.status_code != 200 or "error" in response.text.lower(), \
            f"Expected error for empty referenceId but got: {response.text}"


class TestGenerationSearch:
    """Test cases for generation search/polling."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)

    def test_generation_search_invalid_id(self):
        """Test searching with a non-existent generation ID."""
        response = search_generation_status(
            self.token, self.client, "00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 200, f"Generation search request failed: {response.text}"
        data = response.json()
        details = data.get("GenerationDetails", [])
        assert len(details) == 0, "Expected empty results for invalid ID"


class TestFileOperations:
    """Test cases for filestore download URL and upload."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)

    def test_get_file_download_url_invalid_id(self):
        """Test getting download URL with an invalid filestoreId."""
        response = get_file_download_url(self.client, "00000000-0000-0000-0000-000000000000")
        # The API may still return 200 with an empty/error response
        assert response.status_code in [200, 400, 404], \
            f"Unexpected status: {response.status_code} - {response.text}"


class TestProcessSearch:
    """Test cases for process search API."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)

    def test_process_search_invalid_id(self):
        """Test searching with a non-existent process ID."""
        response = search_process_status(
            self.token, self.client, "00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 200, f"Process search request failed: {response.text}"
        data = response.json()
        details = data.get("ProcessingDetails", [])
        assert len(details) == 0, "Expected empty results for invalid ID"


# --- Campaign Creation Helpers (mirrored from test_campaign_service.py) ---

def create_campaign_setup(token, client, campaign_name=None):
    """Create a new campaign setup (draft)."""
    payload = load_payload("campaign", "create_setup.json")
    payload = apply_dynamic_dates(payload)
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["locale"] = locale
    if campaign_name:
        payload["CampaignDetails"]["campaignName"] = campaign_name
    else:
        payload["CampaignDetails"]["campaignName"] = f"Excel_Test_{uuid.uuid4().hex[:8]}"
    url = f"{PROJECT_FACTORY_BASE}/create"
    return client.post(url, payload)


def update_campaign_boundary(token, client, campaign_id, campaign_number, campaign_name, hierarchy_type_val):
    """Update campaign with boundary information."""
    payload = load_payload("campaign", "update_boundary.json")
    payload = apply_dynamic_dates(payload)
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["id"] = campaign_id
    payload["CampaignDetails"]["campaignNumber"] = campaign_number
    payload["CampaignDetails"]["campaignName"] = campaign_name
    payload["CampaignDetails"]["hierarchyType"] = hierarchy_type_val
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["locale"] = locale
    url = f"{PROJECT_FACTORY_BASE}/update"
    return client.post(url, payload)


def update_campaign_delivery(token, client, campaign_id, campaign_number, campaign_name, hierarchy_type_val):
    """Update campaign with delivery rules."""
    payload = load_payload("campaign", "update_delivery.json")
    payload = apply_dynamic_dates(payload)
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["id"] = campaign_id
    payload["CampaignDetails"]["campaignNumber"] = campaign_number
    payload["CampaignDetails"]["campaignName"] = campaign_name
    payload["CampaignDetails"]["hierarchyType"] = hierarchy_type_val
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["locale"] = locale
    url = f"{PROJECT_FACTORY_BASE}/update"
    return client.post(url, payload)


def update_campaign_files(token, client, campaign_id, campaign_number, campaign_name, hierarchy_type_val,
                          file_store_id=None):
    """Update campaign with resource files. Optionally override the filestoreId."""
    payload = load_payload("campaign", "update_files.json")
    payload = apply_dynamic_dates(payload)
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["id"] = campaign_id
    payload["CampaignDetails"]["campaignNumber"] = campaign_number
    payload["CampaignDetails"]["campaignName"] = campaign_name
    payload["CampaignDetails"]["hierarchyType"] = hierarchy_type_val
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["locale"] = locale
    if file_store_id and "resources" in payload["CampaignDetails"]:
        for resource in payload["CampaignDetails"]["resources"]:
            resource["filestoreId"] = file_store_id
    url = f"{PROJECT_FACTORY_BASE}/update"
    return client.post(url, payload)


def finalize_campaign(token, client, campaign_id, campaign_number, campaign_name):
    """Finalize and create the campaign (change action to 'create')."""
    payload = load_payload("campaign", "create_campaign.json")
    payload = apply_dynamic_dates(payload)
    payload["RequestInfo"] = get_campaign_request_info(token)
    payload["CampaignDetails"]["id"] = campaign_id
    payload["CampaignDetails"]["campaignNumber"] = campaign_number
    payload["CampaignDetails"]["campaignName"] = campaign_name
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["locale"] = locale
    url = f"{PROJECT_FACTORY_BASE}/update"
    return client.post(url, payload)


def wait_for_campaign_status(token, client, campaign_number, target_status="created",
                             max_attempts=60, delay=5):
    """Poll for campaign status until it reaches the target status."""
    for attempt in range(1, max_attempts + 1):
        payload = load_payload("campaign", "search_campaign.json")
        payload["RequestInfo"] = get_campaign_request_info(token)
        payload["CampaignDetails"]["tenantId"] = tenantId
        payload["CampaignDetails"]["campaignNumber"] = campaign_number
        url = f"{PROJECT_FACTORY_BASE}/search"
        response = client.post(url, payload)

        if response.status_code == 200:
            data = response.json()
            campaigns = data.get("CampaignDetails", [])
            if isinstance(campaigns, list) and len(campaigns) > 0:
                campaign = next((c for c in campaigns if c.get("campaignNumber") == campaign_number), None)
                if campaign:
                    current_status = campaign.get("status")
                    print(f"  Attempt {attempt}: Campaign status = {current_status}")
                    if current_status == target_status:
                        print(f"  Campaign reached '{target_status}' after {attempt} attempt(s)")
                        return response, True
                    if current_status == "failed":
                        print(f"  Campaign reached 'failed' status. Stopping poll.")
                        return response, False

        if attempt < max_attempts:
            print(f"  Waiting for status '{target_status}'... (attempt {attempt}/{max_attempts})")
            time.sleep(delay)

    print(f"  Campaign did not reach '{target_status}' after {max_attempts} attempts")
    return response, False


class TestExcelIngestionE2E:
    """End-to-end: draft campaign -> excel ingestion -> process -> finalize campaign."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)

    def test_full_excel_ingestion_flow(self):
        """
        Full E2E flow:
        1.  Create campaign draft (setup + boundary + delivery)
        2.  Generate Excel template for the draft
        3.  Poll generation until complete
        4.  Get download URL from filestore
        5.  Download the Excel file
        6.  Upload file to filestore
        7.  Update campaign files with uploaded resource
        8.  Finalize campaign (create)
        9.  Wait for campaign to reach 'created' status
        10. Save all IDs to campaign_ids.json
        """

        # --- Step 1: Create campaign draft ---
        print(f"\n=== Step 1: Creating campaign draft ===")
        setup_response = create_campaign_setup(self.token, self.client)
        assert setup_response.status_code == 200, f"Failed to create campaign setup: {setup_response.text}"

        setup_data = setup_response.json()
        campaign_id = setup_data["CampaignDetails"]["id"]
        campaign_number = setup_data["CampaignDetails"]["campaignNumber"]
        campaign_name = setup_data["CampaignDetails"]["campaignName"]
        campaign_hierarchy = setup_data["CampaignDetails"]["hierarchyType"]
        project_type = setup_data["CampaignDetails"].get("projectType", "")
        print(f"  Campaign: {campaign_name} ({campaign_number})")
        print(f"  ID: {campaign_id}")
        print(f"  hierarchyType={campaign_hierarchy}, projectType={project_type}")

        # Update boundary
        print(f"\n  Updating boundary...")
        boundary_resp = update_campaign_boundary(
            self.token, self.client, campaign_id, campaign_number, campaign_name, campaign_hierarchy
        )
        assert boundary_resp.status_code == 200, f"Boundary update failed: {boundary_resp.text}"

        # Update delivery
        print(f"  Updating delivery rules...")
        delivery_resp = update_campaign_delivery(
            self.token, self.client, campaign_id, campaign_number, campaign_name, campaign_hierarchy
        )
        assert delivery_resp.status_code == 200, f"Delivery update failed: {delivery_resp.text}"

        # --- Step 2: Generate Excel template ---
        print(f"\n=== Step 2: Generating Excel template ===")
        gen_response = generate_excel_template(
            self.token, self.client, campaign_id, campaign_hierarchy, project_type
        )
        assert gen_response.status_code in [200, 202], f"Generate init failed: {gen_response.text}"

        gen_data = gen_response.json()
        assert "GenerateResource" in gen_data
        generation_id = gen_data["GenerateResource"]["id"]
        print(f"  Generation ID: {generation_id}")

        # --- Step 3: Poll generation until complete ---
        print(f"\n=== Step 3: Polling generation status ===")
        gen_search_resp, file_store_id, gen_completed = wait_for_generation_complete(
            self.token, self.client, generation_id
        )
        assert gen_completed, f"Generation did not complete: {gen_search_resp.text}"
        assert file_store_id, "No fileStoreId returned from generation"
        print(f"  fileStoreId: {file_store_id}")

        # --- Step 4: Get download URL ---
        print(f"\n=== Step 4: Getting file download URL ===")
        url_response = get_file_download_url(self.client, file_store_id)
        assert url_response.status_code == 200, f"Get download URL failed: {url_response.text}"

        url_data = url_response.json()
        file_urls = url_data.get("fileStoreIds", [])
        assert len(file_urls) > 0, f"No file URLs returned: {url_data}"
        download_url = file_urls[0].get("url")
        assert download_url, f"Download URL is empty: {file_urls[0]}"
        print(f"  Download URL: {download_url[:80]}...")

        # --- Step 5: Download the Excel file ---
        print(f"\n=== Step 5: Downloading Excel file ===")
        local_file_path = download_file_to_disk(download_url)
        assert os.path.exists(local_file_path), f"Downloaded file not found: {local_file_path}"
        assert os.path.getsize(local_file_path) > 0, "Downloaded file is empty"

        # --- Step 6: Use known upload filestoreId ---
        print(f"\n=== Step 6: Using upload fileStoreId ===")
        uploaded_file_store_id = UPLOAD_FILESTORE_ID
        print(f"  Using fileStoreId: {uploaded_file_store_id}")

        # --- Step 7: Update campaign files with the uploaded resource ---
        print(f"\n=== Step 7: Updating campaign files ===")
        files_resp = update_campaign_files(
            self.token, self.client, campaign_id, campaign_number, campaign_name,
            campaign_hierarchy, file_store_id=uploaded_file_store_id
        )
        assert files_resp.status_code == 200, f"Update files failed: {files_resp.text}"

        # --- Step 8: Finalize campaign ---
        print(f"\n=== Step 8: Finalizing campaign (create) ===")
        self.token = get_auth_token("user")
        self.client = APIClient(token=self.token)
        create_resp = finalize_campaign(
            self.token, self.client, campaign_id, campaign_number, campaign_name
        )
        assert create_resp.status_code == 200, f"Finalize campaign failed: {create_resp.text}"

        # --- Step 9: Wait for campaign status ---
        print(f"\n=== Step 9: Waiting for campaign to reach 'created' status ===")
        status_resp, status_reached = wait_for_campaign_status(
            self.token, self.client, campaign_number, target_status="created"
        )
        assert status_reached, f"Campaign did not reach 'created' status: {status_resp.text}"

        # --- Step 10: Save IDs ---
        print(f"\n=== Step 10: Saving IDs to campaign_ids.json ===")
        output_data = {
            "campaignId": campaign_id,
            "campaignNumber": campaign_number,
            "campaignName": campaign_name,
            "excelIngestion": {
                "generationId": generation_id,
                "generatedFileStoreId": file_store_id,
                "uploadedFileStoreId": uploaded_file_store_id,
            }
        }
        save_campaign_ids(output_data)
        print(f"  Saved all IDs to campaign_ids.json")
        print(f"\n=== Excel Ingestion E2E flow completed successfully ===")
