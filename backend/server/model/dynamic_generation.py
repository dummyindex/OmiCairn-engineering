from db import alchemy_db as db


class DynamicGeneration(db.Model):
    __tablename__ = 'dynamic_generation'
    generation_id = db.Column(
        db.BigInteger, primary_key=True, autoincrement=True)
    analysis_id = db.Column(db.BigInteger)
    previous_node_id = db.Column(db.BigInteger)
    previous_computation_id = db.Column(db.BigInteger)
    max_node = db.Column(db.Integer)
    max_branch = db.Column(db.Integer)
    user_request = db.Column(db.Text)
    created_time = db.Column(db.DateTime)
    state = db.Column(db.String(50))
    rest_node_count = db.Column(db.Integer)
    computation_resource_configure = db.Column(db.String(150))
    generation_mode = db.Column(db.String(50))
    file_ids = db.Column(db.Text)
    max_debug = db.Column(db.Integer)
    plan_name = db.Column(db.String(50))
    plan_status = db.Column(db.String(50))
    plan_status_message = db.Column(db.String(150))
    llm_model = db.Column(db.String(255))
    version = db.Column(db.String(24))
    replan_count_limit = db.Column(db.Integer)
    claude_execution_model = db.Column(db.String(255))
    claude_max_iterations = db.Column(db.Integer, default=100)

    def to_dict(self):
        dynamic_generation_attrs_dict = dict()
        dynamic_generation_attrs_dict["generationId"] = self.generation_id
        dynamic_generation_attrs_dict["analysisId"] = self.analysis_id
        dynamic_generation_attrs_dict["previousNodeId"] = self.previous_node_id
        dynamic_generation_attrs_dict["previousComputationId"] = self.previous_computation_id
        dynamic_generation_attrs_dict["maxNode"] = self.max_node
        dynamic_generation_attrs_dict["maxBranch"] = self.max_branch
        dynamic_generation_attrs_dict["userRequest"] = self.user_request
        dynamic_generation_attrs_dict["createdTime"] = self.created_time and self.created_time.timestamp(
        ) * 1000
        dynamic_generation_attrs_dict["state"] = self.state
        dynamic_generation_attrs_dict["restNodeCount"] = self.rest_node_count
        dynamic_generation_attrs_dict["computationResourceConfigure"] = self.computation_resource_configure
        dynamic_generation_attrs_dict["generationMode"] = self.generation_mode
        dynamic_generation_attrs_dict["fileIds"] = self.file_ids
        dynamic_generation_attrs_dict["maxDebug"] = self.max_debug
        dynamic_generation_attrs_dict["planName"] = self.plan_name
        dynamic_generation_attrs_dict["planStatus"] = self.plan_status
        dynamic_generation_attrs_dict["planStatusMessage"] = self.plan_status_message
        dynamic_generation_attrs_dict["llmModel"] = self.llm_model
        dynamic_generation_attrs_dict["version"] = self.version
        dynamic_generation_attrs_dict["replanCountLimit"] = self.replan_count_limit
        dynamic_generation_attrs_dict["claudeExecutionModel"] = self.claude_execution_model
        dynamic_generation_attrs_dict["claudeMaxIterations"] = self.claude_max_iterations
        return dynamic_generation_attrs_dict
