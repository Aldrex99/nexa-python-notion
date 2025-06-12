import os
import requests
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "Authorization": f"Bearer {os.getenv("NOTION_TOKEN")}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def get_database_properties(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()