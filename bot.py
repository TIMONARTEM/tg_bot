import os
import asyncio
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from openai import OpenAI
from threading import Thread

# --- Настройки токенов ---
TELEGRAM_TOKEN = os.getenv("8370187250:AAHaAFePonylTO3Bn5CsQoA2Vw25h_JHXl0")
OPENAI_API_KEY = os.getenv("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")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("❌ Укажи TELEGRAM_TOKEN и OPENAI_API_KEY в Render Environment Variables")

# --- Инициализация клиентов ---
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Flask: нужен Render, чтобы видеть 'порт' ---
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram ChatGPT бот работает!"

# --- Обработчики Telegram ---
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет 👋 Я бот, подключённый к ChatGPT! Напиши мне что-нибудь.")

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
    await dp.start_polling(bot)

# --- Flask в отдельном потоке, чтобы Render не падал ---
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(start_bot())
