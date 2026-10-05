import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.lead import Lead
from app.schemas.lead import LeadCreate
from app.services.csv_storage import append_lead_to_csv
from app.services.telegram import send_lead_notification

logger = logging.getLogger(__name__)


async def create_lead(db: Session, lead_in: LeadCreate, settings: Settings) -> Lead:
    lead = Lead(
        name=lead_in.name,
        phone=lead_in.phone,
        service=lead_in.service,
        comment=lead_in.comment,
        utm_source=lead_in.utm_source or "",
        utm_campaign=lead_in.utm_campaign or "",
    )
    try:
        db.add(lead)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    # The database is authoritative. An optional export must not turn an
    # already committed submission into a failed response or skip Telegram.
    try:
        append_lead_to_csv(lead, settings.leads_csv_path)
    except Exception as exc:
        logger.warning("CSV export failed for lead %s (%s)", lead.id, type(exc).__name__)
    try:
        await send_lead_notification(lead, settings)
    except Exception as exc:
        logger.warning("Telegram failed for lead %s (%s)", lead.id, type(exc).__name__)
    return lead


def list_leads(db: Session) -> list[Lead]:
    statement = select(Lead).order_by(Lead.created_at.desc())
    return list(db.scalars(statement))
