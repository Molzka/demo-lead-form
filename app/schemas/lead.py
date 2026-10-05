import re
from dataclasses import dataclass

FIELD_LIMITS = {
    "name": 120,
    "phone": 60,
    "service": 160,
    "comment": 2000,
    "utm_source": 120,
    "utm_campaign": 160,
}
FIELD_LABELS = {
    "name": "Имя",
    "phone": "Телефон",
    "service": "Услуга",
    "comment": "Комментарий",
    "utm_source": "Источник перехода",
    "utm_campaign": "Кампания",
}


class LeadValidationError(ValueError):
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(message)


@dataclass(frozen=True)
class LeadCreate:
    name: str
    phone: str
    service: str = ""
    comment: str = ""
    utm_source: str | None = None
    utm_campaign: str | None = None

    def __post_init__(self) -> None:
        for field, limit in FIELD_LIMITS.items():
            value = getattr(self, field) or ""
            if len(value) > limit:
                raise LeadValidationError(
                    field, f"{FIELD_LABELS[field]}: не более {limit} символов."
                )
            object.__setattr__(self, field, value.strip())

        phone = self.phone
        if not self.name:
            raise LeadValidationError("name", "Укажите имя.")
        if not phone:
            raise LeadValidationError("phone", "Укажите телефон.")
        digits = re.sub(r"[^0-9]", "", phone)
        if not re.fullmatch(r"\+?[0-9 ()\-]+", phone) or not 10 <= len(digits) <= 15:
            raise LeadValidationError(
                "phone", "Телефон должен содержать от 10 до 15 цифр. Например: +7 (999) 123-45-67."
            )
        object.__setattr__(self, "phone", ("+" if phone.startswith("+") else "") + digits)
