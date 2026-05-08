import os
from datetime import datetime
from flask import Flask, send_from_directory, render_template, abort, request, send_file, redirect, url_for, flash, session, jsonify, Response, render_template_string
from werkzeug.utils import secure_filename, safe_join
from werkzeug.security import check_password_hash, generate_password_hash
from pdf2image import convert_from_bytes
import io
import logging
from urllib.parse import unquote
import mimetypes
import chardet
import pygments
from pygments import lexers, formatters
from pygments.util import ClassNotFound
import requests
from urllib.parse import urlparse
import shutil
import json
import time
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import string
import qrcode
from io import BytesIO
from PIL import Image
from functools import wraps
from datetime import timedelta

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

from module_loader import ModuleLoader
module_loader = ModuleLoader(app)
module_loader.load_all()

# Налаштування
app.config['FILES_FOLDER'] = os.path.abspath('host/files')
app.config['SKINS_FOLDER'] = os.path.abspath('host/skins')
app.config['PRIVATE_FILES_FOLDER'] = os.path.abspath('host/privatefiles')
app.config['PHOTOS_FOLDER'] = os.path.abspath('photos')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Налаштування сесії
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

PRIVATE_FILES_DB = "bot_data/private_files.json"
ADMIN_CODES_DB = "bot_data/admin_codes.json"
USERS_DB = "bot_data/users.json"
CODES_DB = "bot_data/codes.json"
DOWNLOADS_LOG = "bot_data/downloads.json"

# Створення папок якщо не існують
os.makedirs(app.config['FILES_FOLDER'], exist_ok=True)
os.makedirs(app.config['SKINS_FOLDER'], exist_ok=True)  # NEW
os.makedirs(app.config['PRIVATE_FILES_FOLDER'], exist_ok=True)
os.makedirs("bot_data", exist_ok=True)

# Налаштування MIME типів
mimetypes.init()

@app.route('/photo/<path:filename>')
def photo(filename):
    try:
        path = safe_join(app.config['PHOTOS_FOLDER'], filename)
        if not os.path.exists(path):
            abort(404)
        return send_from_directory(app.config['PHOTOS_FOLDER'], filename)
    except Exception:
        abort(404)

mimetypes.add_type('text/markdown', '.md')
mimetypes.add_type('text/x-python', '.py')
mimetypes.add_type('text/x-java', '.java')
mimetypes.add_type('text/x-c++', '.cpp')
mimetypes.add_type('text/x-c', '.c')
mimetypes.add_type('text/x-javascript', '.js')
mimetypes.add_type('text/x-html', '.html')
mimetypes.add_type('text/x-css', '.css')
mimetypes.add_type('text/x-php', '.php')
mimetypes.add_type('text/x-ruby', '.rb')
mimetypes.add_type('text/x-shellscript', '.sh')
mimetypes.add_type('text/x-sql', '.sql')
mimetypes.add_type('text/x-xml', '.xml')
mimetypes.add_type('text/x-yaml', '.yml')
mimetypes.add_type('text/x-yaml', '.yaml')
mimetypes.add_type('text/x-json', '.json')
mimetypes.add_type('video/x-matroska', '.mkv')
mimetypes.add_type('video/mp4', '.mp4')
mimetypes.add_type('video/x-msvideo', '.avi')
mimetypes.add_type('video/quicktime', '.mov')
mimetypes.add_type('video/webm', '.webm')

def is_archive_file(file_path):
    """Перевіряє чи є файл архівом"""
    ext = os.path.splitext(file_path)[1].lower()
    archive_exts = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.tar.gz', '.tar.bz2']
    return ext in archive_exts

