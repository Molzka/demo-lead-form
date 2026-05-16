# LeadForm Demo

Демо: заявка с сайта отправляется в FastAPI backend, сохраняется через SQLAlchemy в SQLite, дописывается в CSV и при наличии настроек отправляется админу в Telegram.

## Запуск

```powershell
uv sync
copy .env.example .env
uv run uvicorn app.main:app --reload
```

Откройте `http://127.0.0.1:8000`.

## Telegram

Создайте бота через BotFather и заполните в `.env`:

```env
TELEGRAM_BOT_TOKEN="123456:token"
TELEGRAM_CHAT_ID="123456789"
```

Если переменные пустые, заявка все равно сохранится в базе и CSV, а отправка в Telegram будет пропущена.

## Endpoints

- `GET /` - форма заявки.
- `POST /lead` - прием заявки.
- `GET /leads` - список заявок в HTML.
- `GET /leads?format=json` - список заявок в JSON.

