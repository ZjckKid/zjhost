import telebot
from PIL import Image
import requests
from io import BytesIO
import os
import time
import json
import random
import string

from dotenv import load_dotenv
load_dotenv('host/.env')

# Bot helper
def get_bot_username(token):
    """Get Telegram bot username from token using getMe."""
    if not token:
        return None
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('result', {}).get('username')
    except Exception as e:
        print(f"Failed to resolve bot username from token: {e}")
        return None

# Bot configuration
BOT_TOKEN = os.getenv("SKIN_TELEGRAM_TOKEN")
BOT_USERNAME = get_bot_username(BOT_TOKEN)
bot = telebot.TeleBot(BOT_TOKEN)

# Files for storing user data
USERS_DB = "bot_data/users.json"
CODES_DB = "bot_data/codes.json"

# Create folders if they don't exist
os.makedirs("bot_data", exist_ok=True)
os.makedirs("host/skins", exist_ok=True)

def load_json(filepath):
    """Loads JSON file"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    """Saves data to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_code():
    """Generates unique 6-character code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_user_skins(user_id):
    """Gets list of users skins"""
    users = load_json(USERS_DB)
    user_id_str = str(user_id)
    if user_id_str in users:
        return users[user_id_str].get('skins', [])
    return []

def add_user_skin(user_id, skin_data):
    """Adds skin to users profile"""
    users = load_json(USERS_DB)
    user_id_str = str(user_id)

    if user_id_str not in users:
        users[user_id_str] = {
            'telegram_id': user_id,
            'username': None,
            'skins': []
        }

    users[user_id_str]['skins'].append(skin_data)
    save_json(USERS_DB, users)

# Start & Error & Success messages
WELCOME_MESSAGE_EN = (
    "🎨 Hello! I'm a bot for installing custom skins for SkinsRestorer.\n\n"
    "🎮 <b>Available commands:</b>\n"
    "/start - Show this message\n"
    "/connect - Get code to login to website\n"
    "/myskins - View your skins\n\n"
    "📤 <b>How to upload a skin:</b>\n"
    "Just send me a PNG image as a file (not as a photo!)\n\n"
    "The bot will automatically convert the image to the required format and save it to your profile.\n\n"
    "❓ If the bot stops working, message me: @zjckkid"
)

SUCCESS_MESSAGE_EN = (
    '<b>✅ Success!</b>\n\n'
    '🔗 Download link: {link}\n\n'
    '⚙️ Minecraft command:\n'
    '<code>/skin url "{link}"</code>\n\n'
    '📦 Skin saved to your profile!\n'
    '🌐 View all skins: https://host.zjck.eu/skinbot\n'
    'Use /myskins command to see your skins\n\n'
    '<span class="tg-spoiler">💡 If the skin is white - upload it to an online editor (e.g. NovaSkin), save and send to the bot again</span>'
)

ERROR_MESSAGE_EN = "❌ An error occurred: {error}\n\nMessage me: @zjckkid"

WELCOME_MESSAGE_UK = (
    "🎨 Привіт! Я бот для встановлення кастомних скінів для SkinsRestorer.\n\n"
    "🎮 <b>Доступні команди:</b>\n"
    "/start - Показати це повідомлення\n"
    "/connect - Отримати код для входу на сайт\n"
    "/myskins - Переглянути свої скіни\n\n"
    "📤 <b>Як завантажити скін:</b>\n"
    "Просто надішліть мені зображення PNG як файл (не як фото!)\n\n"
    "Бот автоматично конвертує зображення в потрібний формат та збереже його у вашому профілі.\n\n"
    "❓ Якщо бот перестав працювати, напишіть мені: @zjckkid"
)

SUCCESS_MESSAGE_UK = (
    '<b>✅ Успішно!</b>\n\n'
    '🔗 Посилання на скачування: {link}\n\n'
    '⚙️ Команда для Minecraft:\n'
    '<code>/skin url "{link}"</code>\n\n'
    '📦 Скін збережено у вашому профілі!\n'
    '🌐 Переглянути всі скіни: https://host.zjck.eu/skinbot\n'
    'Команда /myskins покаже ваші скіни\n\n'
    '<span class="tg-spoiler">💡 Якщо скін білий - завантажте його в онлайн-редактор (наприклад NovaSkin), збережіть та відправте боту знову</span>'
)

ERROR_MESSAGE_UK = "❌ Сталася помилка: {error}\n\nНапишіть мені: @zjckkid"

WELCOME_MESSAGE_RU = (
    "🎨 Привет! Я бот для установки кастомных скинов для SkinsRestorer.\n\n"
    "🎮 <b>Доступные команды:</b>\n"
    "/start - Показать это сообщение\n"
    "/connect - Получить код для входа на сайт\n"
    "/myskins - Посмотреть свои скины\n\n"
    "📤 <b>Как загрузить скин:</b>\n"
    "Просто отправьте мне изображение PNG как файл (не как фото!)\n\n"
    "Бот автоматически конвертирует изображение в нужный формат и сохранит его в вашем профиле.\n\n"
    "❓ Если бот перестал работать, напишите мне: @zjckkid"
)

SUCCESS_MESSAGE_RU = (
    '<b>✅ Успешно!</b>\n\n'
    '🔗 Ссылка на скачивание: {link}\n\n'
    '⚙️ Команда для Minecraft:\n'
    '<code>/skin url "{link}"</code>\n\n'
    '📦 Скин сохранён в вашем профиле!\n'
    '🌐 Посмотреть все скины: https://host.zjck.eu/skinbot\n'
    'Команда /myskins покажет ваши скины\n\n'
    '<span class="tg-spoiler">💡 Если скин белый - загрузите его в онлайн-редактор (например NovaSkin), сохраните и отправьте боту снова</span>'
)

ERROR_MESSAGE_RU = "❌ Произошла ошибка: {error}\n\nНапишите мне: @zjckkid"

def process_skin(image: BytesIO):
    """Process skin image"""
    try:
        img = Image.open(image)

        if img.format not in ["PNG"]:
            raise ValueError("Image format not supported. Use PNG.")


        if img.size[0] > 128 or img.size[1] > 128:
            raise ValueError("Maximum resolution is 128x128 pixels.")


        if img.size != (64, 64):
            img = img.resize((64, 64), Image.Resampling.LANCZOS)

        img = img.convert("RGBA")
        data = img.load()
        width, height = img.size
        for y in range(height):
            for x in range(width):
                if data[x, y][:3] == (255, 255, 255):
                    data[x, y] = (255, 255, 255, 0)

        output = BytesIO()
        img.save(output, format="PNG")
        output.seek(0)
        return output

    except Exception as e:
        print(f"Ошибка бота скинов: {e}")
        raise ValueError(f"Image processing error: {str(e)}")

def save_skin_file(image: BytesIO, user_id: int) -> tuple:
    """Saves skin file and returns (link, filename)"""
    try:
        filename = f"skin_{user_id}_{int(time.time())}.png"
        save_path = os.path.join("host", "skins", filename)  # CHANGED: saving to host/skins/
        image.seek(0)
        with open(save_path, "wb") as f:
            f.write(image.read())
        link = f"https://host.zjck.eu/download/skin/{filename}"  # CHANGED: new URL
        return link, filename
    except Exception as e:
        print(f"Ошибка бота скинов: {e}")
        raise ValueError(f"File save error: {str(e)}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_language = message.from_user.language_code
    if user_language == 'uk':
        bot.reply_to(message, WELCOME_MESSAGE_UK, parse_mode="HTML")
    elif user_language == 'ru':
        bot.reply_to(message, WELCOME_MESSAGE_RU, parse_mode="HTML")
    else:
        bot.reply_to(message, WELCOME_MESSAGE_EN, parse_mode="HTML")


@bot.message_handler(commands=['connect'])
def connect_command(message):
    """Generates code for website login"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"

        # Generate code
        code = generate_code()
        codes = load_json(CODES_DB)

        # Save code with 10 minute expiration
        codes[code] = {
            'telegram_id': user_id,
            'username': username,
            'timestamp': time.time(),
            'used': False
        }
        save_json(CODES_DB, codes)

        # Update user information
        users = load_json(USERS_DB)
        user_id_str = str(user_id)
        if user_id_str not in users:
            users[user_id_str] = {
                'telegram_id': user_id,
                'username': username,
                'skins': []
            }
        else:
            users[user_id_str]['username'] = username
        save_json(USERS_DB, users)

        user_language = message.from_user.language_code
        if user_language == 'uk':
            response = (
                f"🔐 <b>Код для входу на сайт:</b>\n\n"
                f"<code>{code}</code>\n\n"
                f"⏱ Код дійсний протягом 10 хвилин.\n"
                f"📱 Введіть цей код на сторінці входу:\n"
                f"https://host.zjck.eu/skinbot/login"
            )
        elif user_language == 'ru':
            response = (
                f"🔐 <b>Код для входа на сайт:</b>\n\n"
                f"<code>{code}</code>\n\n"
                f"⏱ Код действителен в течение 10 минут.\n"
                f"📱 Введите этот код на странице входа:\n"
                f"https://host.zjck.eu/skinbot/login"
            )
        else:
            response = (
                f"🔐 <b>Login code for website:</b>\n\n"
                f"<code>{code}</code>\n\n"
                f"⏱ Code is valid for 10 minutes.\n"
                f"📱 Enter this code on the login page:\n"
                f"https://host.zjck.eu/skinbot/login"
            )

        bot.reply_to(message, response, parse_mode="HTML")

    except Exception as e:
        print(f"Ошибка бота скинов: {e}")
        bot.reply_to(message, ERROR_MESSAGE_EN.format(error=str(e)), parse_mode="HTML")

