from db import alchemy_db as db


class Computation(db.Model):
    __tablename__ = 'computation'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    computation_params = db.Column(db.Text)
    created_time = db.Column(db.DateTime)
    start_time = db.Column(db.DateTime)
    duration = db.Column(db.Double)
    computation_state = db.Column(db.String(255))
    node_id = db.Column(db.BigInteger)
    source_data_ids = db.Column(db.String(255))
    result_data_id = db.Column(db.BigInteger)
    function_block_id = db.Column(db.BigInteger)
    function_block_version_id = db.Column(db.BigInteger)
    task_id = db.Column(db.BigInteger)
    error_description = db.Column(db.Text)
    job_ident = db.Column(db.String(200))
    optimized_error_description = db.Column(db.Text)
    buried = db.Column(db.Boolean)
    system_env = db.Column(db.String(100))
    computation_resource_configure = db.Column(db.String(200))
    previous_computation_id = db.Column(db.BigInteger)
    retry_process_id = db.Column(db.BigInteger)
    enable_code_agent = db.Column(db.Boolean, default=False)
    is_review_error = db.Column(db.Boolean, default=False)

    def to_dict(self):
        computation_attrs_dict = dict()
        computation_attrs_dict["id"] = self.id
        computation_attrs_dict["computationParams"] = self.computation_params
        computation_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000 if self.created_time is not None else None
        computation_attrs_dict["startTime"] = self.start_time.timestamp(
        ) * 1000 if self.start_time is not None else None
        computation_attrs_dict["duration"] = self.duration
        computation_attrs_dict["computationState"] = self.computation_state
        computation_attrs_dict["nodeId"] = self.node_id
        computation_attrs_dict["sourceDataIds"] = self.source_data_ids
        computation_attrs_dict["resultDataId"] = self.result_data_id
        computation_attrs_dict["functionBlockId"] = self.function_block_id
        computation_attrs_dict["functionBlockVersionId"] = self.function_block_version_id
        computation_attrs_dict["taskId"] = self.task_id
        computation_attrs_dict["errorDescription"] = self.error_description
        computation_attrs_dict["jobIdent"] = self.job_ident
        computation_attrs_dict["optimizedErrorDescription"] = self.optimized_error_description
        computation_attrs_dict["buried"] = self.buried
        computation_attrs_dict["systemEnv"] = self.system_env
        computation_attrs_dict["computationResourceConfigure"] = self.computation_resource_configure
        computation_attrs_dict["previousComputationId"] = self.previous_computation_id
        computation_attrs_dict["retryProcessId"] = self.retry_process_id
        computation_attrs_dict["enableCodeAgent"] = self.enable_code_agent
        computation_attrs_dict["isReviewError"] = self.is_review_error
        return computation_attrs_dict
