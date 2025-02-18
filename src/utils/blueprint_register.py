import importlib
import pkgutil
import os
from flask import Blueprint


def register_blueprints(app, package_name, package_path):
    for _, name, is_pkg in pkgutil.iter_modules(package_path):
        module = importlib.import_module(f"{package_name}.{name}")
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if isinstance(attribute, Blueprint):
                app.register_blueprint(attribute)
