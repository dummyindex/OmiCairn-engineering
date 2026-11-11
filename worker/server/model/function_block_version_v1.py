from db import alchemy_db as db
import json


class FunctionBlockVersionV1(db.Model):

    __tablename__ = "function_block_version_v1"

    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    name = db.Column(db.String(100), nullable=False, comment='name')
    function_block_id = db.Column(
        db.BigInteger, nullable=False, comment='parent function block ID')
    args = db.Column(db.Text, comment='arguments')
    tag = db.Column(db.String(100), comment='tag')
    document_url = db.Column(db.Text, comment='documentation URL')
    description = db.Column(db.Text, comment='description')
    source = db.Column(db.String(100), comment='source')
    plot_only = db.Column(db.Boolean, comment='plot only')
    runtime_version = db.Column(db.String(45), comment='runtime version')
    created_time = db.Column(db.DateTime, comment='creation time')
    state = db.Column(db.String(50), comment='state')
    program_language = db.Column(db.String(45), comment='programming language')
    error_message = db.Column(db.Text, comment='error message')
    preset_env = db.Column(db.String(255), comment='preset environment')
    average_time = db.Column(db.Float, comment='average runtime')
    is_v2 = db.Column(db.Boolean, nullable=True, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'functionBlockId': self.function_block_id,
            'args': json.loads(self.args) if self.args else None,
            'tag': self.tag,
            'documentUrl': self.document_url,
            'description': self.description,
            'source': self.source,
            'plotOnly': self.plot_only,
            'runtimeVersion': self.runtime_version,
            'createdTime': self.created_time,
            'state': self.state,
            'programLanguage': self.program_language,
            'errorMessage': self.error_message,
            'presetEnv': self.preset_env,
            'averageTime': self.average_time,
            'isV2': self.is_v2
        }
