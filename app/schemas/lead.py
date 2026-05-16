from dataclasses import dataclass


@dataclass(frozen=True)
class LeadCreate:
    name: str
    phone: str
    service: str = ""
    comment: str = ""
    utm_source: str | None = None
    utm_campaign: str | None = None

    def __post_init__(self) -> None:
        name = self.name.strip()
        phone = self.phone.strip()
        if not name:
            raise ValueError("Укажите имя.")
        if not phone:
            raise ValueError("Укажите телефон.")

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "phone", phone)
        object.__setattr__(self, "service", self.service.strip())
        object.__setattr__(self, "comment", self.comment.strip())
        object.__setattr__(self, "utm_source", (self.utm_source or "").strip())
        object.__setattr__(self, "utm_campaign", (self.utm_campaign or "").strip())
