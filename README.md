# API Automation Framework

A comprehensive Python-based API automation testing framework for microservices testing using pytest. This framework provides reusable utilities, dynamic payload management, and extensive reporting capabilities.

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
- [Configuration](#configuration)
- [Services Covered](#services-covered)
- [Writing Tests](#writing-tests)
- [Running Tests](#running-tests)
- [Reporting](#reporting)
- [CI/CD](#cicd)
- [Utilities Documentation](#utilities-documentation)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

This framework is designed to test multiple microservices with a focus on:
- **Modularity**: Reusable utilities for authentication, API calls, and data management
- **Maintainability**: Separation of test logic, payloads, and configuration
- **Extensibility**: Easy addition of new services and test cases
- **Reporting**: Multiple reporting formats (HTML, Allure)
- **Configuration Management**: Environment-based configuration using `.env` files

---

## Project Structure

```
Console-API-Automation/
├── tests/                          # Test modules
│   ├── test_excel_ingestion.py    # Excel ingestion + campaign creation E2E tests
│   └── test_search_services.py    # Search API tests (Campaign, Project, Facility, Staff)
├── utils/                          # Utility modules
│   ├── api_client.py              # HTTP client wrapper (JSON + file upload)
│   ├── auth.py                    # Authentication token management
│   ├── config.py                  # Configuration loader
│   ├── data_loader.py             # Payload loader with dynamic dates
│   ├── request_info.py            # Request metadata builder
│   └── search_helpers.py          # Common search operations
├── payloads/                       # JSON payload templates
│   ├── campaign/                  # Campaign service payloads
│   │   ├── create_setup.json      # Initial campaign setup
│   │   ├── update_boundary.json   # Add boundary information
│   │   ├── update_delivery.json   # Add delivery rules
│   │   ├── update_files.json      # Add resource files
│   │   ├── create_campaign.json   # Finalize campaign creation
│   │   ├── search_campaign.json   # Search campaigns
│   │   ├── search_project.json    # Search projects by campaign
│   │   ├── search_project_facility.json  # Search project facilities
│   │   └── search_project_staff.json     # Search project staff
│   └── excel_ingestion/           # Excel ingestion service payloads
│       ├── generate_init.json     # Initiate template generation
│       ├── generation_search.json # Poll generation status
│       ├── process_validation.json # Trigger process validation
│       └── process_search.json    # Poll processing status
├── data/                          # Test data
│   ├── inputs.json               # Test input data
│   └── outputs/                  # Test outputs
│       └── campaign_ids.json     # Generated campaign IDs
├── reports/                       # Test reports
│   ├── report.html               # Pytest HTML report
│   ├── junit.xml                 # JUnit XML report (CI/CD)
│   ├── dashboard.html            # Dashboard template
│   ├── campaign_dashboard.html   # Generated campaign dashboard
│   └── campaign_report.html     # Generated campaign report
├── .github/                       # CI/CD configuration
│   └── workflows/
│       └── ci.yml                # GitHub Actions test pipeline
├── generate_dashboard.py         # Dashboard generator script
├── .env                          # Environment configuration
├── .env.example                  # Example environment template
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## Architecture

### Core Components

1. **API Client Layer** (`utils/api_client.py`)
   - Abstraction over HTTP requests
   - Automatic authentication header injection
   - Support for GET, POST, PUT, DELETE methods
   - File upload via multipart/form-data (`upload_file()`)

2. **Authentication Module** (`utils/auth.py`)
   - OAuth2 token acquisition
   - Token caching per service

3. **Configuration Management** (`utils/config.py`)
   - Centralized environment variable loading
   - Reusable search parameters
   - Service-specific configurations

4. **Payload Management** (`utils/data_loader.py`)
   - Dynamic JSON payload loading
   - Template-based payload structure

5. **Request Metadata** (`utils/request_info.py`)
   - Standardized RequestInfo object creation
   - API metadata and user context

6. **Search Helpers** (`utils/search_helpers.py`)
   - Generic search functionality
   - ID extraction from output files
   - Reusable across multiple services

### Test Flow

```
Test Execution
    ↓
Authentication (get_auth_token)
    ↓
API Client Initialization
    ↓
Load Payload Template (data_loader)
    ↓
Inject Dynamic Data (UUID, IDs, etc.)
    ↓
Add RequestInfo
    ↓
API Call (via APIClient)
    ↓
Validate Response (assertions)
    ↓
Store IDs/Data (output files)
    ↓
Generate Reports
```

---

## Prerequisites

- **Python**: 3.8 or higher
- **pip**: Python package manager
- **Virtual Environment**: Recommended for dependency isolation
- **Git**: For version control

---

## Setup and Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Console-API-Automation
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and update with your environment-specific values:

```env
BASE_URL=https://your-api-server.com
USERNAME=your_username
PASSWORD=your_password
TENANTID=your_tenant
LOCALE=en_MZ
USERTYPE=EMPLOYEE
CLIENT_AUTH_HEADER=Basic <base64_encoded_credentials>

SEARCH_LIMIT=200
SEARCH_OFFSET=0

HIERARCHYTYPE=MICROPLAN
BOUNDARY_TYPE=LOCALITY
BOUNDARY_CODE=your_boundary_code

SERVICE_EXCEL_INGESTION=/excel-ingestion/v1/data
SERVICE_FILESTORE=/filestore/v1/files
```

### 5. Verify Setup

```bash
python -m pytest tests/ -v
```

---

## Configuration

### Environment Variables (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `BASE_URL` | API base URL | `https://hcm-demo.digit.org` |
| `USERNAME` | API username | `Shreya` |
| `PASSWORD` | API password | `eGov@1234` |
| `TENANTID` | Tenant identifier | `mz` |
| `LOCALE` | Locale setting | `en_MZ` |
| `USERTYPE` | User type | `EMPLOYEE` |
| `CLIENT_AUTH_HEADER` | Basic auth header for OAuth | `Basic ZWdvdi11c2VyLWNsaWVudDo=` |
| `SEARCH_LIMIT` | Default search limit | `200` |
| `SEARCH_OFFSET` | Default search offset | `0` |
| `HIERARCHYTYPE` | Boundary hierarchy type | `MICROPLAN` |
| `BOUNDARY_TYPE` | Boundary type | `LOCALITY` |
| `BOUNDARY_CODE` | Boundary code | `MICROPLAN_MO_13_03_02_03_02_TUGLOR` |
| `SERVICE_PROJECT` | Project service endpoint | `/project/v1` |
| `SERVICE_PROJECT_FACILITY` | Project facility endpoint | `/project/facility/v1` |
| `SERVICE_PROJECT_STAFF` | Project staff endpoint | `/project/staff/v1` |
| `SERVICE_PROJECT_FACTORY` | Project factory endpoint | `/project-factory/v1/project-type` |
| `SERVICE_EXCEL_INGESTION` | Excel ingestion endpoint | `/excel-ingestion/v1/data` |
| `SERVICE_FILESTORE` | Filestore endpoint | `/filestore/v1/files` |

### Pytest Configuration (pytest.ini)

```ini
[pytest]
pythonpath = .
```

This ensures the root directory is in the Python path for imports.

---

## Services Covered

| Service | Operations | Test File |
|---------|-----------|-----------|
| **Excel Ingestion + Campaign** | Draft Campaign, Generate Template, Poll Generation, Download File, Upload File, Process Validation, Update Files, Finalize Campaign | `test_excel_ingestion.py` |
| **Search Services** | Search Campaign, Search Project, Search Project Facility, Search Project Staff | `test_search_services.py` |

**Total: 2 Test Files, 13 Payload Templates**

### Test Classes

#### test_excel_ingestion.py
- `TestGenerateExcelTemplate` - Template generation tests (2 tests)
- `TestGenerationSearch` - Generation search/polling tests (1 test)
- `TestFileOperations` - Filestore download URL tests (1 test)
- `TestProcessValidation` - Process validation API tests (1 test)
- `TestProcessSearch` - Process search tests (2 tests)
- `TestExcelIngestionE2E` - End-to-end flow: draft campaign → excel ingestion → finalize campaign (1 test)

#### test_search_services.py
- `TestCampaignSearchService` - Campaign search API tests (4 tests)
- `TestProjectSearchService` - Project search API tests (5 tests)
- `TestProjectFacilitySearchService` - Project facility search tests (5 tests)
- `TestProjectStaffSearchService` - Project staff search tests (5 tests)
- `TestSearchServicesE2E` - End-to-end search flow test (1 test)

### Excel Ingestion + Campaign E2E Flow

The `TestExcelIngestionE2E` test covers the full campaign lifecycle with excel ingestion:

1. **Create Campaign Draft** - Setup with boundary and delivery rules
2. **Generate Excel Template** - POST to `/excel-ingestion/v1/data/generate/_init`
3. **Poll Generation Status** - POST to `/excel-ingestion/v1/data/generate/_search`
4. **Get Download URL** - GET from `/filestore/v1/files/url`
5. **Download Excel File** - Download from pre-signed S3 URL
6. **Use Upload FileStoreId** - Use pre-configured filestoreId for upload
7. **Update Campaign Files** - Attach resource with uploaded filestoreId
8. **Finalize Campaign** - Change action to `create`
9. **Wait for Campaign Status** - Poll until `created`
10. **Save IDs** - Write `campaign_ids.json` for downstream tests

### Search Services Flow

After the campaign is created, the search tests validate:

1. **Search Campaign** - Find campaign by number and ID
2. **Search Project** - Find projects by campaign number (referenceID)
3. **Search Project Facility** - Find facilities assigned to projects
4. **Search Project Staff** - Find staff assigned to projects

---

## Writing Tests

### Test Structure

Each test module follows this pattern:

```python
# 1. Imports
from utils.api_client import APIClient
from utils.auth import get_auth_token
from utils.data_loader import load_payload, apply_dynamic_dates
from utils.request_info import get_request_info
from utils.config import tenantId, locale

# 2. Test Functions (with assertions)
def test_create_campaign():
    """Test case with assertions"""
    token = get_auth_token("user")
    client = APIClient(token=token)

    response = create_campaign_setup(token, client)

    # Assertions
    assert response.status_code in [200, 202], f"Failed: {response.text}"
    campaign_id = response.json()["CampaignDetails"]["id"]
    assert campaign_id, "Campaign ID not generated"

    # Store ID for later use
    with open("data/outputs/campaign_ids.json", "w") as f:
        json.dump({"campaignId": campaign_id}, f)

# 3. Helper Functions (reusable, no assertions)
def create_campaign_setup(token, client):
    """Helper function for campaign creation"""
    payload = load_payload("campaign", "create_setup.json")
    payload = apply_dynamic_dates(payload)  # Set future dates

    # Inject dynamic data
    payload["RequestInfo"] = get_request_info(token)
    payload["CampaignDetails"]["tenantId"] = tenantId
    payload["CampaignDetails"]["locale"] = locale

    return client.post("/project-factory/v1/project-type/create", payload)
```

### Key Principles

1. **Separation of Concerns**: Test functions contain assertions; helper functions contain reusable logic
2. **Token Reuse**: Obtain token once per test, reuse across operations
3. **Dynamic Data Injection**: Use UUID for unique identifiers, extract IDs from output files for dependencies
4. **Status Code Flexibility**: Accept both 200 (OK) and 202 (Accepted)
5. **Detailed Error Messages**: Include response text in assertion failures

### Adding a New Service

1. **Create Payload Directory**:
   ```bash
   mkdir payloads/new_service
   ```

2. **Add Payload Templates**:
   ```bash
   # Create JSON files for create, search operations
   touch payloads/new_service/create_entity.json
   touch payloads/new_service/search_entity.json
   ```

3. **Create Test File**:
   ```bash
   touch tests/test_new_service.py
   ```

4. **Implement Tests**:
   ```python
   from utils.api_client import APIClient
   from utils.auth import get_auth_token
   from utils.data_loader import load_payload, apply_dynamic_dates
   from utils.request_info import get_request_info
   from utils.config import tenantId, locale
   import uuid

   def test_create_new_entity():
       token = get_auth_token("user")
       client = APIClient(token=token)

       response = create_new_entity(token, client)
       assert response.status_code in [200, 202]

   def create_new_entity(token, client):
       payload = load_payload("new_service", "create_entity.json")
       payload = apply_dynamic_dates(payload)  # If payload has date fields
       payload["Entity"]["clientReferenceId"] = str(uuid.uuid4())
       payload["RequestInfo"] = get_request_info(token)
       return client.post("/new-service/v1/_create", payload)
   ```

---

## Running Tests

### Normal Execution

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests (excel ingestion first, then search)
python -m pytest tests/test_excel_ingestion.py tests/test_search_services.py -v -s

# Run only excel ingestion tests
python -m pytest tests/test_excel_ingestion.py -v -s

# Run only search tests (requires campaign_ids.json from a prior run)
python -m pytest tests/test_search_services.py -v -s

# Run E2E tests only
python -m pytest tests/test_excel_ingestion.py::TestExcelIngestionE2E -v -s
python -m pytest tests/test_search_services.py::TestSearchServicesE2E -v -s

# Run specific test class
python -m pytest tests/test_search_services.py::TestProjectSearchService -v
python -m pytest tests/test_search_services.py::TestProjectFacilitySearchService -v

# Run with verbose output
python -m pytest tests/ -v

# Run with print statements visible
python -m pytest tests/ -s
```

### HTML Report Generation

```bash
python -m pytest tests/ --html=reports/report.html --self-contained-html
```

The HTML report will be generated at `reports/report.html` with:
- Test results summary
- Pass/Fail status
- Execution time
- Error details

### Allure Report Generation

```bash
# Generate Allure results
python -m pytest --alluredir=allure-results

# Generate Allure report
allure generate allure-results --clean -o allure-report

# Open Allure report in browser
allure open allure-report
```

### Fresh Test Run (Clear Previous IDs)

```bash
rm -f data/outputs/campaign_ids.json && python -m pytest tests/test_excel_ingestion.py tests/test_search_services.py --html=reports/report.html --self-contained-html
```

This removes the previous campaign IDs file before running tests, ensuring a clean test run.

---

## Reporting

### Output Files

1. **data/outputs/campaign_ids.json**
   - Stores campaign details created during test execution
   - JSON format with comprehensive campaign data:
     - `campaignId`, `campaignNumber`, `campaignName`
     - `excelIngestion` - Generation and upload IDs
     - `totalCount` - Total projects created
     - `projectsByBoundaryType` - Project IDs grouped by boundary type
     - `facilityCount` - Total facilities assigned
     - `facilityIds` - List of facility IDs
     - `staffCount` - Total staff assigned
     - `staffIds` - List of staff IDs

### Report Types

1. **HTML Report** (`reports/report.html`)
   - Self-contained HTML file
   - Summary dashboard with pass/fail counts
   - Detailed test results with error traces

2. **JUnit XML Report** (`reports/junit.xml`)
   - Standard JUnit XML format for CI/CD integration
   - Generated with `--junitxml=reports/junit.xml`
   - Used by GitHub Actions to publish test results to PR checks

3. **Campaign Dashboard** (`reports/campaign_dashboard.html`)
   - Visual dashboard showing campaign test results
   - Displays campaign details, projects, facilities, and staff
   - Auto-generated from test output data via `generate_dashboard.py`

4. **Campaign Report** (`reports/campaign_report.html`)
   - Generated by the search services E2E test
   - Contains campaign, project, facility, and staff data from test execution

---

## Dashboard

The framework includes a visual dashboard to display campaign test results.

### Generate Dashboard

```bash
# Generate dashboard from test output
python3 generate_dashboard.py
```

### View Dashboard

```bash
# Open dashboard in default browser
xdg-open reports/campaign_dashboard.html

# Or use Python HTTP server
cd reports && python3 -m http.server 8080
# Then open http://localhost:8080/campaign_dashboard.html
```

### Dashboard Features

The dashboard displays:

| Section | Description |
|---------|-------------|
| **Stats Cards** | Campaign count, Projects, Facilities, Staff, Boundary Types |
| **Campaign Details** | Campaign ID, Number, Name, Status |
| **Projects by Boundary** | Project IDs grouped by boundary type (COUNTRY, PROVINCE, DISTRICT, etc.) |
| **Facilities** | List of all facility IDs |
| **Staff** | List of all staff IDs |

### Regenerate After Tests

```bash
# Run tests and regenerate dashboard
python -m pytest tests/test_excel_ingestion.py tests/test_search_services.py -v && python3 generate_dashboard.py

# Open updated dashboard
xdg-open reports/campaign_dashboard.html
```

---

## CI/CD

The project includes a GitHub Actions pipeline (`.github/workflows/ci.yml`) for automated testing.

### Triggers

- **Push** to `main` branch
- **Pull requests** targeting `main`
- **Manual** via `workflow_dispatch`

### Pipeline Steps

1. Checkout code and set up Python 3.10 with pip caching
2. Install dependencies from `requirements.txt`
3. Create `.env` file from GitHub repository secrets
4. Create `data/outputs/` directory
5. Run pytest with JUnit XML and HTML reports
6. Upload test results and reports as artifacts (30-day retention)
7. Publish test results to PR checks via `publish-unit-test-result-action`

### Required GitHub Secrets

All environment variables from `.env` must be configured as repository secrets. See `.env.example` for the full list of required variables.

### Viewing Results

- **PR Checks**: Test results are published directly to pull request checks
- **Artifacts**: Download `test-results` artifact for HTML reports and campaign output data
- **JUnit**: Download `junit-results` artifact for CI integration

---

## Utilities Documentation

### api_client.py

**Class: APIClient**

HTTP client wrapper with automatic authentication.

```python
from utils.api_client import APIClient

# Initialize with token
client = APIClient(token="your_token_here")

# Make requests
response = client.get("/endpoint")
response = client.post("/endpoint", payload)
response = client.put("/endpoint", payload)
response = client.delete("/endpoint")

# Upload file (multipart/form-data)
response = client.upload_file("/filestore/v1/files", "path/to/file.xlsx", {"tenantId": "mz"})
```

**Constructor Parameters:**
- `service` (optional): Service name to fetch token for
- `token` (optional): Direct token value
- Must provide either `service` or `token`

**Methods:**
- `get(endpoint, params=None)`: GET request
- `post(endpoint, data=None)`: POST request
- `put(endpoint, data=None)`: PUT request
- `delete(endpoint)`: DELETE request
- `upload_file(endpoint, file_path, form_fields=None)`: Multipart file upload

### auth.py

**Function: get_auth_token(service)**

Obtains OAuth2 access token for a service.

```python
from utils.auth import get_auth_token

token = get_auth_token("user")
```

**Parameters:**
- `service` (str): Service name (e.g., "user", "individual")

**Returns:**
- `str`: Access token

**Raises:**
- `Exception`: If authentication fails

### config.py

Configuration module with environment variables.

```python
from utils.config import BASE_URL, tenantId, locale, search_params

# Use configuration values
url = BASE_URL
tenant = tenantId
loc = locale  # e.g., "en_MZ"
params = search_params  # Contains limit, offset, tenantId
```

**Available Variables:**
- `BASE_URL`: API base URL
- `tenantId`: Tenant identifier
- `locale`: Locale setting (e.g., `en_IN`)
- `search_limit`, `search_offset`: Pagination settings
- `search_params`: Dictionary with limit, offset, tenantId
- `hierarchyType`, `boundaryCode`, `boundaryType`: Boundary configs
- `SERVICE_EXCEL_INGESTION`: Excel ingestion service endpoint
- `SERVICE_FILESTORE`: Filestore service endpoint

### data_loader.py

**Function: load_payload(service_name, filename)**

Loads JSON payload template.

```python
from utils.data_loader import load_payload

payload = load_payload("campaign", "create_setup.json")
payload = load_payload("excel_ingestion", "generate_init.json")
```

**Parameters:**
- `service_name` (str): Service folder name under `payloads/`
- `filename` (str): JSON file name

**Returns:**
- `dict`: Parsed JSON payload

**Function: apply_dynamic_dates(payload)**

Applies dynamic future dates to campaign payloads, preventing test failures from expired dates.

```python
from utils.data_loader import load_payload, apply_dynamic_dates

payload = load_payload("campaign", "create_setup.json")
payload = apply_dynamic_dates(payload)  # Sets dates to tomorrow -> one month later
```

**Parameters:**
- `payload` (dict): Campaign payload dictionary

**Returns:**
- `dict`: Payload with updated date fields:
  - `startDate`: Tomorrow at midnight (Unix timestamp ms)
  - `endDate`: One month after tomorrow (Unix timestamp ms)
  - Cycle dates in `deliveryRules`
  - ISO dates in `additionalDetails.cycleData`

**Helper Functions:**
- `get_tomorrow_timestamp()`: Returns tomorrow at midnight as Unix timestamp (ms)
- `get_one_month_later_timestamp()`: Returns one month after tomorrow as Unix timestamp (ms)
- `get_tomorrow_iso()`: Returns tomorrow in ISO format (`YYYY-MM-DDTHH:MM:SS.000Z`)
- `get_one_month_later_iso()`: Returns one month after tomorrow in ISO format

### request_info.py

**Function: get_request_info(token)**

Creates standardized RequestInfo object.

```python
from utils.request_info import get_request_info

request_info = get_request_info(token)
payload["RequestInfo"] = request_info
```

**Parameters:**
- `token` (str): Authentication token

**Returns:**
- `dict`: RequestInfo object with API metadata, user context, and authentication

---

## Best Practices

### 1. Test Independence

- Each test should be independent and not rely on execution order
- Use output files for sharing data between tests that must run sequentially
- Clean up test data when possible

### 2. Error Handling

- Always include response text in assertion messages for debugging
- Use try-except blocks for critical operations
- Log errors to output files

### 3. Payload Management

- Keep payloads as templates with minimal hardcoded values
- Inject dynamic data (UUIDs, IDs) at runtime
- Reuse payloads across similar tests

### 4. Code Reusability

- Extract common operations into helper functions
- Use utility modules for shared functionality
- Follow DRY (Don't Repeat Yourself) principle

### 5. Documentation

- Add docstrings to test functions and helpers
- Comment complex logic
- Keep README updated with new services/features

### 6. Version Control

- Commit frequently with meaningful messages
- Use feature branches for new services
- Keep `.env` file out of version control (add to `.gitignore`)

---

## Troubleshooting

### Common Issues

1. **Authentication Failure**
   - Verify `.env` credentials are correct
   - Check CLIENT_AUTH_HEADER is properly base64 encoded
   - Ensure token hasn't expired

2. **Import Errors**
   - Verify virtual environment is activated
   - Check `pytest.ini` has `pythonpath = .`
   - Install all required dependencies

3. **Test Failures**
   - Check API endpoint availability
   - Verify payload structure matches API requirements
   - Check `data/outputs/campaign_ids.json` for created campaign details

4. **Date-Related Failures**
   - Campaign dates must be in the future
   - Use `apply_dynamic_dates()` to auto-set valid dates

5. **Search Tests Failing**
   - Run `test_excel_ingestion.py` first to create a campaign and generate `campaign_ids.json`
   - Verify `campaign_ids.json` contains valid `campaignId` and `campaignNumber`
