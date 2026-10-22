from flask import (
    Flask
)
from flask_cors import CORS
import typing as t
import json
from tool.json_encoder import StrictJSONProvider
from db import alchemy_db
import config
from controller.task import task_api
from controller.computation import computation_api
from controller.interval import interval_api
from controller.health import health_api
from controller.dynamic_generation import dynamic_generation_api
from controller.visualizer import visualizer_api
from controller.dynamic_generation_llm_monitor import dynamic_generation_llm_monitor_bp
from controller.inputs import inputs_bp
from controller.code_agent_proxy import code_agent_proxy_bp
from controller.rag import rag_api
from log.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("main")

app = Flask(__name__, static_folder=None)
app.config.from_object(config)

# mysql_alchemy
logger.info("init mysql_alchemy")
alchemy_db.init_app(app)

# Set the custom JSON provider
app.json = StrictJSONProvider(app)

logger.info("registering api")
app.register_blueprint(task_api.blueprint)
app.register_blueprint(computation_api.blueprint)
app.register_blueprint(interval_api.blueprint)
app.register_blueprint(health_api.blueprint)
app.register_blueprint(dynamic_generation_api.blueprint)
app.register_blueprint(visualizer_api.blueprint)
app.register_blueprint(dynamic_generation_llm_monitor_bp)
app.register_blueprint(inputs_bp)
app.register_blueprint(code_agent_proxy_bp)
app.register_blueprint(rag_api.blueprint)


logger.info("registering CORS")
CORS(app)

if __name__ == '__main__':
    logger.info("launch server")
    logger.info("server is running (development server)")
    app.run()

# For gunicorn
application = app
