"""
Module Loader
Automatically discovers and registers modules from the /modules/ directory.
"""

import os
import json
import importlib.util
import logging
from functools import wraps
from flask import session, redirect, url_for, abort

logger = logging.getLogger(__name__)

MODULES_DIR = os.path.join(os.path.dirname(__file__), 'modules')


class ModuleLoader:
    def __init__(self, app):
        self.app = app
        self.loaded_modules = {}  # name -> module info
        os.makedirs(MODULES_DIR, exist_ok=True)

    def load_all(self):
        """Scan modules/ folder and register all enabled modules."""
        if not os.path.isdir(MODULES_DIR):
            return

        for name in os.listdir(MODULES_DIR):
            module_dir = os.path.join(MODULES_DIR, name)
            if not os.path.isdir(module_dir):
                continue

            module_py = os.path.join(module_dir, 'module.py')
            config_json = os.path.join(module_dir, 'config.json')

            if not os.path.isfile(module_py):
                continue

            config = self._load_config(config_json, name)

            if not config.get('enabled', True):
                logger.info(f"Module '{name}' is disabled, skipping.")
                continue

            self._register_module(name, module_py, config)

    def _load_config(self, config_path, name):
        """Load config.json for a module, create default if missing."""
        default = {
            "name": name,
            "display_name": name.replace('_', ' ').title(),
            "description": "",
            "version": "1.0.0",
            "enabled": True,
            "visibility": "public",   # "public" or "admin"
            "url_prefix": f"/{name.replace('_', '-')}"
        }
        if os.path.isfile(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                default.update(loaded)
            except Exception as e:
                logger.error(f"Failed to load config for '{name}': {e}")
        else:
            # Write default config
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default, f, ensure_ascii=False, indent=2)
        return default

    def _register_module(self, name, module_py, config):
        """Import module.py and register its blueprint."""
        try:
            spec = importlib.util.spec_from_file_location(f"modules.{name}", module_py)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            # Every module must expose a `blueprint` object
            if not hasattr(mod, 'blueprint'):
                logger.error(f"Module '{name}' has no `blueprint` attribute, skipping.")
                return

            bp = mod.blueprint
            visibility = config.get('visibility', 'public')
            url_prefix = config.get('url_prefix', f"/{name.replace('_', '-')}")

            # For admin modules, wrap all views with login_required
            if visibility == 'admin':
                url_prefix = f"/admin{url_prefix}"
                self._protect_blueprint(bp)

            self.app.register_blueprint(bp, url_prefix=url_prefix)

            self.loaded_modules[name] = {
                'config': config,
                'url_prefix': url_prefix,
                'visibility': visibility,
            }
            logger.info(f"Module '{name}' registered at {url_prefix} [{visibility}]")

        except Exception as e:
            logger.error(f"Failed to load module '{name}': {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _protect_blueprint(self, bp):
        """Wrap all blueprint views with admin login check."""
        @bp.before_request
        def require_admin():
            if not session.get('logged_in'):
                return redirect(url_for('admin_login'))

    def get_all_configs(self):
        """Return list of all modules with their configs (for admin panel)."""
        modules = []
        if not os.path.isdir(MODULES_DIR):
            return modules

        for name in sorted(os.listdir(MODULES_DIR)):
            module_dir = os.path.join(MODULES_DIR, name)
            if not os.path.isdir(module_dir):
                continue
            config_path = os.path.join(module_dir, 'config.json')
            config = self._load_config(config_path, name)
            config['_loaded'] = name in self.loaded_modules
            modules.append(config)
        return modules

    def save_config(self, module_name, updates):
        """Save updated config for a module."""
        config_path = os.path.join(MODULES_DIR, module_name, 'config.json')
        if not os.path.isfile(config_path):
            return False
        config = self._load_config(config_path, module_name)
        config.update(updates)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
