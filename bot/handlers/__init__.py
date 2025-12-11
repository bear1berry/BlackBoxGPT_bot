# bot/handlers/__init__.py

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

from aiogram import Dispatcher, Router


def register_all_handlers(dp: Dispatcher) -> None:
    """
    Dynamically import all modules inside bot.handlers package and include
    every aiogram.Router instance found there into the dispatcher.

    This lets you freely add new handler modules like:
        bot/handlers/start.py        (router = Router(...))
        bot/handlers/menu.py         (router = Router(...))
        bot/handlers/chat.py         (router = Router(...))
    and they will be auto-registered.
    """
    package_name = __name__
    package = importlib.import_module(package_name)

    for module_info in pkgutil.iter_modules(package.__path__):
        module_full_name = f"{package_name}.{module_info.name}"
        module = importlib.import_module(module_full_name)

        for attr_name in dir(module):
            attr: Any = getattr(module, attr_name)
            if isinstance(attr, Router):
                dp.include_router(attr)
