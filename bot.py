import os
import asyncio
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

# --- Удаляем proxy-переменные ДО импорта openai ---
for proxy_var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    if proxy_var in os.environ:
        del os.environ[proxy_var]

# --- Monkey patch для OpenAI: убираем неожиданный аргумент proxies ---
import openai

_old_client_init = openai.OpenAI.__init__


def _patched_init(self, *args, **kwargs):
    kwargs.pop("proxies", None)
    return _old_client_init(self, *args, **kwargs)


openai.OpenAI.__init__ = _patched_init

from openai import OpenAI

# --- Токены из Environment Variables ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("❌ Укажи TELEGRAM_TOKEN и OPENAI_API_KEY в Render Environment Variables")

# --- Инициализация клиентов ---
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Flask сервер для Render ---
app = Flask(__name__)


@app.route("/")
def home():
    return "✅ Telegram ChatGPT бот работает на Render!"


# --- Обработчики Telegram ---
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет 👋 Я бот, подключённый к ChatGPT!")


@dp.message()
async def chatgpt_handler(message: Message):
    user_text = message.text.strip()
    await message.answer("⏳ Думаю над ответом...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты дружелюбный Telegram-бот."},
                {"role": "user", "content": user_text},
            ],
        )
        reply = response.choices[0].message.content
        await message.answer(reply)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")


# --- Асинхронный запуск бота ---
async def start_bot():
    print("✅ Бот запущен и ждёт сообщений...")
    await dp.start_polling(bot)


# --- Flask в отдельном потоке ---
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# --- Точка входа ---
if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    asyncio.get_event_loop().run_until_complete(start_bot())
