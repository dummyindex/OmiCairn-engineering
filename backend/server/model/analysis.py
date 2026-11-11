from db import alchemy_db as db


class Analysis(db.Model):
    __tablename__ = 'analysis'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    created_time = db.Column(db.DateTime, nullable=False)
    disabled = db.Column(db.Boolean, nullable=False, default=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    bug_fixer_enabled = db.Column(db.Boolean, nullable=False, default=False)
    max_retry = db.Column(db.Integer, nullable=False, default=3)
    figure_visible = db.Column(db.Boolean, nullable=False, default=True)
    error_node_hidden = db.Column(db.Boolean, nullable=False, default=False)
    password = db.Column(db.String(255), nullable=True)
    creation_source = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        analysis_attrs_dict = dict()
        analysis_attrs_dict["id"] = self.id
        analysis_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        analysis_attrs_dict["disabled"] = self.disabled
        analysis_attrs_dict["name"] = self.name
        analysis_attrs_dict["description"] = self.description
        analysis_attrs_dict["bugFixerEnabled"] = self.bug_fixer_enabled
        analysis_attrs_dict["maxRetry"] = self.max_retry
        analysis_attrs_dict["figureVisible"] = self.figure_visible
        analysis_attrs_dict["errorNodeHidden"] = self.error_node_hidden
        analysis_attrs_dict["hasPassword"] = bool(self.password)
        analysis_attrs_dict["creationSource"] = self.creation_source
        return analysis_attrs_dict