@bot.message_handler(commands=['myskins'])
def my_skins_command(message):
    """Shows list of users skins"""
    try:
        user_language = message.from_user.language_code
        if user_language == 'uk':
            user_id = message.from_user.id
            skins = get_user_skins(user_id)

            if not skins:
                bot.reply_to(message, "📭 У вас ще немає збережених скінів.\n\nНадішліть мені PNG файл зі скіном!", parse_mode="HTML")
                return

            response = f"🎨 <b>Ваші скіни ({len(skins)}):</b>\n\n"
            for i, skin in enumerate(skins[-10:], 1):  # Показуємо останні 10
                response += f"{i}. {skin['filename']}\n"
                response += f"   🔗 <a href='{skin['link']}'>Завантажити</a>\n"
                response += f"   📅 {skin['upload_date']}\n\n"

            response += "💻 Переглянути всі скіни та управляти ними:\nhttps://host.zjck.eu/skinbot"
            bot.reply_to(message, response, parse_mode="HTML", disable_web_page_preview=True)
        elif user_language == 'ru':
            user_id = message.from_user.id
            skins = get_user_skins(user_id)

            if not skins:
                bot.reply_to(message, "📭 У вас ещё нет сохранённых скинов.\n\nОтправьте мне PNG файл со скином!", parse_mode="HTML")
                return

            response = f"🎨 <b>Ваши скины ({len(skins)}):</b>\n\n"
            for i, skin in enumerate(skins[-10:], 1):  # Показываем последние 10
                response += f"{i}. {skin['filename']}\n"
                response += f"   🔗 <a href='{skin['link']}'>Скачать</a>\n"
                response += f"   📅 {skin['upload_date']}\n\n"

            response += "💻 Посмотреть все скины и управлять ими:\nhttps://host.zjck.eu/skinbot"
            bot.reply_to(message, response, parse_mode="HTML", disable_web_page_preview=True)
        else:
            user_id = message.from_user.id
            skins = get_user_skins(user_id)

            if not skins:
                bot.reply_to(message, "📭 You don't have any saved skins yet.\n\nSend me a PNG file with a skin!", parse_mode="HTML")
                return

            response = f"🎨 <b>Your skins ({len(skins)}):</b>\n\n"
            for i, skin in enumerate(skins[-10:], 1):  # Show last 10
                response += f"{i}. {skin['filename']}\n"
                response += f"   🔗 <a href='{skin['link']}'>Download</a>\n"
                response += f"   📅 {skin['upload_date']}\n\n"

            response += "💻 View all skins and manage them:\nhttps://host.zjck.eu/skinbot"
            bot.reply_to(message, response, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        print(f"Ошибка бота скинов: {e}")
        bot.reply_to(message, ERROR_MESSAGE_EN.format(error=str(e)), parse_mode="HTML")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        user_language = message.from_user.language_code
        if user_language == 'uk':
            if not message.document.mime_type.startswith('image/'):
                bot.reply_to(message, "⚠️ Надішліть зображення у форматі PNG.", parse_mode="HTML")
                return

            # Відправляємо повідомлення про обробку
            processing_msg = bot.reply_to(message, "⏳ Обробляю скін...", parse_mode="HTML")

            file_info = bot.get_file(message.document.file_id)
            file = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}")

            processed_image = process_skin(BytesIO(file.content))
            skin_link, filename = save_skin_file(processed_image, message.from_user.id)

            # Зберігаємо інформацію про скін
            skin_data = {
                'filename': filename,
                'link': skin_link,
                'upload_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': time.time()
            }
            add_user_skin(message.from_user.id, skin_data)

            # Оновлюємо повідомлення
            bot.edit_message_text(
                SUCCESS_MESSAGE_UK.format(link=skin_link),
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                parse_mode="HTML"
            )

            # Відправляємо превю скіна
            try:
                with open(os.path.join("host", "skins", filename), "rb") as skin_file:
                    bot.send_photo(
                        message.chat.id,
                        skin_file,
                        caption=f"🎨 Ваш скін готовий!\n\n📎 {filename}"
                    )
            except:
                pass
        elif user_language == 'ru':
            if not message.document.mime_type.startswith('image/'):
                bot.reply_to(message, "⚠️ Отправьте изображение в формате PNG.", parse_mode="HTML")
                return

            # Отправляем сообщение об обработке
            processing_msg = bot.reply_to(message, "⏳ Обрабатываю скин...", parse_mode="HTML")

            file_info = bot.get_file(message.document.file_id)
            file = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}")

            processed_image = process_skin(BytesIO(file.content))
            skin_link, filename = save_skin_file(processed_image, message.from_user.id)

            # Сохраняем информацию о скине
            skin_data = {
                'filename': filename,
                'link': skin_link,
                'upload_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': time.time()
            }
            add_user_skin(message.from_user.id, skin_data)

            # Обновляем сообщение
            bot.edit_message_text(
                SUCCESS_MESSAGE_RU.format(link=skin_link),
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                parse_mode="HTML"
            )

            # Отправляем превью скина
            try:
                with open(os.path.join("host", "skins", filename), "rb") as skin_file:
                    bot.send_photo(
                        message.chat.id,
                        skin_file,
                        caption=f"🎨 Ваш скин готов!\n\n📎 {filename}"
                    )
            except:
                pass
        else:
            if not message.document.mime_type.startswith('image/'):
                bot.reply_to(message, "⚠️ Send an image in PNG format.", parse_mode="HTML")
                return

            # Send processing message
            processing_msg = bot.reply_to(message, "⏳ Processing skin...", parse_mode="HTML")

            file_info = bot.get_file(message.document.file_id)
            file = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}")

            processed_image = process_skin(BytesIO(file.content))
            skin_link, filename = save_skin_file(processed_image, message.from_user.id)

            # Save skin information
            skin_data = {
                'filename': filename,
                'link': skin_link,
                'upload_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': time.time()
            }
            add_user_skin(message.from_user.id, skin_data)

            # Update message
            bot.edit_message_text(
                SUCCESS_MESSAGE_EN.format(link=skin_link),
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                parse_mode="HTML"
            )

            # Send skin preview
            try:
                with open(os.path.join("host", "skins", filename), "rb") as skin_file:
                    bot.send_photo(
                        message.chat.id,
                        skin_file,
                        caption=f"🎨 Your skin is ready!\n\n📎 {filename}"
                    )
            except:
                pass


    except Exception as e:
        print(f"Ошибка бота скинов: {e}")
        bot.reply_to(message, ERROR_MESSAGE_EN.format(error=str(e)), parse_mode="HTML")

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    try:
        user_language = message.from_user.language_code
        if user_language == 'uk':
            bot.reply_to(message,
                        "⚠️ <b>Будь ласка, надішліть зображення як файл-документ, а не як фото.</b>\n\n"
                        "📌 Це важливо для збереження якості скіна!\n\n"
                        "Дивіться інструкції нижче:",
                        parse_mode="HTML")

            try:
                with open("photos/pc_tutor.png", "rb") as pc_tutor:
                    bot.send_photo(message.chat.id, pc_tutor,
                                caption="💻 <b>Туторіал для ПК</b>\n\nНатисніть на скріпку (📎) → Файл",
                                parse_mode="HTML")
            except:
                pass

            try:
                with open("photos/android_tutor.png", "rb") as android_tutor:
                    bot.send_photo(message.chat.id, android_tutor,
                                caption="📱 <b>Туторіал для телефонів</b>\n\nВиберіть 'Файл' замість 'Галерея'",
                                parse_mode="HTML")
            except:
                pass
        elif user_language == 'ru':
            bot.reply_to(message,
                        "⚠️ <b>Пожалуйста, отправьте изображение как файл-документ, а не как фото.</b>\n\n"
                        "📌 Это важно для сохранения качества скина!\n\n"
                        "Смотрите инструкции ниже:",
                        parse_mode="HTML")

            try:
                with open("photos/pc_tutor.png", "rb") as pc_tutor:
                    bot.send_photo(message.chat.id, pc_tutor,
                                caption="💻 <b>Туториал для ПК</b>\n\nНажмите на скрепку (📎) → Файл",
                                parse_mode="HTML")
            except:
                pass

            try:
                with open("photos/android_tutor.png", "rb") as android_tutor:
                    bot.send_photo(message.chat.id, android_tutor,
                                caption="📱 <b>Туториал для телефонов</b>\n\nВыберите 'Файл' вместо 'Галерея'",
                                parse_mode="HTML")
            except:
                pass
        else:
            bot.reply_to(message,
                        "⚠️ <b>Please send the image as a file-document, not as a photo.</b>\n\n"
                        "📌 This is important to preserve skin quality!\n\n"
                        "See instructions below:",
                        parse_mode="HTML")

            try:
                with open("photos/pc_tutor.png", "rb") as pc_tutor:
                    bot.send_photo(message.chat.id, pc_tutor,
                                caption="💻 <b>Tutorial for PC</b>\n\nClick on the paperclip (📎) → File",
                                parse_mode="HTML")
            except:
                pass

            try:
                with open("photos/android_tutor.png", "rb") as android_tutor:
                    bot.send_photo(message.chat.id, android_tutor,
                                caption="📱 <b>Tutorial for mobile</b>\n\nSelect 'File' instead of 'Gallery'",
                                parse_mode="HTML")
            except:
                pass
    except Exception as e:
        print(f"Ошибка бота скинов: {e}")
        bot.reply_to(message, ERROR_MESSAGE_EN.format(error=str(e)), parse_mode="HTML")

if __name__ == "__main__":
    print("SKIN bot started")
    print(f"Download URL: https://host.zjck.eu/download/skin/")

    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
    except Exception as e:
        print(f"\n\nError: {str(e)}")
