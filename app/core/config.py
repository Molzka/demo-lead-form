import os
from dataclasses import dataclass, fields

from dotenv import load_dotenv
from fastapi import Request


@dataclass(frozen=True)
class Settings:
    app_name: str = "LeadForm Demo"
    database_url: str = "sqlite:///./data/leads.db"
    leads_csv_path: str = "./data/leads.csv"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    admin_username: str = ""
    admin_password: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            **{
                field.name: os.getenv(field.name.upper(), field.default)
                for field in fields(cls)
            }
        )

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings
