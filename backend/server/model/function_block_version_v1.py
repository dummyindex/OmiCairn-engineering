# CREATE TABLE `function_block_version_v1` (
#   `id` bigint NOT NULL AUTO_INCREMENT,
#   `name` varchar(100) DEFAULT NULL,
#   `function_block_id` bigint DEFAULT NULL,
#   `args` text,
#   `tag` varchar(100) DEFAULT NULL,
#   `document_url` text,
#   `description` text,
#   `source` varchar(100) DEFAULT NULL,
#   `plot_only` tinyint DEFAULT '0',
#   `created_time` datetime DEFAULT NULL,
#   `state` varchar(50) DEFAULT NULL,
#   `program_language` varchar(45) DEFAULT NULL,
#   `error_message` text,
#   PRIMARY KEY (`id`),
#   KEY `name_index` (`name`)
# ) ENGINE=InnoDB AUTO_INCREMENT=20143 DEFAULT CHARSET=utf8mb3

from db import alchemy_db as db
import json

class FunctionBlockVersionV1(db.Model):

    __tablename__ = "function_block_version_v1"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=True)
    function_block_id = db.Column(db.BigInteger, nullable=True)
    args = db.Column(db.Text, nullable=True)
    tag = db.Column(db.String(100), nullable=True)
    document_url = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(100), nullable=True)
    plot_only = db.Column(db.Boolean, nullable=True)
    runtime_version = db.Column(db.String(50), nullable=True)
    created_time = db.Column(db.DateTime, nullable=True)
    state = db.Column(db.String(50), nullable=True)
    program_language = db.Column(db.String(45), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    preset_env = db.Column(db.String(255), nullable=True)
    alt_name = db.Column(db.String(255), nullable=True)
    is_v2 = db.Column(db.Boolean, nullable=True, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "functionBlockId": self.function_block_id,
            "args": json.loads(self.args) if self.args is not None else None,
            "tag": self.tag,
            "documentUrl": self.document_url,
            "description": self.description,
            "source": self.source,
            "plotOnly": self.plot_only,
            "runtimeVersion": self.runtime_version,
            "createdTime": self.created_time,
            "state": self.state,
            "programLanguage": self.program_language,
            "errorMessage": self.error_message,
            "presetEnv": self.preset_env,
            "altName": self.alt_name,
            "isV2": self.is_v2,
        }
