import os
import msal
import requests
from rag.core.config import settings

AUTHORITY = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"

def get_access_token():
    if not settings.MICROSOFT_CLIENT_ID or not settings.MICROSOFT_CLIENT_SECRET:
        raise ValueError("Microsoft credentials not set in environment.")
        
    app = msal.ConfidentialClientApplication(
        settings.MICROSOFT_CLIENT_ID,
        authority=AUTHORITY,
        client_credential=settings.MICROSOFT_CLIENT_SECRET,
    )
    result = app.acquire_token_silent(SCOPES, account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=SCOPES)
        
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Could not get access token: {result.get('error')} - {result.get('error_description')}")

def get_user_drive(access_token, user_email):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH_ENDPOINT}/users/{user_email}/drive"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def search_folder_in_drive(access_token, drive_id, folder_name="SOPs"):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH_ENDPOINT}/drives/{drive_id}/root:/{folder_name}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def list_drive_items(access_token, drive_id, item_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH_ENDPOINT}/drives/{drive_id}/items/{item_id}/children"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("value", [])

def download_file(access_token, download_url, destination_path):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(download_url, headers=headers, stream=True)
    response.raise_for_status()
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    with open(destination_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return destination_path

def get_all_files_in_folder(access_token, drive_id, item_id, current_path=""):
    files = []
    children = list_drive_items(access_token, drive_id, item_id)
    for child in children:
        name = child.get("name")
        child_path = f"{current_path}/{name}".strip("/")
        if child.get("folder"):
            files.extend(get_all_files_in_folder(access_token, drive_id, child.get("id"), child_path))
        elif child.get("file"):
            ext = os.path.splitext(name)[1].lower()
            if ext in [".docx", ".pdf"]:
                files.append({
                    "id": child.get("id"),
                    "name": name,
                    "path": child_path,
                    "download_url": child.get("@microsoft.graph.downloadUrl")
                })
    return files
