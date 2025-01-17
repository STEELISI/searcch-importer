import os
import logging
import hashlib
import socket

import flask
from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

from searcch.importer.server.config import app_config
from searcch.importer.util.config import (
    config_section,ConfigSection,find_configfile,get_config_parser)
from searcch.importer.importer import get_importer
from searcch.importer.exporter import get_exporter

#
# Read our config in our style, then forward necessary bits into Flask.
#
@config_section
class FlaskConfigSection(ConfigSection):

    @classmethod
    def section_name(cls):
        return "flask"

    @classmethod
    def section_defaults(cls):
        return dict(
            config_name="development")

@config_section
class ServerConfigSection(ConfigSection):

    @classmethod
    def section_name(cls):
        return "server"

    @classmethod
    def section_defaults(cls):
        return dict(
            secret_key="",
            myurl="",
            max_tasks="1",
            remote_register="true",
            remote_update="true",
            remote_update_interval="10",
            remote_delete_on_exit="false")

cf = find_configfile()
config = get_config_parser()
if cf:
    config.read(cf)
config.read_env()
# Set a random secret for ourselves if one is not already set.
if not config["server"]["secret_key"]:
    config["server"]["secret_key"] = hashlib.sha256(os.urandom(32)).hexdigest()
# Construct a URL for ourselves if unset.
if not config["server"]["myurl"]:
    config["server"]["myurl"] = "http://%s/v1" % (socket.gethostname(),)

# Create the app and initialize its Flaskish config from our defaults.
app = Flask(__name__)
config_name = os.getenv("FLASK_ENV",None)
if config_name:
    config["flask"]["config_name"] = config_name
app.config.from_object(app_config[config["flask"].get("config_name","development")])
if os.getenv('FLASK_INSTANCE_CONFIG_FILE'):
    app.config.from_pyfile(os.getenv('FLASK_INSTANCE_CONFIG_FILE'))

# Forward some values into the flask config.
for (k,v) in config["flask"].items():
    app.config[k.upper()] = v
app.config["SECRET_KEY"] = config["server"]["secret_key"]
if config["db"]["url"]:
    app.config["SQLALCHEMY_DATABASE_URI"] = config["db"]["url"]

db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)

if "DEBUG" in app.config and app.config["DEBUG"]:
    @app.before_request
    def log_request_info():
        app.logger.debug("Headers: %r", flask.request.headers)
        app.logger.debug("Body: %r", flask.request.get_data())


from searcch.importer.server.resources.status import (
    StatusResourceRoot)
from searcch.importer.server.resources.artifact_import import (
    ArtifactImportResourceRoot, ArtifactImportResource )

approot = app.config["APPLICATION_ROOT"]

api.add_resource(
    StatusResourceRoot,
    approot + "/status",endpoint="api.status")

api.add_resource(
    ArtifactImportResourceRoot,
    approot + "/artifact/imports", endpoint="api.artifact_imports")
api.add_resource(
    ArtifactImportResource,
    approot + "/artifact/import/<int:artifact_import_id>", endpoint="api.artifact_import")
