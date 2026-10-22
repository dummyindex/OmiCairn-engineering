from db import alchemy_db as db


class Visualizer(db.Model):
    __tablename__ = 'visualizer'
    id = db.Column(db.Integer, primary_key=True)
    original_node_id = db.Column(db.Integer, nullable=False)
    original_computation_id = db.Column(db.Integer, nullable=False)
    analysis_id = db.Column(db.Integer, nullable=False)
    max_count = db.Column(db.Integer, nullable=False, default=0)
    rest_count = db.Column(db.Integer, nullable=False, default=0)
    state = db.Column(db.String(50), nullable=True)
    user_prompt = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)
    generation_mode = db.Column(db.String(50))
    computation_resource_configure = db.Column(db.String(255))
    llm_model = db.Column(db.String(255))

    def to_dict(self):
        visualizer_attrs_dict = dict()
        visualizer_attrs_dict["id"] = self.id
        visualizer_attrs_dict["originalNodeId"] = self.original_node_id
        visualizer_attrs_dict["originalComputationId"] = self.original_computation_id
        visualizer_attrs_dict["analysisId"] = self.analysis_id
        visualizer_attrs_dict["maxCount"] = self.max_count
        visualizer_attrs_dict["restCount"] = self.rest_count
        visualizer_attrs_dict["state"] = self.state
        visualizer_attrs_dict["userPrompt"] = self.user_prompt
        visualizer_attrs_dict["userId"] = self.user_id
        visualizer_attrs_dict["createdTime"] = self.created_time and self.created_time.timestamp(
        ) * 1000
        visualizer_attrs_dict["generationMode"] = self.generation_mode
        visualizer_attrs_dict["computationResourceConfigure"] = self.computation_resource_configure
        visualizer_attrs_dict["llmModel"] = self.llm_model
        return visualizer_attrs_dict
