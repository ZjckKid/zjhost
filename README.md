# ZJHost

ZJHost is a multifunctional file-hosting platform built with Python. It provides a web interface for uploading, managing, and sharing files, along with Telegram bots for administrative control and skin management. This project supports modular extensions, private file access, QR code generation, and more.

## Features

- **File Hosting**: Upload and manage files through a web interface.
- **Private Files**: Secure access to private files with authentication.
- **Modular System**: Extensible with custom modules (e.g., QR generator).
- **Admin Panel**: Web-based admin interface for managing the platform.
- **Telegram Bots**:
  - Admin Bot: For authentication and admin notifications.
  - Skin Bot: For managing user skins and avatars for minecraft.
- **Cloudflare Tunnel**: Secure tunneling for local development or deployment.
- **File Preview**: Support for images, PDFs, code highlighting, and more.
- **User Management**: User registration, login, and session management.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ZjckKid/zjhost.git
   cd zjhost
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the `host/` directory with the following variables:
   ```
   SECRET_KEY=your_secret_key_here
   ADMIN_TELEGRAM_TOKEN=your_admin_bot_token
   ADMIN_TELEGRAM_ID=your_admin_telegram_id
   SKIN_TELEGRAM_TOKEN=your_skin_bot_token
   ```

4. Configure Cloudflare Tunnel:
   - Ensure `cloudflared` is installed and configured in `host/cloudflared/`.
   - Update `host/cloudflared/config.yml` with your tunnel settings.

## Usage

1. Run the main application:
   ```bash
   python main.py
   ```
   This will start the Flask web app, admin bot, skin bot, and Cloudflare tunnel.

2. Access the web interface:
   - Main site: Visit the URL provided by Cloudflare tunnel.
   - Admin panel: Navigate to `/admin` and authenticate via the Telegram bot.

3. Telegram Bots:
   - Admin Bot: Use commands like `/start` for help and code generation.
   - Skin Bot: Interact for skin-related features.

## Project Structure

```
ZJHost/
├── main.py                 # Main launcher script
├── skin.py                 # Skin bot script
├── requirements.txt        # Python dependencies
├── bot_data/               # Bot data storage
│   ├── admin_codes.json
│   ├── codes.json
│   ├── downloads.json
│   ├── private_files.json
│   └── users.json
├── host/
│   ├── app.py              # Flask web application
│   ├── admin_bot.py        # Admin Telegram bot
│   ├── module_loader.py    # Module loading system
│   ├── cloudflared/        # Cloudflare tunnel setup
│   ├── files/              # Public uploaded files
│   ├── modules/            # Custom modules
│   │   └── qr_generator/
│   ├── privatefiles/       # Private files
│   ├── skins/              # User skins
│   └── templates/          # HTML templates
├── photos/                 # Photo storage
└── README.md
```

## Modules

ZJHost supports custom modules. Add your module in `host/modules/` with a `module.py` and `config.json`.

Example: QR Generator module for generating QR codes.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the terms specified in the LICENSE file.

## Disclaimer

This is my first big project, so there might be some rough edges. Feedback and improvements are appreciated!
