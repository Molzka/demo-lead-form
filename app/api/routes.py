from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.lead import LeadCreate
from app.services.leads import create_lead, list_leads

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
):
    try:
        lead_in = LeadCreate(
            name=name,
            phone=phone,
            service=service,
            comment=comment,
            utm_source=utm_source,
            utm_campaign=utm_campaign,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "app_name": "LeadForm Demo",
                "error": str(exc),
                "form": {
                    "name": name,
                    "phone": phone,
                    "service": service,
                    "comment": comment,
                    "utm_source": utm_source or "",
                    "utm_campaign": utm_campaign or "",
                },
            },
            status_code=422,
        )

    lead = await create_lead(db, lead_in)
    return templates.TemplateResponse(
        request,
        "success.html",
        {
            "lead": lead,
        },
    )


@router.get("/leads")
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
