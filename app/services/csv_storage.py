import csv
from pathlib import Path

from app.core.config import settings
from app.models.lead import Lead

CSV_FIELDS = [
    "id",
    "created_at",
    "name",
    "phone",
    "service",
    "comment",
    "utm_source",
    "utm_campaign",
    "source",
]


def append_lead_to_csv(lead: Lead) -> None:
    csv_path = Path(settings.leads_csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "id": lead.id,
                "created_at": lead.created_at.isoformat(sep=" ", timespec="seconds"),
                "name": lead.name,
                "phone": lead.phone,
                "service": lead.service,
                "comment": lead.comment,
                "utm_source": lead.utm_source,
                "utm_campaign": lead.utm_campaign,
                "source": lead.source,
            }
        )
