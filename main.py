
import os
import random
import time
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram import executor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize bot and dispatcher
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(bot)

# User data storage
users = {}

class User:
    def __init__(self):
        self.tokens = 0
        self.xp = 0
        self.level = 1
        self.last_mine = 0
        self.last_daily = 0
        self.mining_power = 1
        self.referrals = []
        self.inventory = []

def get_user(user_id):
    if user_id not in users:
        users[user_id] = User()
    return users[user_id]

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user = get_user(message.from_user.id)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("⛏ Madencilik", callback_data="mine"),
        types.InlineKeyboardButton("🎁 Günlük Ödül", callback_data="daily"),
        types.InlineKeyboardButton("🏪 Market", callback_data="store"),
        types.InlineKeyboardButton("👥 Referans", callback_data="referral"),
        types.InlineKeyboardButton("👤 Profil", callback_data="profile"),
        types.InlineKeyboardButton("📊 Sıralama", callback_data="leaderboard")
    )

    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={message.from_user.id}"
    welcome_text = (
        f"🎮 *DOGTEA MINER'A HOŞ GELDİNİZ!*\n\n"
        f"💰 Bakiye: {user.tokens} DOGTEA\n"
        f"⛏ Madenci Gücü: {user.mining_power}x\n"
        f"📊 Seviye: {user.level}\n"
        f"✨ XP: {user.xp}/{user.level * 100}\n\n"
        f"📎 Referans Linkin:\n`{ref_link}`"
    )
    
    await message.reply(
        f"🎮 Dogtea Miner'a Hoş Geldiniz!\n\n"
        f"💰 Bakiye: {user.tokens} DOGTEA\n"
        f"📊 Seviye: {user.level}\n"
        f"✨ XP: {user.xp}",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == 'mine')
async def mine_callback(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    now = time.time()
    
    if now - user.last_mine < 300:  # 5 dakika bekleme süresi
        remaining = 300 - (now - user.last_mine)
        await callback_query.answer(f"⏳ {int(remaining)} saniye beklemelisiniz!")
        return

    tokens = random.randint(5, 15)
    xp = random.randint(5, 10)
    
    user.tokens += tokens
    user.xp += xp
    user.last_mine = now
    
    # Level up kontrolü
    if user.xp >= user.level * 100:
        user.level += 1
        await bot.send_message(
            callback_query.from_user.id,
            f"🎉 Tebrikler! Seviye {user.level}'e yükseldiniz!"
        )
    
    await callback_query.answer(f"⛏ +{tokens} DOGTEA | +{xp} XP kazandınız!")

@dp.callback_query_handler(lambda c: c.data == 'daily')
async def daily_callback(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    now = time.time()
    
    if now - user.last_daily < 86400:  # 24 saat bekleme süresi
        remaining = 86400 - (now - user.last_daily)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        await callback_query.answer(f"⏳ {hours}s {minutes}d beklemelisiniz!")
        return

    tokens = random.randint(50, 100)
    user.tokens += tokens
    user.last_daily = now
    
    await callback_query.answer(f"🎁 Günlük ödül: +{tokens} DOGTEA!")

@dp.callback_query_handler(lambda c: c.data == 'profile')
async def profile_callback(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"👤 Profil Bilgileri\n\n"
        f"💰 Bakiye: {user.tokens} DOGTEA\n"
        f"📊 Seviye: {user.level}\n"
        f"✨ XP: {user.xp}/{user.level * 100}\n"
        f"⚡️ Sonraki seviye: {user.level + 1}"
    )

STORE_ITEMS = {
    "pickaxe_1": {"name": "💎 Elmas Kazma", "price": 1000, "power": 2},
    "pickaxe_2": {"name": "⚡️ Elektrikli Kazma", "price": 2500, "power": 3},
    "pickaxe_3": {"name": "🌟 Süper Kazma", "price": 5000, "power": 5}
}

@dp.callback_query_handler(lambda c: c.data == 'store')
async def store_callback(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    store_text = "🏪 *MARKET*\n\n💰 Bakiyen: " + str(user.tokens) + " DOGTEA\n\n"
    for item_id, item in STORE_ITEMS.items():
        store_text += f"{item['name']}\n💰 Fiyat: {item['power']}x güç\n\n"
        keyboard.add(types.InlineKeyboardButton(
            f"Satın Al: {item['name']}", 
            callback_data=f"buy_{item_id}"
        ))
    
    keyboard.add(types.InlineKeyboardButton("⬅️ Geri", callback_data="start"))
    
    await bot.edit_message_text(
        store_text,
        callback_query.message.chat.id,
        callback_query.message.message_id,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
async def buy_callback(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    item_id = callback_query.data.split('_')[1]
    item = STORE_ITEMS[item_id]
    
    if user.tokens >= item['price']:
        user.tokens -= item['price']
        user.mining_power = item['power']
        user.inventory.append(item_id)
        await callback_query.answer(f"✅ {item['name']} satın aldınız!")
    else:
        await callback_query.answer("❌ Yeterli DOGTEA'nız yok!")

if __name__ == '__main__':
    print('DogteaMinerBot başlatılıyor...')
    executor.start_polling(dp, skip_updates=True)