def generate_file_password():
    """Генерує випадковий пароль для файлу"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

def load_json(filepath):
    """Завантажує JSON файл"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    """Зберігає дані в JSON файл"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_download(filename, file_type='regular', user_ip=None):
    """Логує завантаження файлу"""
    try:
        logs = load_json(DOWNLOADS_LOG)
        if filename not in logs:
            logs[filename] = {
                'count': 0,
                'first_download': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': file_type
            }
        logs[filename]['count'] += 1
        logs[filename]['last_download'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if user_ip:
            if 'ips' not in logs[filename]:
                logs[filename]['ips'] = []
            if user_ip not in logs[filename]['ips']:
                logs[filename]['ips'].append(user_ip)
        save_json(DOWNLOADS_LOG, logs)
    except Exception as e:
        app.logger.error(f"Error logging download: {str(e)}")

def get_disk_usage():
    """Отримує використання диску"""
    try:
        total, used, free = shutil.disk_usage("/")
        return {
            'total': total,
            'used': used,
            'free': free,
            'percent': (used / total) * 100
        }
    except:
        return None


def get_file_icon(file_type):
    """Повертає іконку для типу файлу"""
    icons = {
        'pdf': 'fa-file-pdf',
        'doc': 'fa-file-word',
        'docx': 'fa-file-word',
        'xls': 'fa-file-excel',
        'xlsx': 'fa-file-excel',
        'ppt': 'fa-file-powerpoint',
        'pptx': 'fa-file-powerpoint',
        'zip': 'fa-file-archive',
        'rar': 'fa-file-archive',
        '7z': 'fa-file-archive',
        'tar': 'fa-file-archive',
        'gz': 'fa-file-archive',
        'jpg': 'fa-file-image',
        'jpeg': 'fa-file-image',
        'png': 'fa-file-image',
        'gif': 'fa-file-image',
        'bmp': 'fa-file-image',
        'svg': 'fa-file-image',
        'webp': 'fa-file-image',
        'mp3': 'fa-file-audio',
        'wav': 'fa-file-audio',
        'ogg': 'fa-file-audio',
        'flac': 'fa-file-audio',
        'mp4': 'fa-file-video',
        'avi': 'fa-file-video',
        'mov': 'fa-file-video',
        'wmv': 'fa-file-video',
        'mkv': 'fa-file-video',
        'webm': 'fa-file-video',
        'py': 'fa-file-code',
        'js': 'fa-file-code',
        'html': 'fa-file-code',
        'css': 'fa-file-code',
        'php': 'fa-file-code',
        'java': 'fa-file-code',
        'cpp': 'fa-file-code',
        'c': 'fa-file-code',
        'rb': 'fa-file-code',
        'sh': 'fa-file-code',
        'sql': 'fa-file-code',
        'xml': 'fa-file-code',
        'yml': 'fa-file-code',
        'yaml': 'fa-file-code',
        'json': 'fa-file-code',
        'txt': 'fa-file-alt',
        'md': 'fa-file-alt',
        'log': 'fa-file-alt',
    }
    return icons.get(file_type.lower(), 'fa-file')

def get_file_color(file_type):
    """Повертає колір для типу файлу"""
    colors = {
        'pdf': 'text-red-500',
        'doc': 'text-blue-500',
        'docx': 'text-blue-500',
        'xls': 'text-green-500',
        'xlsx': 'text-green-500',
        'ppt': 'text-orange-500',
        'pptx': 'text-orange-500',
        'zip': 'text-purple-500',
        'rar': 'text-purple-500',
        '7z': 'text-purple-500',
        'tar': 'text-purple-500',
        'gz': 'text-purple-500',
        'jpg': 'text-blue-500',
        'jpeg': 'text-blue-500',
        'png': 'text-blue-500',
        'gif': 'text-blue-500',
        'bmp': 'text-blue-500',
        'svg': 'text-blue-500',
        'webp': 'text-blue-500',
        'mp3': 'text-yellow-500',
        'wav': 'text-yellow-500',
        'ogg': 'text-yellow-500',
        'flac': 'text-yellow-500',
        'mp4': 'text-pink-500',
        'avi': 'text-pink-500',
        'mov': 'text-pink-500',
        'wmv': 'text-pink-500',
        'mkv': 'text-pink-500',
        'webm': 'text-pink-500',
        'py': 'text-green-500',
        'js': 'text-yellow-500',
        'html': 'text-orange-500',
        'css': 'text-blue-500',
        'php': 'text-purple-500',
        'java': 'text-red-500',
        'cpp': 'text-blue-500',
        'c': 'text-blue-500',
        'rb': 'text-red-500',
        'sh': 'text-green-500',
        'sql': 'text-blue-500',
        'xml': 'text-orange-500',
        'yml': 'text-purple-500',
        'yaml': 'text-purple-500',
        'json': 'text-yellow-500',
        'txt': 'text-gray-500',
        'md': 'text-gray-500',
        'log': 'text-gray-500',
    }
    return colors.get(file_type.lower(), 'text-gray-500')

def format_file_size(size):
    """Форматує розмір файлу"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def detect_encoding(file_path):
    """Визначає кодування файлу"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(4096)
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        if encoding and encoding.lower() not in ['ascii', 'unknown']:
            return encoding
        try:
            with open(file_path, 'r', encoding='utf-8') as test:
                test.read()
            return 'utf-8'
        except:
            pass
        try:
            with open(file_path, 'r', encoding='windows-1251') as test:
                test.read()
            return 'windows-1251'
        except:
            pass
        return 'latin1'

def get_lexer_for_filename(filename):
    """Визначає лексер для підсвічування синтаксису"""
    try:
        return lexers.get_lexer_for_filename(filename)
    except ClassNotFound:
        return lexers.get_lexer_by_name('text')

def is_text_file(file_path):
    """Перевіряє, чи є файл текстовим"""
    # Якщо це архів - не текстовий
    if is_archive_file(file_path):
        return False
        
    mime, _ = mimetypes.guess_type(file_path)
    if mime and mime.startswith('text'):
        return True
    ext = os.path.splitext(file_path)[1].lower()
    text_exts = ['.txt', '.md', '.log', '.py', '.js', '.html', '.css', '.php', '.java', '.cpp', '.c', '.rb', '.sh', '.sql', '.xml', '.yml', '.yaml', '.json']
    if ext in text_exts:
        return True
    try:
        with open(file_path, 'rb') as f:
            raw = f.read(2048)
            result = chardet.detect(raw)
            if result['encoding']:
                return True
    except:
        pass
    return False

def is_video_file(file_path):
    """Перевіряє чи є файл відео"""
    mime, _ = mimetypes.guess_type(file_path)
    if mime and mime.startswith('video'):
        return True
    ext = os.path.splitext(file_path)[1].lower()
    video_exts = ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.webm', '.flv', '.m4v']
    return ext in video_exts

def is_image_file(file_path):
    """Перевіряє чи є файл зображенням"""
    ext = os.path.splitext(file_path)[1].lower()
    image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
    return ext in image_exts

def is_audio_file(file_path):
    """Перевіряє чи є файл аудіо"""
    ext = os.path.splitext(file_path)[1].lower()
    audio_exts = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac']
    return ext in audio_exts

def get_file_info(filename, folder='files'):
    """Отримання інформації про файл"""
    try:
        decoded_name = unquote(filename)
        if folder == 'skins':
            raw_path = safe_join(app.config['SKINS_FOLDER'], decoded_name)
        else:
            raw_path = safe_join(app.config['FILES_FOLDER'], decoded_name)
            
        if not os.path.isfile(raw_path):
            return None
        safe_name = secure_filename(decoded_name)
        file_type = safe_name.split('.')[-1].lower() if '.' in safe_name else 'unknown'
        mime_type, _ = mimetypes.guess_type(safe_name)
        
        # Підрахунок рядків тільки для текстових файлів (не відео, не зображення, не аудіо, не архіви)
        line_count = 0
        if is_text_file(raw_path) and not is_video_file(raw_path) and not is_image_file(raw_path) and not is_audio_file(raw_path) and not is_archive_file(raw_path):
            try:
                with open(raw_path, 'r', encoding=detect_encoding(raw_path)) as f:
                    line_count = sum(1 for _ in f)
            except:
                line_count = 0
        
        # Отримуємо статистику завантажень
        downloads_log = load_json(DOWNLOADS_LOG)
        download_count = downloads_log.get(decoded_name, {}).get('count', 0)
        
        return {
            'original_name': decoded_name,
            'safe_name': safe_name,
            'size': os.path.getsize(raw_path),
            'formatted_size': format_file_size(os.path.getsize(raw_path)),
            'type': file_type,
            'mime_type': mime_type or 'application/octet-stream',
            'path': raw_path,
            'upload_date': datetime.fromtimestamp(os.path.getctime(raw_path)).strftime('%Y-%m-%d %H:%M:%S'),
            'icon': get_file_icon(file_type),
            'color': get_file_color(file_type),
            'line_count': line_count,
            'is_text': is_text_file(raw_path),
            'is_video': is_video_file(raw_path),
            'is_archive': is_archive_file(raw_path),
            'download_count': download_count,
            'folder': folder
        }
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
        return None

def get_file_preview(file_info):
    """Отримання попереднього перегляду файлу"""
    try:
        # Архіви
        if file_info['is_archive']:
            return {
                'type': 'archive',
                'content': None
            }
        
        # Відео файли
        if file_info['is_video']:
            return {
                'type': 'video',
                'content': None
            }
        
        # Текстові файли
        if file_info['is_text']:
            encoding = detect_encoding(file_info['path'])
            with open(file_info['path'], 'r', encoding=encoding, errors='replace') as f:
                content = f.read(2048)
                try:
                    lexer = get_lexer_for_filename(file_info['original_name'])
                    formatter = formatters.HtmlFormatter(style='monokai')
                    highlighted = pygments.highlight(content, lexer, formatter)
                    return {
                        'type': 'code',
                        'content': highlighted,
                        'style': formatter.get_style_defs('.highlight')
                    }
                except:
                    return {
                        'type': 'text',
                        'content': content
                    }
        elif file_info['type'] == 'pdf':
            return {
                'type': 'pdf',
                'content': None
            }
        elif file_info['type'] in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']:
            return {
                'type': 'image',
                'content': None
            }
        else:
            return {
                'type': 'unknown',
                'content': None
            }
    except Exception as e:
        print(f"Error generating preview for {file_info['original_name']}: {str(e)}")
        return {
            'type': 'error',
            'content': str(e)
        }

def get_paginated_files(page, per_page=12, search_query='', sort_by='date', sort_order='desc', file_type=''):
    """Отримання файлів для пагінації (БЕЗ скінів)"""
    try:
        files_dir = app.config['FILES_FOLDER']
        all_files = []
        for f in os.listdir(files_dir):
            try:
                full_path = safe_join(files_dir, f)
                if os.path.isfile(full_path) and not f.startswith('.'):
                    decoded_name = unquote(f)
                    file_info = get_file_info(decoded_name, 'files')
                    if file_info:
                        all_files.append(file_info)
            except Exception as e:
                app.logger.error(f"Помилка обробки файлу {f}: {str(e)}")
        
        if search_query:
            all_files = [f for f in all_files if search_query.lower() in f['original_name'].lower()]
        
        if file_type:
            all_files = [f for f in all_files if f['type'].lower() == file_type.lower()]
        
        if sort_by == 'name':
            all_files.sort(key=lambda x: x['original_name'].lower(), reverse=(sort_order == 'desc'))
        elif sort_by == 'size':
            all_files.sort(key=lambda x: x['size'], reverse=(sort_order == 'desc'))
        elif sort_by == 'type':
            all_files.sort(key=lambda x: x['type'].lower(), reverse=(sort_order == 'desc'))
        else:
            all_files.sort(key=lambda x: x['upload_date'], reverse=(sort_order == 'desc'))
        
        total = len(all_files)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        file_types = list(set(f['type'] for f in all_files))
        file_types.sort()
        
        return {
            'files': all_files[start_idx:end_idx],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'file_types': file_types
        }
    except Exception as e:
        app.logger.error(f"Pagination error: {str(e)}")
        return {'files': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0, 'file_types': []}


def download_file_from_url(url, filename=None):
    """Скачує файл по URL"""
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, "Некоректний URL"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        if not filename:
            content_disposition = response.headers.get('content-disposition')
            if content_disposition and 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            else:
                filename = os.path.basename(parsed.path) or 'downloaded_file'
        
        safe_filename = secure_filename(filename)
        if not safe_filename:
            safe_filename = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > app.config['MAX_CONTENT_LENGTH']:
            return False, f"Файл занадто великий (максимум {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)} MB)"
        
        file_path = os.path.join(app.config['FILES_FOLDER'], safe_filename)
        
        counter = 1
        original_filename = safe_filename
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_filename)
            safe_filename = f"{name}_{counter}{ext}"
            file_path = os.path.join(app.config['FILES_FOLDER'], safe_filename)
            counter += 1
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True, safe_filename
        
    except requests.RequestException as e:
        return False, f"Помилка завантаження: {str(e)}"
    except Exception as e:
        return False, f"Помилка: {str(e)}"

