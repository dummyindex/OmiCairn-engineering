from db import alchemy_db as db

class AgentSession(db.Model):
    __tablename__ = 'agent_session'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='primary key')
    agent_type = db.Column(db.String(64), nullable=False,
                           comment='agent type')
    status = db.Column(db.String(32), nullable=False,
                       comment='status')
    current_node_id = db.Column(db.BigInteger, nullable=True,
                                comment='current node ID')
    current_analysis_id = db.Column(db.BigInteger, nullable=True,
                                    comment='current analysis ID')
    current_computation_id = db.Column(db.BigInteger, nullable=True,
                                       comment='current computation ID')
    consumption_id = db.Column(db.BigInteger, nullable=True,
                               comment='consumption ID')
    created_time = db.Column(db.DateTime, nullable=False,
                             default=db.func.current_timestamp(),
                             comment='creation time')

    def to_dict(self):
        agent_session_attrs_dict = dict()
        agent_session_attrs_dict["id"] = self.id
        agent_session_attrs_dict["agentType"] = self.agent_type
        agent_session_attrs_dict["status"] = self.status
        agent_session_attrs_dict["currentNodeId"] = self.current_node_id
        agent_session_attrs_dict["currentAnalysisId"] = self.current_analysis_id
        agent_session_attrs_dict["currentComputationId"] = self.current_computation_id
        agent_session_attrs_dict["consumptionId"] = self.consumption_id
        agent_session_attrs_dict["createdTime"] = self.created_time.timestamp() * 1000
        return agent_session_attrs_dict