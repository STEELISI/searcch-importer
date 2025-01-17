
from flask import abort
from searcch.importer.server.app import app

def verify_api_key(api_key):
    if not api_key:
        abort(403,description="missing instance X-Api-Key")
    if api_key != app.config.get("SECRET_KEY"):
        abort(401,description="incorrect instance X-Api-Key")
