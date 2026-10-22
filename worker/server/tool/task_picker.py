from dao.node import node_dao
from dao.task_node_relation import task_node_relation_dao
from dao.task import task_dao
from dao.inform import inform_dao
from dao.computation import computation_dao
from constants.node import NodeState
from log.logger_factory import LoggerFactory
from model.inform import Inform
from constants.inform import InformType
from constants.authority import SpecialUserId
from datetime import datetime
import json
from constants.task import TaskState
from constants.task_node_relation import TaskNodeRelationType

logger = LoggerFactory.get_logger('TaskLockedPicker')

INTERVAL = 10


class TaskPicker:

    def query_all_running_task(self):
        running_task_list = task_dao.find_by_state(TaskState.RUNNING.value)
        return running_task_list if running_task_list is not None else []

    def check_if_task_running(self, task_id):
        task_node_relation_list = task_node_relation_dao.find_by_task_id_and_relation_type(
            task_id,
            TaskNodeRelationType.BELONG_TO.value
        )
        for task_node_relation in task_node_relation_list:
            node = node_dao.find_by_id(task_node_relation.node_id)
            if node is not None and node.state in (
                NodeState.RUNNING.value,
                NodeState.PENDING.value,
                NodeState.DEBUGGING.value
            ):
                return True
        return False

    def unlock_node_list_by_task(self, task_id):
        task_node_relation_list = task_node_relation_dao.find_by_task_id(
            task_id
        )
        for task_node_relation in task_node_relation_list:
            all_related_relations = task_node_relation_dao.find_by_node_id(
                task_node_relation.node_id
            )
            task_ids = [
                relation.task_id for relation in all_related_relations if relation.task_id != task_id]
            task_list = task_dao.find_by_ids_and_state(
                task_ids,
                TaskState.RUNNING.value
            )
            if len(task_list) == 0:
                node_dao.unlock_if_locked(task_node_relation.node_id)

    def unlock_node_list_without_task_node_relation(self):
        node_list = node_dao.find_locked_without_task_node_relation()
        for node in node_list:
            node_dao.unlock_if_locked(node.node_id)

    def scan(self):
        running_task_list = self.query_all_running_task()
        for task in running_task_list:
            task_is_running = self.check_if_task_running(task.id)
            if not task_is_running:
                # Notify the user
                now = datetime.now()
                task_user_relation_list = task_dao.find_user_relation_by_task_id(
                    task.id
                )
                computation_list = computation_dao.find_by_task_id(
                    task.id
                )
                for task_user_relation in task_user_relation_list:
                    inform = Inform(
                        sender_id=SpecialUserId.SYSTEM.value,
                        receiver_id=task_user_relation.user_id,
                        created_time=now,
                        have_read=False,
                        type=InformType.TASK_END_NOTICE.value,
                        payload=json.dumps({
                            "task_id": task.id,
                            "analysis_id": task.analysis_id,
                            "computation_list": [{
                                "computation_id": computation.id,
                                "start_time": computation.start_time.strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ) if computation.start_time is not None else None,
                                "duration": computation.duration,
                                "error_message": computation.error_description,
                                "node_id": computation.node_id,
                                "state": computation.computation_state
                            } for computation in computation_list],
                            "message": f"Task {task.id} is finished."
                        })
                    )
                    inform_dao.insert_inform(inform)
                logger.info(
                    f"Task {task.id} is not running, unlock all nodes")
                self.unlock_node_list_by_task(task.id)
                task_dao.update(
                    task.id,
                    {
                        "state": TaskState.STOPPED.value
                    }
                )
        # Find nodes that are locked but have no task_node_relation, and unlock them
        self.unlock_node_list_without_task_node_relation()


task_picker = TaskPicker()
