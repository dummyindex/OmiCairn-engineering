from model.node import Node
from model.task_node_relation import TaskNodeRelation
from model.task import Task
from model.edge import Edge
from constants.task import TaskState
from db import alchemy_db
from typing import List
from sqlalchemy import and_
from log.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger('TaskLockedPicker')


class NodeDao:
    def insert(self, node: Node):
        alchemy_db.session.add(node)
        alchemy_db.session.flush()
        return node

    def insert_list(self, node_list: List[Node]):
        alchemy_db.session.bulk_save_objects(node_list)
        alchemy_db.session.flush()
        return node_list

    def find_by_id(self, node_id) -> Node:
        return Node.query.filter(Node.id == node_id).first()

    def find_by_state(self, state: str) -> List[Node]:
        return Node.query.filter(Node.state == state).all()

    def find_by_analysis_id(self, analysis_id) -> List[Node]:
        return Node.query.filter(Node.analysis_id == analysis_id).all()

    def find_by_id_list(self, node_id_list) -> List[Node]:
        return Node.query.filter(Node.id.in_(node_id_list)).all()

    def find_locked_without_task_node_relation(self) -> List[Node]:
        # Use a join
        q = alchemy_db.session.query(
            Node.id.label("node_id"),
            TaskNodeRelation.id.label("task_node_relation_id")
        ).join(
            TaskNodeRelation,
            TaskNodeRelation.node_id == Node.id,
            isouter=True
        ).filter(
            and_(
                Node.locked == True,
                TaskNodeRelation.id == None
            )
        )
        # Print the SQL
        logger.debug(q.statement.compile(
            compile_kwargs={"literal_binds": True}))
        return q.all()
    
    def find_branch_path(self, node_id) -> List[Node]:
        path: List[Node] = []
        next_edge_path: List[Edge] = Edge.query.filter(Edge.target_node_id == node_id).all()
        for edge in next_edge_path:
            path.append(self.find_by_id(edge.source_node_id))
        index = 0
        while index < len(next_edge_path):
            next_edge = next_edge_path[index]
            edges = Edge.query.filter(
                Edge.target_node_id == next_edge.source_node_id
            ).all()
            next_edge_path += edges
            for edge in edges:
                path.append(self.find_by_id(edge.source_node_id))
            index += 1
        path.reverse()
        next_edge_path.reverse()
        return path, next_edge_path

    def find_locked_with_stopped_task(self) -> List[Node]:
        from model.task import Task
        from constants.task import TaskState
        # Find locked nodes whose associated tasks are all stopped
        q = alchemy_db.session.query(
            Node.id.label("node_id")
        ).join(
            TaskNodeRelation,
            TaskNodeRelation.node_id == Node.id
        ).join(
            Task,
            Task.id == TaskNodeRelation.task_id
        ).filter(
            Node.locked == True
        ).group_by(
            Node.id
        ).having(
            alchemy_db.func.count(
                alchemy_db.case(
                    (Task.state == TaskState.RUNNING.value, 1)
                )
            ) == 0
        )
        logger.debug(q.statement.compile(
            compile_kwargs={"literal_binds": True}))
        return q.all()

    def update(self, node_id, attrs: dict):
        Node.query.filter(Node.id == node_id).update(attrs)
        alchemy_db.session.flush()

    def update_by_id_list(self, node_id_list, attrs: dict):
        # Sort node IDs so all transactions lock resources in the same order, avoiding deadlocks
        sorted_node_ids = sorted(node_id_list) if node_id_list else []
        if not sorted_node_ids:
            return

        Node.query.filter(Node.id.in_(sorted_node_ids)).update(attrs)
        alchemy_db.session.flush()

    def unlock_if_locked(self, node_id):
        Node.query.filter(
            and_(
                Node.id == node_id,
                Node.locked == True
            )
        ).update(
            {
                "locked": False
            }
        )
        alchemy_db.session.flush()

    def find_by_dynamic_generation_id(self, generation_id):
        return Node.query.filter(Node.dynamic_generation_id == generation_id).all()

    def unlock_dynamic_generation_by_nodes(self, node_id_list):
        # Sort node IDs so all transactions lock resources in the same order, avoiding deadlocks
        # Even with only 2 concurrent transactions, inconsistent lock order can cause a deadlock
        sorted_node_ids = sorted(node_id_list) if node_id_list else []
        if not sorted_node_ids:
            return

        Node.query.filter(Node.id.in_(sorted_node_ids)).update(
            {
                "dynamic_generation_locked": False
            }
        )
        alchemy_db.session.flush()

    def force_unlock_all_nodes(self):
        """
        Force-unlock all nodes; used for initialization after a server restart
        Resolves lock anomalies
        """
        try:
            # Use SQLAlchemy's text() to execute raw SQL
            from sqlalchemy import text
            alchemy_db.session.execute(text("""
                UPDATE node SET 
                    locked = FALSE,
                    dynamic_generation_locked = FALSE,
                    visualizer_locked = FALSE
                WHERE locked = TRUE 
                   OR dynamic_generation_locked = TRUE 
                   OR visualizer_locked = TRUE
            """))
            alchemy_db.session.flush()
            logger.info("Successfully force unlocked all nodes via DAO")
        except Exception as e:
            logger.error(f"Failed to force unlock all nodes: {e}")
            alchemy_db.session.rollback()
            raise e

    def find_by_dynamic_generation_session_id(self, session_id):
        return Node.query.filter(Node.dynamic_generation_session_id == session_id).all()


node_dao = NodeDao()
