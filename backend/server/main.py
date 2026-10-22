import os
from flask import Flask
from flask_cors import CORS

from tool.json_encoder import StrictJSONEncoder
from db import alchemy_db
import configs
from controller.user import user_api
from controller.analysis import analysis_api
from controller.data import data_api
from controller.sss import sss_api
from controller.function_block_v1 import function_block_v1_api
from controller.pipeline_template import pipeline_template_api
from controller.flow import flow_api
from controller.node import node_api
from controller.edge import edge_api
from controller.computation import computation_api
from controller.gseapy import gseapy_api
from controller.gpt import gpt_api
from controller.report import report_api
from controller.system_file import system_file_api
from controller.burial_point import burial_point_api
from controller.schedule import schedule_api
from controller.vitessce import vitessce_api
from controller.inform import inform_api
from controller.workflow_report import workflow_report_api
from controller.param_file import param_file_api
from controller.api_key import api_key_api
from controller.figure import figure_api
from controller.chat import chat_bp
from controller.chatbot import chatbot_bp
from controller.file_management import file_api
from controller.consumption import consumption_api
from log.logger_factory import logger_factory

logger = logger_factory.create_logger("main.py")

def create_app(testing=False):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(configs)
    app.config["TESTING"] = bool(testing)
    # mysql_alchemy
    alchemy_db.init_app(app)
    app.json_encoder = StrictJSONEncoder
    app.register_blueprint(user_api.blueprint)
    app.register_blueprint(analysis_api.blueprint)
    app.register_blueprint(data_api.blueprint)
    app.register_blueprint(sss_api.blueprint)
    app.register_blueprint(pipeline_template_api.blueprint)
    app.register_blueprint(node_api.blueprint)
    app.register_blueprint(edge_api.blueprint)
    app.register_blueprint(computation_api.blueprint)
    app.register_blueprint(gseapy_api.blueprint)
    app.register_blueprint(gpt_api.blueprint)
    app.register_blueprint(function_block_v1_api.blueprint)
    app.register_blueprint(report_api.blueprint)
    app.register_blueprint(system_file_api.blueprint)
    app.register_blueprint(flow_api.blueprint)
    app.register_blueprint(burial_point_api.blueprint)
    app.register_blueprint(schedule_api.blueprint)
    app.register_blueprint(inform_api.blueprint)
    app.register_blueprint(vitessce_api.blueprint)
    app.register_blueprint(workflow_report_api.blueprint)
    app.register_blueprint(param_file_api.blueprint)
    app.register_blueprint(api_key_api.blueprint)
    app.register_blueprint(figure_api.blueprint)
    app.register_blueprint(chat_bp)
    # AI-assistant side panel of the analysis page (frontend services/chatbotService.ts)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(file_api.blueprint)
    app.register_blueprint(consumption_api.blueprint)
    # Restrict cross-origin access to the configured frontend origin(s).
    cors_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
    CORS(app, origins=cors_origins)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
