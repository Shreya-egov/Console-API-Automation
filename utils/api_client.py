import os
import mimetypes
from utils.auth import get_auth_token
from utils.config import BASE_URL
import requests

class APIClient:
    def __init__(self, service=None, token=None):
        if not token and service:
            token = get_auth_token(service)
        elif not token:
            raise ValueError("Either 'service' or 'token' must be provided")

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

    def get(self, endpoint):
        return requests.get(BASE_URL + endpoint, headers=self.headers)

    def post(self, endpoint, data):
        return requests.post(BASE_URL + endpoint, headers=self.headers, json=data)

    def put(self, endpoint, data):
        return requests.put(BASE_URL + endpoint, headers=self.headers, json=data)

    def delete(self, endpoint):
        return requests.delete(BASE_URL + endpoint, headers=self.headers)

    def upload_file(self, endpoint, file_path, form_fields=None):
        """Upload a file using multipart/form-data.

        Args:
            endpoint: API endpoint path
            file_path: Path to the file to upload
            form_fields: Optional dict of additional form fields
        """
        headers = {"Authorization": self.headers["Authorization"]}
        filename = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, content_type)}
            return requests.post(
                BASE_URL + endpoint,
                headers=headers,
                files=files,
                data=form_fields or {},
            )