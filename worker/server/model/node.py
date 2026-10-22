from db import alchemy_db as db


class Node(db.Model):
    __tablename__ = 'node'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    created_time = db.Column(db.DateTime)
    name = db.Column(db.String(255))
    x = db.Column(db.Double)
    y = db.Column(db.Double)
    type = db.Column(db.String(255))
    function_block_id = db.Column(db.BigInteger)
    function_block_version_id = db.Column(db.BigInteger)
    data_id = db.Column(db.BigInteger)
    computation_params = db.Column(db.Text)
    state = db.Column(db.String(255))
    analysis_id = db.Column(db.BigInteger)
    locked = db.Column(db.Boolean)
    tag = db.Column(db.String(200))
    system_env = db.Column(db.String(100))
    computation_resource_configure = db.Column(db.String(200))
    dynamic_generation_id = db.Column(db.BigInteger)
    dynamic_generation_session_id = db.Column(db.BigInteger)
    dynamic_generation_locked = db.Column(db.Boolean)
    annotated = db.Column(db.Boolean, default=False)
    avg_duration = db.Column(db.Float, default=0.0)
    visualizer_id = db.Column(db.BigInteger)
    visualizer_previous_node_id = db.Column(db.BigInteger)
    visualizer_locked = db.Column(db.Boolean, default=False)
    is_review_error = db.Column(db.Boolean, default=False)

    def to_dict(self):
        node_attrs_dict = dict()
        node_attrs_dict["id"] = self.id
        node_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        node_attrs_dict["name"] = self.name
        node_attrs_dict["x"] = self.x
        node_attrs_dict["y"] = self.y
        node_attrs_dict["type"] = self.type
        node_attrs_dict["functionBlockId"] = self.function_block_id
        node_attrs_dict["functionBlockVersionId"] = self.function_block_version_id
        node_attrs_dict["dataId"] = self.data_id
        node_attrs_dict["computationParams"] = self.computation_params
        node_attrs_dict["state"] = self.state
        node_attrs_dict["analysisId"] = self.analysis_id
        node_attrs_dict["locked"] = self.locked
        node_attrs_dict["tag"] = self.tag
        node_attrs_dict["systemEnv"] = self.system_env
        node_attrs_dict["computationResourceConfigure"] = self.computation_resource_configure
        node_attrs_dict["dynamicGenerationId"] = self.dynamic_generation_id
        node_attrs_dict["dynamicGenerationSessionId"] = self.dynamic_generation_session_id
        node_attrs_dict["dynamicGenerationLocked"] = self.dynamic_generation_locked
        node_attrs_dict["annotated"] = self.annotated
        node_attrs_dict["avgDuration"] = self.avg_duration
        node_attrs_dict["visualizerId"] = self.visualizer_id
        node_attrs_dict["visualizerPreviousNodeId"] = self.visualizer_previous_node_id
        node_attrs_dict["visualizerLocked"] = self.visualizer_locked
        node_attrs_dict["isReviewError"] = self.is_review_error
        return node_attrs_dict
