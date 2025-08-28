import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from dotenv import load_dotenv
from database import add_command, get_panels, get_commands
from flask import Flask, request

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000))
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

app = Flask(__name__)

# ------------------ /start ------------------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Komanda qo‘shish", callback_data="add_command"))
    await message.answer("Assalomu alaykum! Panelni tanlang:", reply_markup=markup)

# ------------------ Komanda qo‘shish ------------------
@dp.callback_query_handler(lambda c: c.data == "add_command")
async def add_command_callback(callback_query: types.CallbackQuery):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("User Panel", callback_data="panel_user"))
    markup.add(InlineKeyboardButton("Admin Panel", callback_data="panel_admin"))
    await bot.send_message(callback_query.from_user.id, "Qaysi panelga qo‘shmoqchisiz?", reply_markup=markup)

# ------------------ Panel tanlash ------------------
@dp.callback_query_handler(lambda c: c.data.startswith("panel_"))
async def panel_selected(callback_query: types.CallbackQuery):
    panel = "User Panel" if callback_query.data == "panel_user" else "Admin Panel"
    sub_panels = get_panels(panel)
    markup = InlineKeyboardMarkup()
    for sp in sub_panels:
        markup.add(InlineKeyboardButton(sp, callback_data=f"sub_{sp}"))
    await bot.send_message(callback_query.from_user.id, f"{panel} ichidagi panelni tanlang:", reply_markup=markup)

# ------------------ Sub-panel tanlash ------------------
@dp.callback_query_handler(lambda c: c.data.startswith("sub_"))
async def sub_panel_selected(callback_query: types.CallbackQuery):
    sub_panel = callback_query.data.replace("sub_", "")
    await bot.send_message(callback_query.from_user.id, f"{sub_panel} panelga qo‘shmoqchi bo‘lgan komandani nomini kiriting:")

    # Keyingi хабар үшін listener
    @dp.message_handler()
    async def get_command_name(message: types.Message):
        command_name = message.text
        await bot.send_message(message.from_user.id, "Bu komanda nima qilishi kerakligini yozing:")

        @dp.message_handler()
        async def get_command_description(desc_msg: types.Message):
            description = desc_msg.text
            panel = "User Panel" if "User Panel" in callback_query.message.text else "Admin Panel"
            await add_command(panel, sub_panel, command_name, description)
            await bot.send_message(desc_msg.from_user.id, f"Komanda '{command_name}' {panel}/{sub_panel} ga muvaffaqiyatli qo‘shildi!")

# ------------------ Dynamic commands display ------------------
@dp.message_handler(commands=["panel"])
async def show_panel(message: types.Message):
    panels = ["User Panel", "Admin Panel"]
    markup = InlineKeyboardMarkup()
    for p in panels:
        markup.add(InlineKeyboardButton(p, callback_data=f"show_{p.replace(' ','_')}"))
    await message.answer("Panelni tanlang:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("show_"))
async def display_commands(callback_query: types.CallbackQuery):
    panel = callback_query.data.replace("show_", "").replace("_", " ")
    commands = get_commands(panel)
    text = f"{panel} komandalar:\n"
    for cmd in commands:
        text += f"- {cmd['command_name']}: {cmd['description']}\n"
    await bot.send_message(callback_query.from_user.id, text)

# ------------------ Flask webhook route ------------------
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = types.Update.de_json(request.get_data().decode("utf-8"))
    asyncio.run(dp.process_update(update))
    return "OK", 200

# ------------------ Run Flask ------------------
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    app.run(host="0.0.0.0", port=PORT)
