import importlib.util
import logging
import os
from logging.handlers import TimedRotatingFileHandler
import json

from flask import Flask, has_request_context, request

# Standard library imports
from .config import DevelopmentConfig, TestingConfig

# from logging.handlers import SMTPHandler


def create_app(config=TestingConfig):
    app = Flask(__name__)

    register_blueprints(app, app.config["ROUTES_DIR"])

    app.config.from_object(config)
    print(f"ENV is set to:\n   {json.dumps(app.config, indent=3, sort_keys=True)}")

    app.secret_key = app.config["SECRET_KEY"]

    class RequestFormatter(logging.Formatter):
        def format(self, record):
            if has_request_context():
                record.url = request.url
                record.remote_addr = request.remote_addr
            else:
                record.url = None
                record.remote_addr = None
            return super().format(record)

    formatter = RequestFormatter(
        "{'TIME':%(asctime)s,'ADDRESS':'%(remote_addr)s','URL': '%(url)s','TYPE':'%(levelname)s','MODULE':'%(module)s','MSG':{%(message)s}}"
    )
    handler = TimedRotatingFileHandler(
        app.config["LOG_FILE"], when="midnight", interval=1, encoding="utf8"
    )
    handler.suffix = "%Y-%m-%d"
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)
    return app


def register_blueprints(app, dir):
    try:
        lst = os.listdir("app/" + dir)
    except OSError:
        print("NO SE PUDIERON CARGAR LAS BLUEPRINTS")
    else:
        for name_route in lst:
            if name_route != "__pycache__":
                name_class = name_route.split(".py")[0]
                module = importlib.import_module("app." + dir + "." + name_class)
                app.register_blueprint(getattr(module, name_class))