def get_dashboard_stats():
    """Отримує статистику для dashboard"""
    try:
        stats = {
            'total_files': 0,
            'total_size': 0,
            'total_downloads': 0,
            'file_types': {},
            'recent_uploads': [],
            'top_downloads': [],
            'disk_usage': get_disk_usage()
        }
        
        # Рахуємо файли
        files_dir = app.config['FILES_FOLDER']
        for f in os.listdir(files_dir):
            try:
                full_path = safe_join(files_dir, f)
                if os.path.isfile(full_path) and not f.startswith('.'):
                    stats['total_files'] += 1
                    file_size = os.path.getsize(full_path)
                    stats['total_size'] += file_size
                    
                    # Тип файлу
                    ext = os.path.splitext(f)[1].lower()[1:]
                    if ext:
                        stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
            except:
                pass
        
        # Завантаження логів
        downloads_log = load_json(DOWNLOADS_LOG)
        for filename, data in downloads_log.items():
            stats['total_downloads'] += data.get('count', 0)
        
        # Топ файлів по завантаженням
        top_files = sorted(downloads_log.items(), key=lambda x: x[1].get('count', 0), reverse=True)[:5]
        stats['top_downloads'] = [
            {
                'filename': filename,
                'count': data.get('count', 0)
            }
            for filename, data in top_files
        ]
        
        stats['formatted_size'] = format_file_size(stats['total_size'])
        
        return stats
    except Exception as e:
        app.logger.error(f"Stats error: {str(e)}")
        return None

