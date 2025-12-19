import os
from dotenv import load_dotenv

load_dotenv(override=True)  # This forces reloading of updated values

BASE_URL = os.getenv("BASE_URL")
tenantId = os.getenv("TENANTID", "mz")
locale = os.getenv("LOCALE", "en_MZ")

search_limit = os.getenv("SEARCH_LIMIT", "100")
search_offset = os.getenv("SEARCH_OFFSET", "0")
hierarchyType = os.getenv("HIERARCHYTYPE")
boundaryCode = os.getenv("BOUNDARY_CODE")
boundaryType=os.getenv("BOUNDARY_TYPE")

if not BASE_URL:
    raise ValueError("BASE_URL not found in .env")


# Define reusable params dict
search_params = {
    "limit": search_limit,
    "offset": search_offset,
    "tenantId": tenantId
}

# Service Endpoints
SERVICE_CAMPAIGN = os.getenv("SERVICE_CAMPAIGN", "project-factory")
SERVICE_PROJECT = os.getenv("SERVICE_PROJECT", "/project/v1")
SERVICE_PROJECT_FACILITY = os.getenv("SERVICE_PROJECT_FACILITY", "/project/facility/v1")
SERVICE_PROJECT_STAFF = os.getenv("SERVICE_PROJECT_STAFF", "/project/staff/v1")
SERVICE_PROJECT_FACTORY = os.getenv("SERVICE_PROJECT_FACTORY", "/project-factory/v1/project-type")