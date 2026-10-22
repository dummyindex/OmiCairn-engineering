from model.data import Data
from model.computation import Computation
from model.node import Node
from dao.data import data_dao
from dao.computation import computation_dao
from dao.node import node_dao
from constants.node import NodeState
from constants.data import CreatedFrom, DataState
from waiter.data_waiter import DataWaiter
from typing import List
from datetime import datetime, timedelta
from log.logger_factory import logger_factory

logger = logger_factory.create_logger(__name__)

class ScheduleService:
    def clear_data_in_s3(self, data_id: int):
        waiter = DataWaiter(data_id)
        waiter.remove_data()

    def bury_computations(self, computations: List[Computation]):
        for computation in computations:
            computation_dao.update(computation.id, {
                'buried': True
            })
            result_data_id = computation.result_data_id
            # set the data's buried field to true
            data_dao.update(result_data_id, {
                'buried': True
            })
            # delete the data in S3
            self.clear_data_in_s3(result_data_id)

    def clear_finished_node(self, computations: List[Computation]):
        # node computation finished, so earlier computation data is obsolete; delete it
        if len(computations) == 1:
            # only one computation task, nothing to clean up
            return 0
        self.bury_computations(computations[1:])
        return len(computations[1:])
            

    def clear_failed_node(self, computations: List[Computation]):
        # node computation failed, so earlier computation data is obsolete; delete it
        self.bury_computations(computations)
        return len(computations)

    def clear_running_node(self, computations: List[Computation]):
        # node is computing, so the current task has already been created; delete from the second one onward
        if len(computations) == 1:
            # only one computation task, nothing to clean up
            return 0
        self.bury_computations(computations[1:])
        return len(computations[1:])

    def clear_pending_node(self, computations: List[Computation]):
        # because of possible state-sync issues, keep the latest computation task to be safe
        if len(computations) == 1:
            # only one computation task, nothing to clean up
            return 0
        self.bury_computations(computations[1:])
        return len(computations[1:])

    def clear_orignal_node(self, computations: List[Computation]):
        # node in initial state, clean up all computation tasks
        self.bury_computations(computations)
        return len(computations)

    def clear_buried_data_by_computation(self):
        max_handle_count = 100
        handled_count = 0

        # clean up by node
        node_id_set = set()
        node_offset = 0
        node_limit = 200
        while handled_count < max_handle_count:
            node_list = node_dao.find_page(node_offset, node_limit)
            node_id_set.update([node.id for node in node_list])
            logger.info(f"node length: {len(node_list)}")
            for node in node_list:
                computations = computation_dao.find_not_buried_by_node_id(node.id)
                computations.sort(key=lambda x: x.created_time, reverse=True)
                if node.state == NodeState.ORIGINAL.value:
                    handled_count += self.clear_orignal_node(computations)
                elif node.state == NodeState.PENDING.value:
                    handled_count += self.clear_pending_node(computations)
                elif node.state == NodeState.RUNNING.value:
                    handled_count += self.clear_running_node(computations)
                elif node.state == NodeState.FAILED.value:
                    handled_count += self.clear_failed_node(computations)
                elif node.state == NodeState.FINISHED.value:
                    handled_count += self.clear_finished_node(computations)
            # start offset for the next iteration
            node_offset += node_limit
            if len(node_list) < node_limit:
                break
        # clean up by computation
        computation_offset = 0
        computation_limit = 200
        while handled_count < max_handle_count:
            computation_list = computation_dao.find_not_buried_with_page(computation_offset, computation_limit)
            logger.info(f"computation length: {len(computation_list)}")
            for computation in computation_list:
                if computation.node_id in node_id_set:
                    continue
                self.bury_computations([computation])
                handled_count += 1
            # start offset for the next iteration
            computation_offset += computation_limit
            if len(computation_list) < computation_limit:
                break
        return handled_count
    
    def clear_buried_data(self):
        max_handle_count = 100
        handled_count = 0
        offset = 0
        limit = 200
        while handled_count < max_handle_count:
            data_list = data_dao.find_isolated_and_not_buried_by_created_from_with_page(CreatedFrom.COMPUTATION.value, offset, limit)
            if len(data_list) > 0:
                data_dao.update_by_id_list([data.data_id for data in data_list], {
                    'buried': True
                })
                logger.info(f"data length: {len(data_list)}")
                for data in data_list:
                    self.clear_data_in_s3(data.data_id)
                    handled_count += 1
            offset += limit
            if len(data_list) < limit:
                break
        return handled_count

    def scan_uploading_timeout(self):
        data = data_dao.find_by_state(DataState.UPLOADING.value)
        handled_count = 0
        for d in data:
            if datetime.now() - d.created_time > timedelta(hours=1):
                data_dao.update(d.id, {
                    'state': DataState.ERROR.value,
                    'buried': True,
                    'error_message': 'uploading timeout'
                })
                handled_count += 1
        return handled_count
        
schedule_service = ScheduleService()