# ==================== SKINBOT ROUTES ====================

def skinbot_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('skinbot_user_id'):
            return redirect(url_for('skinbot_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', message="Внутрішня помилка сервера"), 500

@app.route('/login', methods=['GET'])
def login_redirect():
    """Redirect to telegram login"""
    return redirect(url_for('admin_login'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
def admin():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'date')
    sort_order = request.args.get('order', 'desc')
    file_type = request.args.get('type', '')
    
    if page < 1:
        page = 1
    
    stats = get_dashboard_stats()
    result = get_paginated_files(page, 15, search_query, sort_by, sort_order, file_type)
    return render_template(
        'admin.html',
        files=result['files'],
        page=result['page'],
        total_pages=result['total_pages'],
        search_query=search_query,
        sort_by=sort_by,
        sort_order=sort_order,
        file_type=file_type,
        file_types=result['file_types'],
        total_files=result['total'],
        stats=stats
    )

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Файл не вибрано'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Файл не вибрано'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        file_path = os.path.join(app.config['FILES_FOLDER'], filename)
        counter = 1
        original_filename = filename
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_filename)
            filename = f"{name}_{counter}{ext}"
            file_path = os.path.join(app.config['FILES_FOLDER'], filename)
            counter += 1
        
        try:
            file.save(file_path)
            return jsonify({
                'success': True, 
                'message': f'Файл {filename} успішно завантажено!',
                'filename': filename
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f'Помилка: {str(e)}'}), 500

@app.route('/upload_url', methods=['POST'])
@login_required
def upload_from_url():
    url = request.form.get('url', '').strip()
    custom_filename = request.form.get('filename', '').strip()
    
    if not url:
        flash('URL не вказано', 'error')
        return redirect(url_for('admin'))
    
    success, result = download_file_from_url(url, custom_filename)
    
    if success:
        flash(f'Файл {result} успішно завантажено по URL!', 'success')
    else:
        flash(f'Помилка завантаження: {result}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/delete/<filename>')
@login_required
def delete_file(filename):
    try:
        decoded_name = unquote(filename)
        file_path = safe_join(app.config['FILES_FOLDER'], decoded_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f'Файл {decoded_name} успішно видалено!', 'success')
        else:
            flash('Файл не знайдено!', 'error')
    except Exception as e:
        flash(f'Помилка видалення файлу: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/bulk_delete', methods=['POST'])
@login_required
def bulk_delete():
    """Масове видалення файлів"""
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])
        
        deleted = 0
        for filename in filenames:
            try:
                decoded_name = unquote(filename)
                file_path = safe_join(app.config['FILES_FOLDER'], decoded_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted += 1
            except:
                pass
        
        return jsonify({
            'success': True,
            'message': f'Видалено {deleted} файлів'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== PUBLIC ROUTES ====================

@app.route('/')
def index():
    try:
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('search', '')
        sort_by = request.args.get('sort', 'date')
        sort_order = request.args.get('order', 'desc')
        file_type = request.args.get('type', '')
        
        if page < 1:
            page = 1
            
        result = get_paginated_files(page, 12, search_query, sort_by, sort_order, file_type)
        return render_template(
            'index.html',
            files=result['files'],
            page=result['page'],
            total_pages=result['total_pages'],
            search_query=search_query,
            sort_by=sort_by,
            sort_order=sort_order,
            file_type=file_type,
            file_types=result['file_types'],
            is_logged_in=session.get('logged_in', False),
            is_skinbot_logged=session.get('skinbot_user_id') is not None
        )
        
    except Exception as e:
        app.logger.error(f"Index route error: {str(e)}")
        return render_template('error.html', message="Помилка завантаження файлів"), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        decoded_name = unquote(filename)
        path = safe_join(app.config['FILES_FOLDER'], decoded_name)
        if not os.path.exists(path):
            return render_template('404.html'), 404
        
        preview = request.args.get('preview')
        as_attachment = False if preview is not None else True

        if not preview:
            log_download(decoded_name, 'regular', request.remote_addr)
        
        response = send_from_directory(
            app.config['FILES_FOLDER'],
            filename,
            as_attachment=as_attachment
        )
        if filename.endswith(".woff2"):
            response.headers["Content-Type"] = "font/woff2"
        elif filename.endswith(".ttf"):
            response.headers["Content-Type"] = "font/ttf"

        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"

        return response
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return render_template('404.html'), 404

@app.route('/download/skin/<path:filename>')
def download_skin(filename):
    """Завантаження скіна"""
    try:
        decoded_name = unquote(filename)
        path = safe_join(app.config['SKINS_FOLDER'], decoded_name)
        if not os.path.exists(path):
            return render_template('404.html'), 404
        
        log_download(decoded_name, 'skin', request.remote_addr)
        return send_from_directory(app.config['SKINS_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Skin download error: {str(e)}")
        return render_template('404.html'), 404

@app.route('/preview/<path:filename>')
def preview_file(filename):
    """Прев'ю файла"""
    try:
        file_info = get_file_info(filename, 'files')
        if not file_info:
            return render_template('404.html'), 404
        
        preview = get_file_preview(file_info)
        return render_template('preview.html', 
                             file=file_info, 
                             preview=preview,
                             is_logged_in=session.get('logged_in', False))
    except Exception as e:
        app.logger.error(f"Preview error: {str(e)}")
        return render_template('404.html'), 404

@app.route('/preview/skin/<path:filename>')
def preview_skin(filename):
    """Прев'ю скіна"""
    try:
        file_info = get_file_info(filename, 'skins')
        if not file_info:
            return render_template('404.html'), 404
        
        preview = get_file_preview(file_info)
        return render_template('preview.html', 
                             file=file_info, 
                             preview=preview,
                             is_logged_in=session.get('logged_in', False))
    except Exception as e:
        app.logger.error(f"Skin preview error: {str(e)}")
        return render_template('404.html'), 404

@app.route('/preview/pdf/<filename>')
def preview_pdf(filename):
    file_path = safe_join(app.config['FILES_FOLDER'], filename)
    if not os.path.exists(file_path):
        abort(404)
    
    try:
        images = convert_from_bytes(open(file_path, 'rb').read())
        img_io = io.BytesIO()
        images[0].save(img_io, 'JPEG', quality=70)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        app.logger.error(f"PDF preview error: {str(e)}")
        abort(500)

@app.route('/preview/full/<path:filename>')
def preview_full_file(filename):
    """Повний перегляд файлу"""
    file_info = get_file_info(filename, 'files')
    if not file_info or not file_info['is_text']:
        abort(404)
    encoding = detect_encoding(file_info['path'])
    try:
        with open(file_info['path'], 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
            try:
                lexer = get_lexer_for_filename(file_info['original_name'])
                formatter = formatters.HtmlFormatter(style='monokai')
                highlighted = pygments.highlight(content, lexer, formatter)
                return render_template('preview_full.html',
                                    file=file_info,
                                    content=highlighted,
                                    style=formatter.get_style_defs('.highlight'),
                                    is_logged_in=session.get('logged_in', False))
            except:
                return render_template('preview_full.html',
                                    file=file_info,
                                    content=content,
                                    style='',
                                    is_logged_in=session.get('logged_in', False))
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

@app.route('/qrcode/<path:filename>')
def generate_qr(filename):
    """Генерація QR коду для файлу"""
    try:
        # Створюємо повну URL
        file_url = url_for('download_file', filename=filename, _external=True)
        
        # Генеруємо QR код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(file_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертуємо в BytesIO
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        app.logger.error(f"QR generation error: {str(e)}")
        abort(500)

# ==================== PRIVATE FILES ROUTES ====================

@app.route('/admin/upload_private', methods=['POST'])
@login_required
def upload_private_file():
    """Завантаження приватного файлу"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Файл не вибрано'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Файл не вибрано'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        file_id = secrets.token_urlsafe(8)
        file_path = os.path.join(app.config['PRIVATE_FILES_FOLDER'], f"private_{file_id}_{filename}")
        
        password = generate_file_password()
        
        try:
            file.save(file_path)
            
            private_files = load_json(PRIVATE_FILES_DB)
            private_files[file_id] = {
                'original_name': filename,
                'stored_name': f"private_{file_id}_{filename}",
                'password': password,
                'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'size': os.path.getsize(file_path),
                'type': filename.split('.')[-1] if '.' in filename else 'unknown'
            }
            save_json(PRIVATE_FILES_DB, private_files)
            
            return jsonify({
                'success': True,
                'message': f'Приватний файл завантажено!',
                'password': password,
                'file_id': file_id
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/private_files')
@login_required
def admin_private_files():
    """Список приватних файлів"""
    private_files = load_json(PRIVATE_FILES_DB)
    
    files_list = []
    for file_id, data in private_files.items():
        files_list.append({
            'id': file_id,
            'name': data['original_name'],
            'password': data['password'],
            'date': data['upload_date'],
            'size': format_file_size(data['size']),
            'type': data['type'],
            'url': url_for('access_private_file', file_id=file_id, _external=True)
        })
    
    files_list.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('admin_private_files.html', files=files_list)

@app.route('/admin/private/<file_id>/reset_password', methods=['POST'])
@login_required
def reset_private_password(file_id):
    """Скидання паролю приватного файлу"""
    try:
        private_files = load_json(PRIVATE_FILES_DB)
        
        if file_id not in private_files:
            return jsonify({'success': False, 'message': 'Файл не знайдено'})
        
        new_password = generate_file_password()
        private_files[file_id]['password'] = new_password
        save_json(PRIVATE_FILES_DB, private_files)
        
        return jsonify({'success': True, 'password': new_password})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/private/<file_id>/delete', methods=['POST'])
@login_required
def delete_private_file(file_id):
    """Видалення приватного файлу"""
    try:
        private_files = load_json(PRIVATE_FILES_DB)
        
        if file_id not in private_files:
            return jsonify({'success': False, 'message': 'Файл не знайдено'})
        
        file_path = os.path.join(app.config['PRIVATE_FILES_FOLDER'], private_files[file_id]['stored_name'])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        del private_files[file_id]
        save_json(PRIVATE_FILES_DB, private_files)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/p/<file_id>')
def access_private_file(file_id):
    """Доступ до приватного файлу з перевіркою паролю"""
    try:
        private_files = load_json(PRIVATE_FILES_DB)
        
        if file_id not in private_files:
            return render_template('404.html'), 404
        
        file_data = private_files[file_id]
        password_param = request.args.get('p', '')
        
        if password_param and password_param == file_data['password']:
            file_path = os.path.join(app.config['PRIVATE_FILES_FOLDER'], file_data['stored_name'])
            if os.path.exists(file_path):
                log_download(file_data['original_name'], 'private', request.remote_addr)
                return send_file(file_path, as_attachment=True, download_name=file_data['original_name'])
            return render_template('404.html'), 404

        return render_template('404.html'), 404
    except Exception as e:
        app.logger.error(f"Private file access error: {str(e)}")
        return render_template('404.html'), 404

@app.route('/p/<file_id>/verify', methods=['POST'])
def verify_private_password(file_id):
    """Перевірка паролю для приватного файлу"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        private_files = load_json(PRIVATE_FILES_DB)
        
        if file_id not in private_files:
            return jsonify({'success': False, 'message': 'Файл не знайдено'})
        
        if password == private_files[file_id]['password']:
            return jsonify({'success': True, 'url': f'/p/{file_id}?p={password}'})
        else:
            return jsonify({'success': False, 'message': 'Невірний пароль'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ==================== TELEGRAM ADMIN AUTH ====================

@app.route('/admin_login')
def admin_login():
    """Сторінка авторизації через Telegram бота"""
    if session.get('logged_in'):
        return redirect(url_for('admin'))
    return render_template('admin_telegram_login.html')

@app.route('/admin_login/request_code', methods=['POST'])
def request_admin_code():
    """Запит коду через Telegram бота"""
    try:
        import sys
        sys.path.append(os.path.dirname(__file__))
        from admin_bot import send_admin_code, ADMIN_ID
        
        code = send_admin_code(ADMIN_ID)
        
        if code:
            return jsonify({'success': True, 'message': 'Код надіслано в Telegram!'})
        else:
            return jsonify({'success': False, 'message': 'Помилка відправки коду'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin_login/verify', methods=['POST'])
def verify_admin_code():
    """Перевірка коду з Telegram"""
    try:
        data = request.get_json()
        code = data.get('code', '').upper().strip()
        
        if not code or len(code) != 6:
            return jsonify({'success': False, 'message': 'Невірний формат коду'})
        
        codes = load_json(ADMIN_CODES_DB)
        
        if code not in codes:
            return jsonify({'success': False, 'message': 'Невірний код'})
        
        code_data = codes[code]
        
        if code_data.get('used', False):
            return jsonify({'success': False, 'message': 'Код вже використано'})
        
        if time.time() - code_data['timestamp'] > 600:
            return jsonify({'success': False, 'message': 'Код прострочений'})
        
        codes[code]['used'] = True
        save_json(ADMIN_CODES_DB, codes)
        
        session['logged_in'] = True
        session['auth_method'] = 'telegram'
        
        return jsonify({'success': True})
        
    except Exception as e:
        app.logger.error(f"Verify admin error: {str(e)}")
        return jsonify({'success': False, 'message': 'Помилка сервера'})

# ==================== API ENDPOINTS ====================

@app.route('/api/stats')
def api_stats():
    """API для отримання статистики"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    stats = get_dashboard_stats()
    return jsonify(stats)

@app.route('/api/downloads/<filename>')
def api_file_downloads(filename):
    """API для отримання статистики завантажень файлу"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    logs = load_json(DOWNLOADS_LOG)
    file_data = logs.get(filename, {})
    
    return jsonify(file_data)
        
@app.route("/skinbot/login")
def skinbot_login():
    if session.get('skinbot_user_id'):
        return redirect(url_for('skinbot_dashboard'))
    return render_template('skinbot_login.html')

@app.route('/skinbot/verify', methods=['POST'])
def skinbot_verify():
    """Перевірка коду з Telegram"""
    try:
        data = request.get_json()
        code = data.get('code', '').upper().strip()
        
        if not code or len(code) != 6:
            return jsonify({'success': False, 'message': 'Невірний формат коду'})
        
        codes = load_json(CODES_DB)
        
        if code not in codes:
            return jsonify({'success': False, 'message': 'Невірний код'})
        
        code_data = codes[code]
        
        if code_data.get('used', False):
            return jsonify({'success': False, 'message': 'Код вже використано'})
        
        if time.time() - code_data.get('timestamp', 0) > 600:
            return jsonify({'success': False, 'message': 'Код прострочений'})
        
        # Позначаємо код як використаний
        codes[code]['used'] = True
        save_json(CODES_DB, codes)
        
        # Зберігаємо дані користувача в сесії
        session['skinbot_user_id'] = code_data['telegram_id']
        session['skinbot_username'] = code_data['username']
        session.permanent = True  # Додаємо постійну сесію
        
        return jsonify({'success': True})
        
    except Exception as e:
        app.logger.error(f"Verify error: {str(e)}")
        return jsonify({'success': False, 'message': 'Помилка сервера'})

@app.route('/skinbot')
@skinbot_required
def skinbot_dashboard():
    """Панель управління скінами"""
    try:
        user_id = session.get('skinbot_user_id')
        username = session.get('skinbot_username', 'Unknown')
        
        if not user_id:
            app.logger.error("No user_id in session")
            return redirect(url_for('skinbot_login'))
        
        # Завантажуємо дані користувачів
        users = load_json(USERS_DB)
        user_id_str = str(user_id)
        skins = []
        
        # Перевіряємо чи існує користувач
        if user_id_str in users:
            user_data = users[user_id_str]
            # Перевіряємо чи є скіни
            if 'skins' in user_data and isinstance(user_data['skins'], list):
                skins = user_data['skins']
            else:
                app.logger.warning(f"User {user_id_str} has no skins or invalid skins data")
                skins = []
        else:
            # Якщо користувача немає в базі - створюємо його
            app.logger.info(f"Creating new user entry for {user_id_str}")
            users[user_id_str] = {
                'telegram_id': user_id,
                'username': username,
                'skins': []
            }
            save_json(USERS_DB, users)
        
        # Логуємо для debug
        app.logger.info(f"User {username} ({user_id}) has {len(skins)} skins")
        
        # Сортуємо скіни за датою (найновіші спочатку)
        if skins:
            skins.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return render_template('skinbot_dashboard.html', 
                             username=username,
                             skins=skins)
                             
    except Exception as e:
        app.logger.error(f"Dashboard error: {str(e)}")
        app.logger.error(f"Error type: {type(e).__name__}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Показуємо помилку без редіректа
        return render_template('error.html', 
                             message=f"Помилка завантаження панелі скінів: {str(e)}"), 500

@app.route('/skinbot/delete', methods=['POST'])
@skinbot_required
def skinbot_delete_skin():
    """Видалення скіна"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'message': 'Не вказано файл'})
        
        user_id = session.get('skinbot_user_id')
        users = load_json(USERS_DB)
        user_id_str = str(user_id)
        
        if user_id_str not in users:
            return jsonify({'success': False, 'message': 'Користувач не знайдений'})
        
        skins = users[user_id_str].get('skins', [])
        new_skins = [s for s in skins if s['filename'] != filename]
        
        if len(new_skins) == len(skins):
            return jsonify({'success': False, 'message': 'Скін не знайдено'})
        
        users[user_id_str]['skins'] = new_skins
        save_json(USERS_DB, users)
        
        # Видаляємо файл
        try:
            file_path = os.path.join(app.config['SKINS_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            app.logger.error(f"Error deleting file: {str(e)}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        app.logger.error(f"Delete skin error: {str(e)}")
        return jsonify({'success': False, 'message': 'Помилка видалення'})

@app.route('/skinbot/logout')
def skinbot_logout():
    """Вихід з SkinBot"""
    session.pop('skinbot_user_id', None)
    session.pop('skinbot_username', None)
    flash('Ви вийшли з SkinBot', 'info')
    return redirect(url_for('index'))

# ==================== ADMIN ROUTES ====================

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('auth_method', None)
    flash('Ви вийшли з системи', 'info')
    return redirect(url_for('index'))

@app.route('/index')
def index_index():
    try:
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('search', '')
        sort_by = request.args.get('sort', 'date')
        sort_order = request.args.get('order', 'desc')
        file_type = request.args.get('type', '')
        
        if page < 1:
            page = 1
            
        result = get_paginated_files(page, 12, search_query, sort_by, sort_order, file_type)
        return render_template(
            'index.html',
            files=result['files'],
            page=result['page'],
            total_pages=result['total_pages'],
            search_query=search_query,
            sort_by=sort_by,
            sort_order=sort_order,
            file_type=file_type,
            file_types=result['file_types'],
            is_logged_in=session.get('logged_in', False),
            is_skinbot_logged=session.get('skinbot_user_id') is not None
        )
        
    except Exception as e:
        app.logger.error(f"Index route error: {str(e)}")
        return render_template('error.html', message="Помилка завантаження файлів"), 500

@app.route('/robots.txt')
def robots_txt():
    robots_content = """
User-agent: *

Allow: /

Allow: /skinbot
Allow: /skinbot/login

Allow: /preview/

Disallow: /admin
Disallow: /admin/
Disallow: /admin_login
Disallow: /logout

Disallow: /admin/private_files
Disallow: /p/

Disallow: /skinbot/logout

Disallow: /preview/skin/
Disallow: /download/skin/
Disallow: /download/

Disallow: /*?

Sitemap: https://host.zjck.eu/sitemap.xml"""
    
    return Response(robots_content, mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    # Динамічна генерація з поточною датою
    today = datetime.now().strftime('%Y-%m-%d')
    
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  
  <url>
    <loc>https://host.zjck.eu/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  
  <url>
    <loc>https://host.zjck.eu/skinbot</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  
  <url>
    <loc>https://host.zjck.eu/skinbot/login</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>

</urlset>"""
    
    return Response(sitemap_content, mimetype='application/xml')
    
@app.route('/admin/modules')
@login_required
def admin_modules():
    """Сторінка управління модулями"""
    configs = module_loader.get_all_configs()
    return render_template('admin_modules.html', modules=configs)
 
 
@app.route('/admin/modules/<module_name>/toggle', methods=['POST'])
@login_required
def toggle_module(module_name):
    """Перемикач enabled/disabled для модуля"""
    from flask import request, jsonify
    data = request.get_json()
    field = data.get('field')   # 'enabled' or 'visibility'
    value = data.get('value')   # True/False or 'public'/'admin'
 
    allowed_fields = {'enabled', 'visibility'}
    if field not in allowed_fields:
        return jsonify({'success': False, 'message': 'Invalid field'})
 
    ok = module_loader.save_config(module_name, {field: value})
    if ok:
        return jsonify({'success': True, 'message': f'Збережено. Перезапустіть сервер для застосування.'})
    return jsonify({'success': False, 'message': 'Модуль не знайдено'})
    
if __name__ == '__main__':
    try:
        logging.info("Запуск Flask сервера...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logging.critical(f"Критична помилка: {str(e)}")
