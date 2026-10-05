import logging

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import require_admin
from app.db.session import get_db
from app.schemas.lead import FIELD_LIMITS, LeadCreate, LeadValidationError
from app.services.leads import create_lead, list_leads

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["field_limits"] = FIELD_LIMITS
logger = logging.getLogger(__name__)


@router.post("/lead", response_class=HTMLResponse)
async def submit_lead(
    request: Request,
    name: str = Form(""),
    phone: str = Form(""),
    service: str = Form(""),
    comment: str = Form(""),
    utm_source: str | None = Form(None),
    utm_campaign: str | None = Form(None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    form = {
        "name": name,
        "phone": phone,
        "service": service,
        "comment": comment,
        "utm_source": utm_source or "",
        "utm_campaign": utm_campaign or "",
    }
    context = {"app_name": settings.app_name, "form": form}
    try:
        lead_in = LeadCreate(**form)
    except LeadValidationError as exc:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                **context,
                "error": str(exc),
                "error_field": exc.field,
            },
            status_code=422,
        )

    try:
        await create_lead(db, lead_in, settings)
    except SQLAlchemyError as exc:
        logger.error("Lead could not be saved (%s)", type(exc).__name__)
        return templates.TemplateResponse(
            request, "index.html",
            {**context, "error": "Не удалось сохранить заявку. Попробуйте отправить её ещё раз чуть позже."},
            status_code=503,
        )
    return RedirectResponse("/success", status_code=303)


@router.get("/success", response_class=HTMLResponse)
def submission_result(request: Request, settings: Settings = Depends(get_settings)):
    return templates.TemplateResponse(
        request, "success.html", {"app_name": settings.app_name},
    )


@router.get("/leads", dependencies=[Depends(require_admin)])
def get_leads(
    request: Request,
    format_: str = Query("html", alias="format", pattern="^(html|json)$"),
    db: Session = Depends(get_db),
):
    leads = list_leads(db)

    if format_ == "json":
        return JSONResponse(
            [
                {
                    "id": lead.id,
                    "created_at": lead.created_at.isoformat(),
                    "name": lead.name,
                    "phone": lead.phone,
                    "service": lead.service,
                    "comment": lead.comment,
                    "utm_source": lead.utm_source,
                    "utm_campaign": lead.utm_campaign,
                    "source": lead.source,
                }
                for lead in leads
            ]
        )

    return templates.TemplateResponse(
        request,
        "leads.html",
        {
            "leads": leads,
        },
    )
