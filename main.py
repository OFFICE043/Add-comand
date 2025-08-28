import os
import asyncio
import threading
import time
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from database import add_command, get_panels, get_commands
from flask import Flask, request

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000))
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

# Aiogram bot & dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Flask app
app = Flask(__name__)

# ------------------ Keep-alive ------------------
def keep_alive(url: str, interval: int = 300):
    def _ping():
        while True:
            try:
                requests.get(url)
            except Exception as e:
                print("Keep-alive ping error:", e)
            time.sleep(interval)
    thread = threading.Thread(target=_ping, daemon=True)
    thread.start()

# ------------------ /start ------------------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = InlineKeyboardBuilder()
    markup.row(InlineKeyboardButton(text="Komanda qo‘shish", callback_data="add_command"))
    await message.answer("Assalomu alaykum! Panelni tanlang:", reply_markup=markup.as_markup())

# ------------------ Komanda qo‘shish ------------------
@dp.callback_query(lambda c: c.data == "add_command")
async def add_command_callback(callback: types.CallbackQuery):
    markup = InlineKeyboardBuilder()
    markup.row(InlineKeyboardButton(text="User Panel", callback_data="panel_user"))
    markup.row(InlineKeyboardButton(text="Admin Panel", callback_data="panel_admin"))
    await callback.message.answer("Qaysi panelga qo‘shmoqchisiz?", reply_markup=markup.as_markup())

# ------------------ Panel tanlash ------------------
@dp.callback_query(lambda c: c.data.startswith("panel_"))
async def panel_selected(callback: types.CallbackQuery):
    panel = "User Panel" if callback.data == "panel_user" else "Admin Panel"
    sub_panels = get_panels(panel)
    markup = InlineKeyboardBuilder()
    for sp in sub_panels:
        markup.row(InlineKeyboardButton(text=sp, callback_data=f"sub_{sp}"))
    await callback.message.answer(f"{panel} ichidagi panelni tanlang:", reply_markup=markup.as_markup())

# ------------------ Sub-panel tanlash ------------------
@dp.callback_query(lambda c: c.data.startswith("sub_"))
async def sub_panel_selected(callback: types.CallbackQuery):
    sub_panel = callback.data.replace("sub_", "")
    await callback.message.answer(f"{sub_panel} panelga qo‘shmoqchi bo‘lgan komandani nomini kiriting:")

    # Keyingi xabarni kutamiz
    @dp.message()
    async def get_command_name(message: types.Message):
        command_name = message.text
        await message.answer("Bu komanda nima qilishi kerakligini yozing:")

        @dp.message()
        async def get_command_description(desc_msg: types.Message):
            description = desc_msg.text
            panel = "User Panel" if "User Panel" in callback.message.text else "Admin Panel"
            await add_command(panel, sub_panel, command_name, description)
            await desc_msg.answer(f"Komanda '{command_name}' {panel}/{sub_panel} ga muvaffaqiyatli qo‘shildi!")

# ------------------ Dynamic commands display ------------------
@dp.message(Command("panel"))
async def show_panel(message: types.Message):
    panels = ["User Panel", "Admin Panel"]
    markup = InlineKeyboardBuilder()
    for p in panels:
        markup.row(InlineKeyboardButton(text=p, callback_data=f"show_{p.replace(' ','_')}"))
    await message.answer("Panelni tanlang:", reply_markup=markup.as_markup())

@dp.callback_query(lambda c: c.data.startswith("show_"))
async def display_commands(callback: types.CallbackQuery):
    panel = callback.data.replace("show_", "").replace("_", " ")
    commands = get_commands(panel)
    text = f"{panel} komandalar:\n"
    for cmd in commands:
        text += f"- {cmd['command_name']}: {cmd['description']}\n"
    await callback.message.answer(text)

# ------------------ Flask webhook route ------------------
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    data = request.get_json()
    asyncio.create_task(dp.feed_update(data))
    return "OK", 200

# ------------------ Run Flask ------------------
if __name__ == "__main__":
    keep_alive(WEBHOOK_URL)
    import logging
    logging.basicConfig(level=logging.INFO)
    dp.startup.register(lambda _: bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH))
    app.run(host="0.0.0.0", port=PORT)
