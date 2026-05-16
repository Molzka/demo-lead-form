from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.schemas.lead import LeadCreate
from app.services.csv_storage import append_lead_to_csv
from app.services.telegram import send_lead_notification


async def create_lead(db: Session, lead_in: LeadCreate) -> Lead:
    lead = Lead(
        name=lead_in.name,
        phone=lead_in.phone,
        service=lead_in.service,
        comment=lead_in.comment,
        utm_source=lead_in.utm_source or "",
        utm_campaign=lead_in.utm_campaign or "",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    append_lead_to_csv(lead)
    await send_lead_notification(lead)
    return lead


def list_leads(db: Session) -> list[Lead]:
    statement = select(Lead).order_by(Lead.created_at.desc())
    return list(db.scalars(statement))
