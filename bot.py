import os
import asyncio
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
import openai

# --- Удаляем proxy-переменные, чтобы Render не ломал OpenAI ---
for proxy_var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    if proxy_var in os.environ:
        del os.environ[proxy_var]

# --- Токены из Environment Variables ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("❌ Укажи TELEGRAM_TOKEN и OPENAI_API_KEY в Render Environment Variables")

# --- Настройка OpenAI ---
openai.api_key = OPENAI_API_KEY

# --- Telegram Bot ---
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- Flask для Render ---
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
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты дружелюбный Telegram-бот."},
                {"role": "user", "content": user_text},
            ],
        )
        reply = completion.choices[0].message["content"]
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

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.get_event_loop().run_until_complete(start_bot())
