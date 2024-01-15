from flask import Blueprint, jsonify
from flask_restx import Api

from .game import ns,ru,st,dlt,get,llen,info_clients

bp_api = Blueprint("demo", __name__, url_prefix="/api")
api = Api(bp_api, version="1.0", title="卡牌项目模板", description="Card Template",prefix='/v1')

api.add_namespace(ns)
api.add_namespace(ru)
api.add_namespace(st)
api.add_namespace(dlt)
api.add_namespace(get)
api.add_namespace(llen)
api.add_namespace(info_clients)


@bp_api.app_errorhandler(Exception)
def handle_exception(error):
    message = [str(x) for x in error.args]
    status_code = error.code
    response = {
        'message': f"{error.__class__.__name__} message: {message}"
    }
    return jsonify(response), status_code
