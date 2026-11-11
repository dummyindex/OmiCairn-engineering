from dao.edge import edge_dao
from dao.node import node_dao
from dao.task_node_relation import task_node_relation_dao
from dao.task import task_dao
from constants.node import NodeState
from threading import Lock, Thread
from datetime import datetime
import time
from log.logger_factory import LoggerFactory
from db import alchemy_db
from dao.task import TaskState
from constants.task_node_relation import TaskNodeRelationType

logger = LoggerFactory.get_logger('TaskLockedPicker')

INTERVAL = 10


class TaskLockedPicker:
    def __init__(self) -> None:
        self.app = None
        self.daemon_thread = Thread(target=self.loop)
        self.daemon_thread.daemon = True
        self.daemon_thread.start()

    def set_app(self, app):
        self.app = app

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
            if node.state in (
                NodeState.RUNNING.value,
                NodeState.PENDING.value
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

    def unlock_node_list_with_stopped_task(self):
        node_list = node_dao.find_locked_with_stopped_task()
        for node in node_list:
            node_dao.unlock_if_locked(node.node_id)

    def loop(self):
        while True:
            if self.app is None:
                logger.info("Waiting for app to be set")
                time.sleep(3)
            else:
                break
        logger.info("TaskLockedPicker start running")
        while True:
            try:
                with self.app.app_context():
                    running_task_list = self.query_all_running_task()
                    for task in running_task_list:
                        task_is_running = self.check_if_task_running(task.id)
                        if not task_is_running:
                            logger.info(
                                f"Task {task.id} is not running, unlock all nodes")
                            self.unlock_node_list_by_task(task.id)
                            task_dao.update(
                                task.id,
                                {
                                    "state": TaskState.STOPPED.value
                                }
                            )
                    # Find nodes that are locked and have no task_node_relation, and unlock them
                    self.unlock_node_list_without_task_node_relation()
                    alchemy_db.session.commit()
            except Exception as e:
                logger.error(e)
            finally:
                time.sleep(INTERVAL)


task_locked_picker = TaskLockedPicker()
