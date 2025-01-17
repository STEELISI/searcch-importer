from flask import abort, jsonify, request, Response, Blueprint
from flask_restful import reqparse, Resource, fields, marshal

import searcch.importer
from searcch.importer.server.app import db
from searcch.importer.server.util import verify_api_key

class StatusResourceRoot(Resource):

    def get(self):
        """
        Return importer status and version.
        """
        api_key = request.headers.get('X-Api-Key')
        verify_api_key(api_key)
        return jsonify({"status":"up","version":searcch.importer.__version__})
