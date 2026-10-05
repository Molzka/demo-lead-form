# LeadForm Demo

Форма заявки на FastAPI. Контакты сохраняются в SQLite и CSV, уведомления отправляются в Telegram.

## Запуск

Нужны Python 3.12+ и uv. Из корня проекта:

```powershell
uv sync --frozen
Copy-Item .env.example .env
```

В `.env` укажите `ADMIN_USERNAME` и `ADMIN_PASSWORD`. Если файл уже есть, достаточно добавить эти настройки.

```powershell
uv run uvicorn app.main:app --reload
```

- [Форма](http://127.0.0.1:8000/)
- [Список заявок](http://127.0.0.1:8000/leads)
- [Заявки в JSON](http://127.0.0.1:8000/leads?format=json)

Список и JSON требуют логин и пароль из `.env`. Если они не заданы, доступ закрыт. Используется HTTP Basic, поэтому на сервере нужен HTTPS.

База `data/leads.db` создаётся при запуске, `data/leads.csv` — при первой заявке. Пути можно изменить в `.env`.

## Telegram

Создайте бота через BotFather и заполните `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` в `.env`. Без этих настроек форма работает без уведомлений.

Если Telegram или запись CSV недоступны, заявка всё равно сохраняется в базе. Ошибки пишутся в лог, автоматических повторов нет.

## Тесты

```powershell
uv sync --frozen --extra dev
uv run --extra dev pytest
```

Тесты используют временные базу и CSV. Рабочие данные не затрагиваются, запросы в Telegram не отправляются.

