# =========================
# Created by git @karmaxexclusive
# =========================

import importlib
import logging
import pkgutil
from aiogram import Dispatcher, Router

def load_plugins(dp: Dispatcher):
    """
    Finds and registers all router instances from the plugins directory.
    """
    plugins_package = "TeslaQuiz.plugins"
    for _, name, _ in pkgutil.iter_modules([plugins_package.replace('.', '/')]):
        try:
            module = importlib.import_module(f"{plugins_package}.{name}")
            for item_name in dir(module):
                item = getattr(module, item_name)
                if isinstance(item, Router):
                    dp.include_router(item)
                    logging.info(f"Successfully registered router from {name}")
        except Exception as e:
            logging.error(f"Failed to load plugin {name}: {e}")

# =========================
