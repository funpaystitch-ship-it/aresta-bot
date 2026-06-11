#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# ─── ТОКЕНЫ ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8869661255:AAHMa3SZyr2BG9FL9YSbAOVUV30Pt48YHtE"
GROQ_API_KEY   = "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"

# ─── НАСТРОЙКИ ─────────────────────────────────────────────────────────────────
MODEL   = "llama-3.3-70b-versatile"
MAX_HISTORY = 20  # сколько сообщений помнит бот

SYSTEM_PROMPT = """Ты — умный AI-ассистент встроенный в Telegram бота ARESTA SOFT.
Ты помогаешь пользователям с любыми вопросами: пишешь код, объясняешь, анализируешь.
Отвечай чётко и по делу. Код всегда оформляй в блоки с указанием языка.
Отвечай на том языке на котором пишет пользователь."""

# ─── ЛОГИ ──────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ─── GROQ КЛИЕНТ ───────────────────────────────────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)

# история сообщений для каждого пользователя
user_histories = {}

def get_history(user_id):
    if user_id not in user_histories:
        user_histories[user_id] = []
    return user_histories[user_id]

def add_to_history(user_id, role, content):
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    # обрезаем если слишком длинная
    if len(history) > MAX_HISTORY:
        user_histories[user_id] = history[-MAX_HISTORY:]

def ask_groq(user_id, user_message):
    add_to_history(user_id, "user", user_message)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(user_id)
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=2048,
        temperature=0.7,
    )
    answer = response.choices[0].message.content
    add_to_history(user_id, "assistant", answer)
    return answer

# ─── КОМАНДЫ ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Привет, {user}!\n\n"
        f"Я AI-ассистент ARESTA SOFT на базе Llama 3.3.\n"
        f"Умею писать код, отвечать на вопросы и помогать с задачами.\n\n"
        f"Просто напиши мне что-нибудь!\n\n"
        f"/help — команды\n"
        f"/clear — очистить историю"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Команды:\n\n"
        "/start — приветствие\n"
        "/clear — очистить историю диалога\n"
        "/help — помощь\n\n"
        "Просто пиши сообщения — я отвечу!"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("🗑 История очищена! Начинаем заново.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # показываем что бот печатает
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        answer = ask_groq(user_id, user_message)
        # телеграм лимит 4096 символов
        if len(answer) > 4096:
            for i in range(0, len(answer), 4096):
                await update.message.reply_text(answer[i:i+4096])
        else:
            await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("⚠️ Ошибка при обращении к AI. Попробуй ещё раз.")

# ─── ЗАПУСК ────────────────────────────────────────────────────────────────────
def main():
    print("▓ ARESTA SOFT BOT запускается...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен! Нажми Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
