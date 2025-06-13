import os
import requests
import datetime
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "Authorization": f"Bearer {os.getenv("NOTION_TOKEN")}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

INTERVENTIONSDB = os.getenv("DB_INTERVENTIONS_ID")
INVOICESDB = os.getenv("DB_INVOICES_ID")

def query_unbilled_entries(date_start: str, date_end: str, already_factured: bool | None):
    """
    Query unbilled entries from the Notion database within a specified date range.
    :param date_start:
    :param date_end:
    :param already_factured:
    :return:
    """

    if not date_start or not date_end:
        raise ValueError("date_start and date_end must be provided")

    date_start = datetime.datetime.strptime(date_start, "%Y-%m-%d")
    date_end = datetime.datetime.strptime(date_end, "%Y-%m-%d")

    if date_start > date_end:
        raise ValueError("date_start must be before date_end")

    query = {
        "filter": {
            "and": [
                {
                    "property": "Date de début",
                    "date": {
                        "on_or_after": date_start.strftime("%Y-%m-%d")
                    }
                },
                {
                    "property": "Date de fin",
                    "date": {
                        "on_or_before": date_end.strftime("%Y-%m-%d")
                    }
                },
                {
                    "property": "Facturé",
                    "checkbox": {
                        "equals": already_factured
                    }
                }
            ]
        },
        "sorts": [
            {
                "property": "Date de début",
                "direction": "ascending"
            }
        ]
    }

    if already_factured is None:
        query = {
            "filter": {
                "and": [
                    {
                        "property": "Date de début",
                        "date": {
                            "on_or_after": date_start.strftime("%Y-%m-%d")
                        }
                    },
                    {
                        "property": "Date de fin",
                        "date": {
                            "on_or_before": date_end.strftime("%Y-%m-%d")
                        }
                    },
                ]
            },
            "sorts": [
                {
                    "property": "Date de début",
                    "direction": "ascending"
                }
            ]
        }

    response = requests.post(
        f"https://api.notion.com/v1/databases/{INTERVENTIONSDB}/query",
        headers=HEADERS,
        json=query
    )

    response.raise_for_status()
    return response.json()["results"]

def create_invoice_page(client: str, interventions: list, mois: str, invoice_number: str):
    """
    Create an invoice page in the Notion database for a given client with detailed interventions.
    :param client: Name of the client
    :param interventions: List of interventions
    :param mois: Month for the invoice
    :param invoice_number:  number
    :return: Response from the Notion API
    """
    total_amount = 0
    if not interventions:
        return 'No interventions provided for invoice creation'
    for item in interventions:
        if not item.get("properties"):
            return 'Invalid item format: missing properties'
        props = item["properties"]
        total_amount += props['Nombre heures']['number'] * props['Tarif horaire']['number']

    children = generate_invoice_blocks(interventions, client, mois)

    payload = {
        "parent": {"database_id": INVOICESDB},
        "properties": {
            "Client": {"title": [{"text": {"content": client}}]},
            "Mois": {"rich_text": [{"text": {"content": datetime.datetime.now().strftime("%B %Y")}}]},
            "Total Amount": {"number": float(total_amount)},
            "Invoice Number": {"rich_text": [{"text": {"content": invoice_number}}]}
        },
        "children": children
    }

    response = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
    response.raise_for_status()

    return response.json()

def generate_invoice_blocks(interventions: list, client: str, mois: str):
    """Generate blocks for the invoice page from the list of interventions.
    :param interventions: List of interventions
    :param client: Name of the client
    :param mois: Month for the invoice
    :return: children blocks and total amount
    """
    children = [
        {"object": "block", "type": "heading_1",
         "heading_1": {"rich_text": [{"type": "text", "text": {"content": "FACTURE"}}]}},
        {"object": "block", "type": "paragraph",
         "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"Client : {client}"}}]}},
        {"object": "block", "type": "paragraph",
         "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"Mois : {mois}"}}]}},
        {"object": "block", "type": "divider", "divider": {}},
        {"object": "block", "type": "heading_2",
         "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Détail des interventions"}}]}},
        {"object": "block", "type": "paragraph",
         "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Cours | Heures | Tarif | Total\n--- | --- | --- | ---"}}]}}
    ]
    total_amount = 0
    for item in interventions:
        if not item.get("properties"):
            return 'Invalid item format: missing properties'
        props = item["properties"]
        row = f"{props['Cours']['title'][0]['plain_text']} | {props['Nombre heures']['number']}h | {props['Tarif horaire']['number']}€ | {props['Nombre heures']['number'] * props['Tarif horaire']['number']}€"
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": row}}]
            }
        })
        total_amount += props['Nombre heures']['number'] * props['Tarif horaire']['number']

    children.append({
        "object": "block",
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": "💰"},
            "rich_text": [{"type": "text", "text": {"content": f"Total à payer : {total_amount} €"}}]
        }
    })

    return children
