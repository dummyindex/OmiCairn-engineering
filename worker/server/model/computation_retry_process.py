from db import alchemy_db as db


class ComputationRetryProcess(db.Model):
    __tablename__ = 'computation_retry_process'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='Primary Key')
    node_id = db.Column(db.BigInteger, nullable=False, comment='Node ID')
    new_node_id = db.Column(
        db.BigInteger, nullable=True, comment='New Node ID')
    task_id = db.Column(db.BigInteger, nullable=False, comment='Task ID')
    analysis_id = db.Column(
        db.BigInteger, nullable=False, comment='Analysis ID')
    state = db.Column(db.String(100), nullable=False,
                      default='pending', comment='Status')
    max_retry = db.Column(db.Integer, nullable=False,
                          default=5, comment='Max Retry')
    rest_retry = db.Column(db.Integer, nullable=False,
                           default=5, comment='Rest Retry')
    user_id = db.Column(db.BigInteger, nullable=False, comment='User ID')
    created_time = db.Column(db.DateTime, nullable=False,
                             default=db.func.current_timestamp(), comment='Created Time')
    user_prompt = db.Column(
        db.Text, nullable=True, comment='User Prompt for the retry process')
    completed_time = db.Column(
        db.DateTime, nullable=True, comment='Completed Time')
    llm_model = db.Column(db.String(255))

    def to_dict(self):
        computation_retry_process_attrs_dict = dict()
        computation_retry_process_attrs_dict["id"] = self.id
        computation_retry_process_attrs_dict["nodeId"] = self.node_id
        computation_retry_process_attrs_dict["newNodeId"] = self.new_node_id
        computation_retry_process_attrs_dict["taskId"] = self.task_id
        computation_retry_process_attrs_dict["analysisId"] = self.analysis_id
        computation_retry_process_attrs_dict["state"] = self.state
        computation_retry_process_attrs_dict["maxRetry"] = self.max_retry
        computation_retry_process_attrs_dict["restRetry"] = self.rest_retry
        computation_retry_process_attrs_dict["userId"] = self.user_id
        computation_retry_process_attrs_dict["createdTime"] = None if self.created_time is None else self.created_time.strftime(
            "%Y-%m-%d %H:%M:%S")
        computation_retry_process_attrs_dict["userPrompt"] = self.user_prompt
        computation_retry_process_attrs_dict["completedTime"] = None if self.completed_time is None else self.completed_time.strftime(
            "%Y-%m-%d %H:%M:%S")
        computation_retry_process_attrs_dict["llmModel"] = self.llm_model
        return computation_retry_process_attrs_dict
