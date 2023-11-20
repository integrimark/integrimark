import requests
import os

# Constants
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "cit-5920"
REPO_NAME = "fall-2023"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "GitHub-Asset-Downloader",
}

# Get the latest release
response = requests.get(
    f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest", headers=HEADERS
)
response.raise_for_status()
release_data = response.json()

# Filter assets that are PDFs and contain "Solutions" in their name
solution_files = [
    asset
    for asset in release_data["assets"]
    if asset["name"].endswith(".pdf") and "Solutions" in asset["name"]
]

# Download each file
for asset in solution_files:
    print(f"Downloading {asset['name']}...")
    download_response = requests.get(asset["browser_download_url"], stream=True)
    download_response.raise_for_status()

    with open(asset["name"], "wb") as f:
        for chunk in download_response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"{asset['name']} downloaded successfully!")

print("All files downloaded!")
