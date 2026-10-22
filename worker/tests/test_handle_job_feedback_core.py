"""
Unit tests for handle_job_feedback core functions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import json
import sys
import os

# Mock database before importing modules
with patch('sqlalchemy.create_engine'):
    with patch('sqlalchemy.orm.sessionmaker'):
        # Add the handle_job_feedback module to the path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'handle_job_feedback'))
        
        from handle_job_feedback.index import (
            optimize_error_description,
            update_node_state_to_error,
            report_fault,
            block_later_nodes,
            handle_failed,
            handle_success,
            retry_directly,
            count_folder_size,
            count_computation,
            count_data_size,
            handle_parent_node_replan_and_execution,
            _handle_fixer,
        )
        from handle_job_feedback.constants import (
            NodeType,
            NodeState,
            ComputationState,
            DataState,
            InformType,
            ComputationRetryProcessState,
        )


class TestOptimizeErrorDescription:
    """Test optimize_error_description function"""

    @patch('handle_job_feedback.index.ServerAgent')
    def test_optimize_error_description_success(self, mock_server_agent_class):
        """Test successful error description optimization"""
        mock_agent = Mock()
        mock_server_agent_class.return_value = mock_agent
        
        optimize_error_description("comp_123", "user_456")
        
        mock_server_agent_class.assert_called_once_with("user_456")
        mock_agent.optimize_error_message.assert_called_once_with("comp_123")

    @patch('handle_job_feedback.index.ServerAgent')
    @patch('handle_job_feedback.index.logger')
    def test_optimize_error_description_failure(self, mock_logger, mock_server_agent_class):
        """Test error description optimization with exception"""
        mock_agent = Mock()
        mock_agent.optimize_error_message.side_effect = Exception("API Error")
        mock_server_agent_class.return_value = mock_agent
        
        optimize_error_description("comp_123", "user_456")
        
        mock_logger.error.assert_called_once()


class TestUpdateNodeStateToError:
    """Test update_node_state_to_error function"""

    @patch('handle_job_feedback.index.update_node')
    def test_update_node_state_to_error_default(self, mock_update_node):
        """Test updating node state to error with default parameters"""
        update_node_state_to_error("node_123")
        
        mock_update_node.assert_called_once_with(
            "node_123",
            {
                "state": NodeState.FAILED.value,
                "locked": False,
                "is_review_error": False
            }
        )

    @patch('handle_job_feedback.index.update_node')
    def test_update_node_state_to_error_with_review_error(self, mock_update_node):
        """Test updating node state to error with review error"""
        update_node_state_to_error("node_123", is_review_error=True)
        
        mock_update_node.assert_called_once_with(
            "node_123",
            {
                "state": NodeState.FAILED.value,
                "locked": False,
                "is_review_error": True
            }
        )


class TestReportFault:
    """Test report_fault function"""

    @patch('handle_job_feedback.index.logger')
    def test_report_fault_with_no_node(self, mock_logger):
        """Test report_fault when node is None"""
        report_fault(node=None, task_owner_relation=Mock())
        
        mock_logger.error.assert_called_once()

    @patch('handle_job_feedback.index.ServerAgent')
    @patch('handle_job_feedback.index.find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id')
    def test_report_fault_with_running_branch(self, mock_find_branch, mock_server_agent_class):
        """Test report_fault with running dynamic generation branch"""
        mock_node = Mock()
        mock_node.id = "node_123"
        mock_node.dynamic_generation_id = "dg_456"
        mock_node.visualizer_id = None
        
        mock_branch = Mock()
        mock_branch.id = "branch_789"
        mock_branch.state = "running"
        mock_find_branch.return_value = mock_branch
        
        mock_task_owner = Mock()
        mock_task_owner.user_id = "user_123"
        
        mock_agent = Mock()
        mock_server_agent_class.return_value = mock_agent
        
        report_fault(node=mock_node, task_owner_relation=mock_task_owner)
        
        mock_agent.report_dynamic_generation_branch_done.assert_called_once_with("branch_789")

    @patch('handle_job_feedback.index.ServerAgent')
    @patch('handle_job_feedback.index.find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id')
    @patch('handle_job_feedback.index.find_visualizer_by_id')
    def test_report_fault_with_visualizer(self, mock_find_visualizer, mock_find_branch, mock_server_agent_class):
        """Test report_fault with visualizer"""
        mock_node = Mock()
        mock_node.id = "node_123"
        mock_node.dynamic_generation_id = "dg_456"
        mock_node.visualizer_id = "viz_789"
        
        mock_find_branch.return_value = None
        
        mock_visualizer = Mock()
        mock_visualizer.id = "viz_789"
        mock_visualizer.state = "running"
        mock_find_visualizer.return_value = mock_visualizer
        
        mock_task_owner = Mock()
        mock_task_owner.user_id = "user_123"
        
        mock_agent = Mock()
        mock_server_agent_class.return_value = mock_agent
        
        report_fault(node=mock_node, task_owner_relation=mock_task_owner)
        
        mock_agent.report_visualizer_step_done.assert_called_once_with("viz_789", "node_123", True)


class TestBlockLaterNodes:
    """Test block_later_nodes function"""

    @patch('handle_job_feedback.index.find_all_after_edges')
    @patch('handle_job_feedback.index.find_task_node_relations_by_task_id_and_relation_type')
    @patch('handle_job_feedback.index.update_node_batch')
    @patch('handle_job_feedback.index.delete_task_node_relations_by_task_id_and_node_id_list')
    @patch('handle_job_feedback.index.find_edges_by_target_node_id_list')
    @patch('handle_job_feedback.index.delete_task_edge_relations_by_task_id_and_edge_id_list')
    def test_block_later_nodes(self, mock_delete_edges, mock_find_edges, 
                               mock_delete_nodes, mock_update_batch, 
                               mock_find_relations, mock_find_after_edges):
        """Test blocking later nodes"""
        mock_computation = Mock()
        mock_computation.node_id = "node_123"
        
        mock_task = Mock()
        mock_task.id = "task_456"
        
        # Mock edges after this node
        mock_edge1 = Mock()
        mock_edge1.target_node_id = "node_2"
        mock_edge2 = Mock()
        mock_edge2.target_node_id = "node_3"
        mock_find_after_edges.return_value = [mock_edge1, mock_edge2]
        
        # Mock task node relations
        mock_relation1 = Mock()
        mock_relation1.node_id = "node_2"
        mock_relation2 = Mock()
        mock_relation2.node_id = "node_3"
        mock_relation3 = Mock()
        mock_relation3.node_id = "node_4"
        mock_find_relations.return_value = [mock_relation1, mock_relation2, mock_relation3]
        
        # Mock edges for deletion
        mock_edge_to_delete = Mock()
        mock_edge_to_delete.id = "edge_1"
        mock_find_edges.return_value = [mock_edge_to_delete]
        
        block_later_nodes(mock_computation, mock_task)
        
        # Verify node state update
        mock_update_batch.assert_called_once()
        update_call_args = mock_update_batch.call_args
        assert NodeState.ORIGINAL.value in str(update_call_args)
        
        # Verify node relations deletion
        mock_delete_nodes.assert_called_once()
        
        # Verify edge relations deletion
        mock_delete_edges.assert_called_once()


class TestHandleFailed:
    """Test handle_failed function"""

    @patch('handle_job_feedback.index.update_computation')
    @patch('handle_job_feedback.index.update_data')
    @patch('handle_job_feedback.index.update_node_state_to_error')
    @patch('handle_job_feedback.index.block_later_nodes')
    @patch('handle_job_feedback.index.report_fault')
    @patch('handle_job_feedback.index._handle_fixer')
    def test_handle_failed_computation_v2(self, mock_handle_fixer, mock_report_fault, 
                                          mock_block_later, mock_update_node_error, 
                                          mock_update_data, mock_update_computation):
        """Test handle_failed for computation node v2"""
        mock_computation = Mock()
        mock_computation.id = "comp_123"
        mock_computation.computation_state = ComputationState.RUNNING.value
        mock_computation.start_time = datetime.now()
        mock_computation.result_data_id = "data_123"
        
        mock_node = Mock()
        mock_node.id = "node_123"
        mock_node.type = NodeType.COMPUTATION_NODE_V2.value
        
        mock_task = Mock()
        mock_task_owner = Mock()
        mock_analysis = Mock()
        
        handle_failed(
            mock_computation,
            "Test error",
            False,
            mock_node,
            mock_task,
            mock_task_owner,
            mock_analysis
        )
        
        # Verify computation update
        mock_update_computation.assert_called_once()
        update_args = mock_update_computation.call_args[0]
        assert update_args[0] == "comp_123"
        
        # Verify data update
        mock_update_data.assert_called_once()
        
        # Verify fixer handling
        mock_handle_fixer.assert_called_once()
        
        # Verify node error state update
        mock_update_node_error.assert_called_once()
        
        # Verify block later nodes
        mock_block_later.assert_called_once()
        
        # Verify report fault
        mock_report_fault.assert_called_once()

    @patch('handle_job_feedback.index.update_computation')
    @patch('handle_job_feedback.index.update_data')
    @patch('handle_job_feedback.index.find_computation_retry_process_by_id')
    @patch('handle_job_feedback.index.BugFixerAgent')
    def test_handle_failed_with_bug_fixer(self, mock_bug_fixer_class, 
                                          mock_find_retry, mock_update_data, 
                                          mock_update_computation):
        """Test handle_failed with BugFixerAgent"""
        mock_computation = Mock()
        mock_computation.id = "comp_123"
        mock_computation.computation_state = ComputationState.RUNNING.value
        mock_computation.start_time = datetime.now()
        mock_computation.result_data_id = "data_123"
        mock_computation.retry_process_id = "retry_123"
        
        mock_node = Mock()
        mock_node.id = "node_123"
        mock_node.type = NodeType.COMPUTATION_NODE.value
        
        mock_task = Mock()
        mock_task_owner = Mock()
        mock_analysis = Mock()
        
        mock_retry_process = Mock()
        mock_find_retry.return_value = mock_retry_process
        
        mock_bug_fixer = Mock()
        mock_bug_fixer_class.return_value = mock_bug_fixer
        
        handle_failed(
            mock_computation,
            "Test error",
            False,
            mock_node,
            mock_task,
            mock_task_owner,
            mock_analysis
        )
        
        # Verify BugFixerAgent instantiation
        mock_bug_fixer_class.assert_called_once()
        
        # Verify handle method called
        mock_bug_fixer.handle.assert_called_once()

    @patch('handle_job_feedback.index.update_computation')
    @patch('handle_job_feedback.index.update_data')
    def test_handle_failed_cancelled_computation(self, mock_update_data, mock_update_computation):
        """Test handle_failed with cancelled computation"""
        mock_computation = Mock()
        mock_computation.computation_state = ComputationState.CANCELLED.value
        
        handle_failed(
            mock_computation,
            "Test error",
            False,
            Mock(),
            Mock(),
            Mock(),
            Mock()
        )
        
        # Should not update anything
        mock_update_computation.assert_not_called()
        mock_update_data.assert_not_called()


class TestRetryDirectly:
    """Test retry_directly function"""

    @patch('handle_job_feedback.index.BugFixerAgent')
    def test_retry_directly(self, mock_bug_fixer_class):
        """Test retry_directly function"""
        mock_computation = Mock()
        mock_computation.error_description = "Previous error"
        
        mock_node = Mock()
        mock_task = Mock()
        mock_task_owner = Mock()
        mock_analysis = Mock()
        
        mock_bug_fixer = Mock()
        mock_bug_fixer_class.return_value = mock_bug_fixer
        
        retry_directly(
            mock_computation,
            mock_node,
            mock_task,
            mock_task_owner,
            mock_analysis,
            "User prompt",
            llm_model="gpt-4",
            max_debug=5
        )
        
        # Verify BugFixerAgent instantiation with correct parameters
        call_args = mock_bug_fixer_class.call_args
        assert call_args[1]['user_prompt'] == "User prompt"
        assert call_args[1]['llm_model'] == "gpt-4"
        assert call_args[1]['max_debug'] == 5
        
        # Verify handle called with True
        mock_bug_fixer.handle.assert_called_once_with(True)


class TestHandleSuccess:
    """Test handle_success function"""

    @patch('handle_job_feedback.index.update_node')
    @patch('handle_job_feedback.index.update_computation')
    @patch('handle_job_feedback.index.update_data')
    @patch('handle_job_feedback.index.find_next_edges_in_task')
    def test_handle_success_basic(self, mock_find_edges, mock_update_data, 
                                  mock_update_computation, mock_update_node):
        """Test basic successful computation handling"""
        mock_computation = Mock()
        mock_computation.id = "comp_123"
        mock_computation.computation_state = ComputationState.RUNNING.value
        mock_computation.start_time = datetime.now()
        mock_computation.node_id = "node_123"
        mock_computation.result_data_id = "data_123"
        
        mock_node = Mock()
        mock_node.id = "node_123"
        mock_node.visualizer_id = None
        mock_node.dynamic_generation_id = None
        
        mock_task = Mock()
        mock_task_owner = Mock()
        mock_analysis = Mock()
        
        mock_find_edges.return_value = []
        
        handle_success(
            mock_computation,
            mock_node,
            mock_task,
            mock_task_owner,
            mock_analysis,
            True,
            None
        )
        
        # Verify node update
        mock_update_node.assert_called_once()
        update_node_args = mock_update_node.call_args[0]
        assert update_node_args[0] == "node_123"
        
        # Verify computation update
        mock_update_computation.assert_called_once()
        
        # Verify data update
        mock_update_data.assert_called_once()

    @patch('handle_job_feedback.index.update_node')
    @patch('handle_job_feedback.index.update_computation')
    @patch('handle_job_feedback.index.update_data')
    @patch('handle_job_feedback.index.find_next_edges_in_task')
    @patch('handle_job_feedback.index.find_node_by_id')
    @patch('handle_job_feedback.index.launch_computation')
    def test_handle_success_with_next_nodes(self, mock_launch, mock_find_node, 
                                            mock_find_edges, mock_update_data, 
                                            mock_update_computation, mock_update_node):
        """Test successful computation with next nodes"""
        mock_computation = Mock()
        mock_computation.id = "comp_123"
        mock_computation.computation_state = ComputationState.RUNNING.value
        mock_computation.start_time = datetime.now()
        mock_computation.node_id = "node_123"
        mock_computation.result_data_id = "data_123"
        mock_computation.task_id = "task_456"
        
        mock_node = Mock()
        mock_node.id = "node_123"
        mock_node.visualizer_id = None
        mock_node.dynamic_generation_id = None
        
        mock_next_edge = Mock()
        mock_next_edge.target_node_id = "node_next"
        mock_find_edges.return_value = [mock_next_edge]
        
        mock_next_node = Mock()
        mock_next_node.id = "node_next"
        mock_find_node.return_value = mock_next_node
        
        mock_task = Mock()
        mock_task_owner = Mock()
        mock_task_owner.user_id = "user_123"
        mock_analysis = Mock()
        
        handle_success(
            mock_computation,
            mock_node,
            mock_task,
            mock_task_owner,
            mock_analysis,
            True,
            None
        )
        
        # Verify next computation launched
        mock_launch.assert_called_once_with(
            node_id="node_next",
            user_id="user_123",
            task_id="task_456"
        )

    @patch('handle_job_feedback.index.update_node')
    @patch('handle_job_feedback.index.update_computation')
    @patch('handle_job_feedback.index.update_data')
    @patch('handle_job_feedback.index.find_next_edges_in_task')
    def test_handle_success_cancelled_computation(self, mock_find_edges, 
                                                  mock_update_data, 
                                                  mock_update_computation, 
                                                  mock_update_node):
        """Test handle_success with cancelled computation"""
        mock_computation = Mock()
        mock_computation.computation_state = ComputationState.CANCELLED.value
        
        handle_success(
            mock_computation,
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            True,
            None
        )
        
        # Should not update anything
        mock_update_node.assert_not_called()
        mock_update_computation.assert_not_called()
        mock_update_data.assert_not_called()


class TestCountFunctions:
    """Test count_folder_size, count_computation, and count_data_size functions"""

    @patch('handle_job_feedback.index.PorterFactory')
    def test_count_folder_size_single_page(self, mock_porter_factory):
        """Test counting folder size with single page"""
        mock_porter = Mock()
        mock_porter_factory.create_porter.return_value = mock_porter
        
        mock_porter.list_file_infos.return_value = {
            'Contents': [
                {'Size': 1024, 'Key': 'file1.txt'},
                {'Size': 2048, 'Key': 'file2.txt'},
            ],
            'IsTruncated': False
        }
        
        size = count_folder_size("test_folder/")
        
        assert size == 3072
        mock_porter.list_file_infos.assert_called_once()

    @patch('handle_job_feedback.index.PorterFactory')
    def test_count_folder_size_multiple_pages(self, mock_porter_factory):
        """Test counting folder size with pagination"""
        mock_porter = Mock()
        mock_porter_factory.create_porter.return_value = mock_porter
        
        # First page
        mock_porter.list_file_infos.side_effect = [
            {
                'Contents': [
                    {'Size': 1024, 'Key': 'file1.txt'},
                ],
                'IsTruncated': True,
                'NextContinuationToken': 'token1'
            },
            # Second page
            {
                'Contents': [
                    {'Size': 2048, 'Key': 'file2.txt'},
                ],
                'IsTruncated': False
            }
        ]
        
        size = count_folder_size("test_folder/")
        
        assert size == 3072
        assert mock_porter.list_file_infos.call_count == 2

    @patch('handle_job_feedback.index.PorterFactory')
    @patch('handle_job_feedback.index.count_folder_size')
    def test_count_computation(self, mock_count_folder, mock_porter_factory):
        """Test counting computation sizes"""
        mock_porter = Mock()
        mock_porter_factory.create_porter.return_value = mock_porter
        
        # Mock head responses for different files
        mock_porter.get_head.side_effect = [
            {"ContentLength": 1024},  # report
            {"ContentLength": 2048},  # log
            {"ContentLength": 512},   # result
            {"ContentLength": 256},   # review_error
            {"ContentLength": 128},   # options
        ]
        
        # Mock output folder size
        mock_count_folder.return_value = 4096
        
        result = count_computation("comp_123")
        
        assert result["report_size"] == 1024
        assert result["log_size"] == 2048
        assert result["result_size"] == 512
        assert result["review_error_size"] == 256
        assert result["options_size"] == 128
        assert result["output_size"] == 4096

    @patch('handle_job_feedback.index.PorterFactory')
    @patch('handle_job_feedback.index.count_folder_size')
    def test_count_data_size(self, mock_count_folder, mock_porter_factory):
        """Test counting data size"""
        mock_porter = Mock()
        mock_porter_factory.create_porter.return_value = mock_porter
        
        # Mock h5ad file head
        mock_porter.get_head.return_value = {"ContentLength": 5120}
        
        # Mock components folder size
        mock_count_folder.return_value = 2048
        
        size = count_data_size("data_123")
        
        assert size == 7168  # 5120 + 2048


class TestHandleParentNodeReplanAndExecution:
    """Test handle_parent_node_replan_and_execution function"""

    @patch('handle_job_feedback.index.find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id')
    @patch('handle_job_feedback.index.find_dynamic_generation_by_id')
    @patch('handle_job_feedback.index.ServerAgent')
    def test_handle_parent_node_replan_no_rest_nodes(self, mock_server_agent_class, 
                                                     mock_find_dg, mock_find_branch):
        """Test handle_parent_node_replan when no rest nodes"""
        mock_node = Mock()
        mock_node.dynamic_generation_id = "dg_123"
        mock_node.id = "node_456"
        
        mock_branch = Mock()
        mock_branch.id = "branch_789"
        mock_find_branch.return_value = mock_branch
        
        mock_dg = Mock()
        mock_dg.rest_node_count = 0
        mock_find_dg.return_value = mock_dg
        
        mock_task_owner = Mock()
        mock_task_owner.user_id = "user_123"
        
        mock_agent = Mock()
        mock_server_agent_class.return_value = mock_agent
        
        handle_parent_node_replan_and_execution(
            mock_node,
            mock_task_owner,
            Mock()
        )
        
        # Should report branch done
        mock_agent.report_dynamic_generation_branch_done.assert_called_once_with("branch_789")

    @patch('handle_job_feedback.index.find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id')
    @patch('handle_job_feedback.index.find_dynamic_generation_by_id')
    @patch('handle_job_feedback.index.find_previous_node_by_node_id')
    @patch('handle_job_feedback.index.find_node_by_replan_source_id')
    @patch('handle_job_feedback.index.ServerAgent')
    def test_handle_parent_node_replan_limit_reached(self, mock_server_agent_class,
                                                     mock_find_by_replan, mock_find_prev,
                                                     mock_find_dg, mock_find_branch):
        """Test handle_parent_node_replan when replan limit reached"""
        mock_node = Mock()
        mock_node.dynamic_generation_id = "dg_123"
        mock_node.id = "node_456"
        mock_node.replan_source_id = "replan_source"
        
        mock_branch = Mock()
        mock_branch.id = "branch_789"
        mock_find_branch.return_value = mock_branch
        
        mock_dg = Mock()
        mock_dg.rest_node_count = 5
        mock_dg.replan_count_limit = 2
        mock_find_dg.return_value = mock_dg
        
        mock_parent = Mock()
        mock_parent.id = "parent_node"
        mock_find_prev.return_value = mock_parent
        
        # Return 2 replanned nodes (limit reached)
        mock_find_by_replan.return_value = [Mock(), Mock()]
        
        mock_task_owner = Mock()
        mock_task_owner.user_id = "user_123"
        
        mock_agent = Mock()
        mock_server_agent_class.return_value = mock_agent
        
        handle_parent_node_replan_and_execution(
            mock_node,
            mock_task_owner,
            Mock()
        )
        
        # Should report branch done without replanning
        mock_agent.report_dynamic_generation_branch_done.assert_called_once_with("branch_789")


class TestHandleFixer:
    """Test _handle_fixer function"""

    @patch('handle_job_feedback.index.handle_parent_node_replan_and_execution')
    def test_handle_fixer_already_enabled(self, mock_replan):
        """Test _handle_fixer when code agent already enabled"""
        mock_computation = Mock()
        mock_computation.enable_code_agent = True
        
        _handle_fixer(
            Mock(),
            Mock(),
            Mock(),
            mock_computation,
            Mock()
        )
        
        # Should call replan
        mock_replan.assert_called_once()

    @patch('handle_job_feedback.index.ServerAgent')
    @patch('handle_job_feedback.index.find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id')
    @patch('handle_job_feedback.index.DynamicGenerationWaiter')
    @patch('handle_job_feedback.index.insert_task_edge_relation')
    @patch('handle_job_feedback.index.insert_task_node_relation')
    @patch('handle_job_feedback.index.launch_computation')
    def test_handle_fixer_with_dynamic_generation(self, mock_launch, mock_insert_node,
                                                  mock_insert_edge, mock_waiter_class,
                                                  mock_find_branch, mock_server_agent_class):
        """Test _handle_fixer with dynamic generation"""
        mock_analysis = Mock()
        
        mock_dg = Mock()
        mock_dg.generation_id = "dg_123"
        mock_dg.state = "running"
        mock_dg.max_debug = 3
        mock_dg.llm_model = "gpt-4"
        
        mock_node = Mock()
        mock_node.id = "node_123"
        
        mock_computation = Mock()
        mock_computation.enable_code_agent = False
        mock_computation.task_id = "task_456"
        
        mock_task_owner = Mock()
        mock_task_owner.user_id = "user_123"
        mock_task_owner.task_id = "task_456"
        
        mock_agent = Mock()
        mock_agent.copy_node.return_value = {
            "data": {
                "id": "new_node",
                "previousEdges": [{"id": "edge_1"}]
            }
        }
        mock_server_agent_class.return_value = mock_agent
        
        mock_branch = Mock()
        mock_branch.id = "old_branch"
        mock_find_branch.return_value = mock_branch
        
        mock_waiter = Mock()
        mock_waiter.retrieve_plan.return_value = {"test": "plan"}
        mock_waiter_class.return_value = mock_waiter
        
        _handle_fixer(
            mock_analysis,
            mock_dg,
            mock_node,
            mock_computation,
            mock_task_owner
        )
        
        # Verify node copy
        mock_agent.copy_node.assert_called_once_with("node_123", with_edges=True)
        
        # Verify branch creation
        mock_agent.create_dynamic_generation_branch.assert_called_once()
        
        # Verify old branch done
        mock_agent.report_dynamic_generation_branch_done.assert_called_once_with("old_branch")
        
        # Verify computation launch with code agent
        mock_launch.assert_called_once()
        launch_args = mock_launch.call_args[1]
        assert launch_args['code_agent_config']['enable'] is True
        assert launch_args['code_agent_config']['max_attempts'] == 3
        assert launch_args['code_agent_config']['model'] == "gpt-4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
