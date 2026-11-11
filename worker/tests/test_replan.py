"""
Unit tests for replan-related logic and functions in omicairn-worker.
Tests the replan functionality including parent node replan, dynamic generation with plan,
and replan count limit enforcement.
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

try:
    from handle_job_feedback.db import (
        Node,
        DynamicGeneration,
        DynamicGenerationBranch,
        TaskUserRelation,
        Analysis,
    )
    from handle_job_feedback.utils import handle_parent_node_replan
    from handle_job_feedback.index import handle_parent_node_replan_and_execution
    from handle_job_feedback.bug_fixer_agent import BugFixerAgent
    from handle_job_feedback.dynamic_generation_agent import DynamicGenerationAgent
except Exception as exc:  # pragma: no cover - depends on worker runtime deps
    # Do not skip the whole module: tests that need these names fail on their own,
    # while import-independent tests (e.g. TestReplanDatabaseLogic) still run.
    HANDLE_JOB_FEEDBACK_IMPORT_ERROR = exc


class TestReplanDatabaseLogic:
    """Test database functions related to replan."""
    
    def test_find_node_by_replan_source_id_with_results(self):
        """Test finding nodes by replan_source_id when results exist."""
        with patch('handle_job_feedback.db.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value.__enter__.return_value = mock_session
            
            # Mock nodes with replan_source_id
            mock_node1 = Mock()
            mock_node1.id = 1
            mock_node1.replan_source_id = 100
            mock_node2 = Mock()
            mock_node2.id = 2
            mock_node2.replan_source_id = 100
            
            mock_query = mock_session.query.return_value
            mock_filter = mock_query.filter.return_value
            mock_filter.all.return_value = [mock_node1, mock_node2]
            
            # Import after mocking
            from handle_job_feedback.db import find_node_by_replan_source_id
            result = find_node_by_replan_source_id(100)
            
            assert len(result) == 2
            assert result[0].id == 1
            assert result[1].id == 2
    
    def test_find_node_by_replan_source_id_with_none(self):
        """Test finding nodes by replan_source_id when input is None."""
        from handle_job_feedback.db import find_node_by_replan_source_id
        result = find_node_by_replan_source_id(None)
        
        assert result == []
    
    def test_find_node_by_replan_source_id_no_results(self):
        """Test finding nodes by replan_source_id when no results exist."""
        with patch('handle_job_feedback.db.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value.__enter__.return_value = mock_session
            
            mock_query = mock_session.query.return_value
            mock_filter = mock_query.filter.return_value
            mock_filter.all.return_value = []
            
            from handle_job_feedback.db import find_node_by_replan_source_id
            result = find_node_by_replan_source_id(100)
            
            assert result == []


class TestLlmInterfaceReplan:
    """Test LlmInterface replan methods."""
    
    def test_dynamic_fb_replan_success(self, mock_requests):
        """Test successful dynamic_fb_replan API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "name": "New Plan",
                "steps": "Step 1: Process data\nStep 2: Analyze results"
            },
            "consumption": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            },
            "message": '{"name": "New Plan", "steps": "Step 1: Process data\\nStep 2: Analyze results"}'
        }
        mock_requests['post'].return_value = mock_response
        
        from handle_job_feedback.llm_interface import LlmInterface
        llm_interface = LlmInterface()
        response = llm_interface.dynamic_fb_replan(
            user_id="user_123",
            node_id=1,
            user_request="Replan the analysis workflow",
            node_context={"inputs": ["data1.csv"], "outputs": []},
            error_description="Previous step failed due to memory error",
            current_plan={"name": "Old Plan", "steps": "Step 1: Load data"},
            llm_model="gpt-4",
            file_list=["file1.txt", "file2.csv"]
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        
        call_args = mock_requests['post'].call_args
        assert "dynamic_fb_plan/replan" in call_args[0][0]
        
        payload = call_args[1]['json']
        assert payload['user_id'] == "user_123"
        assert payload['node_id'] == 1
        assert payload['user_request'] == "Replan the analysis workflow"
        assert payload['error_description'] == "Previous step failed due to memory error"
        assert payload['current_plan'] == {"name": "Old Plan", "steps": "Step 1: Load data"}
        assert payload['llm_model'] == "gpt-4"
        assert payload['file_list'] == ["file1.txt", "file2.csv"]
    
    def test_dynamic_fb_replan_without_optional_params(self, mock_requests):
        """Test dynamic_fb_replan API call without optional parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"name": "New Plan", "steps": "Step 1"},
            "message": '{"name": "New Plan", "steps": "Step 1"}'
        }
        mock_requests['post'].return_value = mock_response
        
        from handle_job_feedback.llm_interface import LlmInterface
        llm_interface = LlmInterface()
        response = llm_interface.dynamic_fb_replan(
            user_id="user_123",
            node_id=1,
            user_request="Replan workflow",
            node_context={},
            error_description="Error occurred"
        )
        
        assert response.status_code == 200
        call_args = mock_requests['post'].call_args
        payload = call_args[1]['json']
        
        assert 'llm_model' not in payload
        assert payload['file_list'] == []
        assert payload['current_plan'] is None
    
    def test_dynamic_fb_replan_api_error(self, mock_requests):
        """Test dynamic_fb_replan API call when server returns error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_requests['post'].return_value = mock_response
        
        from handle_job_feedback.llm_interface import LlmInterface
        llm_interface = LlmInterface()
        response = llm_interface.dynamic_fb_replan(
            user_id="user_123",
            node_id=1,
            user_request="Replan workflow",
            node_context={},
            error_description="Error occurred"
        )
        
        assert response.status_code == 500


class TestHandleParentNodeReplan:
    """Test handle_parent_node_replan function."""
    
    @patch('handle_job_feedback.utils.insert_consumption')
    @patch('handle_job_feedback.utils.insert_session')
    @patch('handle_job_feedback.utils.find_latest_computation_by_node_id')
    @patch('handle_job_feedback.utils.DynamicGenerationWaiter')
    @patch('handle_job_feedback.utils.LlmInterface')
    @patch('handle_job_feedback.utils._build_node_context')
    @patch('handle_job_feedback.utils.validate_dynamic_generation_plan_output_json')
    def test_handle_parent_node_replan_success(
        self,
        mock_validate_json,
        mock_build_context,
        mock_llm_interface_cls,
        mock_waiter_cls,
        mock_find_computation,
        mock_insert_session,
        mock_insert_consumption
    ):
        """Test successful parent node replan."""
        # Setup mocks
        parent_node = Mock(spec=Node)
        parent_node.id = 1
        
        dynamic_generation = Mock(spec=DynamicGeneration)
        dynamic_generation.generation_id = "gen_123"
        dynamic_generation.user_request = "Perform RNA-seq analysis"
        dynamic_generation.llm_model = "gpt-4"
        
        mock_build_context.return_value = {
            "inputs": ["data.csv"],
            "outputs": []
        }
        
        mock_waiter = Mock()
        mock_waiter.retrieve_plan.return_value = {
            "name": "Old Plan",
            "steps": "Step 1: Load data"
        }
        mock_waiter.get_files.return_value = ["file1.txt"]
        mock_waiter_cls.return_value = mock_waiter
        
        mock_computation = Mock()
        mock_computation.error_description = "Memory allocation failed"
        mock_find_computation.return_value = mock_computation
        
        mock_llm_interface = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "consumption": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            },
            "message": '{"name": "Revised Plan", "steps": "Step 1: Load data with chunking"}',
            "data": {
                "name": "Revised Plan",
                "steps": "Step 1: Load data with chunking"
            }
        }
        mock_llm_interface.dynamic_fb_replan.return_value = mock_response
        mock_llm_interface_cls.return_value = mock_llm_interface
        
        mock_validate_json.return_value = (True, [])
        
        mock_consumption = Mock()
        mock_consumption.id = 100
        mock_insert_consumption.return_value = mock_consumption
        
        # Execute
        result = handle_parent_node_replan(
            user_id="user_123",
            node_id=2,
            parent_node=parent_node,
            dynamic_generation=dynamic_generation
        )
        
        # Verify
        assert result is not None
        assert result['name'] == "Revised Plan"
        assert result['steps'] == "Step 1: Load data with chunking"
        
        mock_llm_interface.dynamic_fb_replan.assert_called_once()
        mock_insert_consumption.assert_called_once()
        mock_insert_session.assert_called()
    
    @patch('handle_job_feedback.utils.insert_session')
    @patch('handle_job_feedback.utils.find_latest_computation_by_node_id')
    @patch('handle_job_feedback.utils.DynamicGenerationWaiter')
    @patch('handle_job_feedback.utils.LlmInterface')
    @patch('handle_job_feedback.utils._build_node_context')
    def test_handle_parent_node_replan_llm_error_with_retry(
        self,
        mock_build_context,
        mock_llm_interface_cls,
        mock_waiter_cls,
        mock_find_computation,
        mock_insert_session
    ):
        """Test parent node replan with LLM error and retry."""
        parent_node = Mock(spec=Node)
        parent_node.id = 1
        
        dynamic_generation = Mock(spec=DynamicGeneration)
        dynamic_generation.generation_id = "gen_123"
        dynamic_generation.user_request = "Perform analysis"
        dynamic_generation.llm_model = "gpt-4"
        
        mock_build_context.return_value = {}
        
        mock_waiter = Mock()
        mock_waiter.retrieve_plan.return_value = {}
        mock_waiter.get_files.return_value = []
        mock_waiter_cls.return_value = mock_waiter
        
        mock_find_computation.return_value = None
        
        mock_llm_interface = Mock()
        # First call raises exception, second succeeds
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "consumption": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            "message": '{"name": "Plan", "steps": "Step 1"}',
            "data": {"name": "Plan", "steps": "Step 1"}
        }
        
        mock_llm_interface.dynamic_fb_replan.side_effect = [
            Exception("Connection timeout"),
            mock_response_success
        ]
        mock_llm_interface_cls.return_value = mock_llm_interface
        
        with patch('handle_job_feedback.utils.validate_dynamic_generation_plan_output_json', return_value=(True, [])), \
             patch('handle_job_feedback.utils.insert_consumption', return_value=Mock(id=100)):
            result = handle_parent_node_replan(
                user_id="user_123",
                node_id=2,
                parent_node=parent_node,
                dynamic_generation=dynamic_generation
            )
        
        # Should succeed after retry
        assert result is not None
        assert result['name'] == "Plan"
        assert mock_llm_interface.dynamic_fb_replan.call_count == 2
        # Error session should be inserted for failed attempt
        assert mock_insert_session.call_count >= 1
    
    @patch('handle_job_feedback.utils.insert_session')
    @patch('handle_job_feedback.utils.find_latest_computation_by_node_id')
    @patch('handle_job_feedback.utils.DynamicGenerationWaiter')
    @patch('handle_job_feedback.utils.LlmInterface')
    @patch('handle_job_feedback.utils._build_node_context')
    def test_handle_parent_node_replan_max_retry_exceeded(
        self,
        mock_build_context,
        mock_llm_interface_cls,
        mock_waiter_cls,
        mock_find_computation,
        mock_insert_session
    ):
        """Test parent node replan when max retry is exceeded."""
        parent_node = Mock(spec=Node)
        parent_node.id = 1
        
        dynamic_generation = Mock(spec=DynamicGeneration)
        dynamic_generation.generation_id = "gen_123"
        dynamic_generation.user_request = "Perform analysis"
        dynamic_generation.llm_model = "gpt-4"
        
        mock_build_context.return_value = {}
        
        mock_waiter = Mock()
        mock_waiter.retrieve_plan.return_value = {}
        mock_waiter.get_files.return_value = []
        mock_waiter_cls.return_value = mock_waiter
        
        mock_find_computation.return_value = None
        
        mock_llm_interface = Mock()
        mock_llm_interface.dynamic_fb_replan.side_effect = Exception("Connection timeout")
        mock_llm_interface_cls.return_value = mock_llm_interface
        
        result = handle_parent_node_replan(
            user_id="user_123",
            node_id=2,
            parent_node=parent_node,
            dynamic_generation=dynamic_generation
        )
        
        # Should return empty list after max retries
        assert result == []
        # Should attempt 10 times (max_retry)
        assert mock_llm_interface.dynamic_fb_replan.call_count == 10
    
    @patch('handle_job_feedback.utils.insert_consumption')
    @patch('handle_job_feedback.utils.insert_session')
    @patch('handle_job_feedback.utils.find_latest_computation_by_node_id')
    @patch('handle_job_feedback.utils.DynamicGenerationWaiter')
    @patch('handle_job_feedback.utils.LlmInterface')
    @patch('handle_job_feedback.utils._build_node_context')
    @patch('handle_job_feedback.utils.validate_dynamic_generation_plan_output_json')
    def test_handle_parent_node_replan_invalid_json_with_retry(
        self,
        mock_validate_json,
        mock_build_context,
        mock_llm_interface_cls,
        mock_waiter_cls,
        mock_find_computation,
        mock_insert_session,
        mock_insert_consumption
    ):
        """Test parent node replan with invalid JSON output and retry."""
        parent_node = Mock(spec=Node)
        parent_node.id = 1
        
        dynamic_generation = Mock(spec=DynamicGeneration)
        dynamic_generation.generation_id = "gen_123"
        dynamic_generation.user_request = "Perform analysis"
        dynamic_generation.llm_model = "gpt-4"
        
        mock_build_context.return_value = {}
        
        mock_waiter = Mock()
        mock_waiter.retrieve_plan.return_value = {}
        mock_waiter.get_files.return_value = []
        mock_waiter_cls.return_value = mock_waiter
        
        mock_find_computation.return_value = None
        
        mock_llm_interface = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "consumption": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            "message": '{"invalid": "json"}',
            "data": {"invalid": "json"}
        }
        mock_llm_interface.dynamic_fb_replan.return_value = mock_response
        mock_llm_interface_cls.return_value = mock_llm_interface
        
        # First call returns invalid, second returns valid
        mock_validate_json.side_effect = [
            (False, ["Missing 'name' field"]),
            (True, [])
        ]
        
        mock_consumption = Mock()
        mock_consumption.id = 100
        mock_insert_consumption.return_value = mock_consumption
        
        result = handle_parent_node_replan(
            user_id="user_123",
            node_id=2,
            parent_node=parent_node,
            dynamic_generation=dynamic_generation
        )
        
        # Should retry and succeed
        assert result is not None
        assert mock_llm_interface.dynamic_fb_replan.call_count == 2


class TestHandleParentNodeReplanAndExecution:
    """Test handle_parent_node_replan_and_execution function."""
    
    @patch('handle_job_feedback.index.subprocess.Popen')
    @patch('handle_job_feedback.index.DynamicGenerationWaiter')
    @patch('handle_job_feedback.index.handle_parent_node_replan')
    @patch('handle_job_feedback.index.find_node_by_replan_source_id')
    @patch('handle_job_feedback.index.find_previous_node_by_node_id')
    @patch('handle_job_feedback.index.find_dynamic_generation_by_id')
    @patch('handle_job_feedback.index.find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id')
    def test_replan_and_execution_success(
        self,
        mock_find_branch,
        mock_find_dg,
        mock_find_prev_node,
        mock_find_replaned,
        mock_handle_replan,
        mock_waiter_cls,
        mock_popen
    ):
        """Test successful parent node replan and execution."""
        # Setup node
        node = Mock(spec=Node)
        node.id = 2
        node.dynamic_generation_id = "gen_123"
        node.replan_source_id = None
        
        # Setup task owner relation
        task_owner_relation = Mock(spec=TaskUserRelation)
        task_owner_relation.user_id = "user_123"
        
        # Setup analysis
        analysis = Mock(spec=Analysis)
        analysis.id = "analysis_123"
        
        # Setup dynamic generation
        dynamic_generation = Mock(spec=DynamicGeneration)
        dynamic_generation.generation_id = "gen_123"
        dynamic_generation.rest_node_count = 5
        dynamic_generation.replan_count_limit = 3
        dynamic_generation.user_request = "Perform analysis"
        dynamic_generation.llm_model = "gpt-4"
        dynamic_generation.max_branch = 2
        dynamic_generation.generation_mode = "only_new"
        dynamic_generation.file_ids = []
        
        # Setup branch
        branch = Mock(spec=DynamicGenerationBranch)
        branch.id = "branch_123"
        
        # Setup parent node
        parent_node = Mock(spec=Node)
        parent_node.id = 1
        
        mock_find_branch.return_value = branch
        mock_find_dg.return_value = dynamic_generation
        mock_find_prev_node.return_value = parent_node
        mock_find_replaned.return_value = []  # No previous replans
        
        # Mock replan result
        new_plan = {
            "name": "Revised Plan",
            "steps": "Step 1: Load data\nStep 2: Process"
        }
        mock_handle_replan.return_value = new_plan
        
        # Mock waiter
        mock_waiter = Mock()
        mock_waiter_cls.return_value = mock_waiter
        
        # Execute
        handle_parent_node_replan_and_execution(node, task_owner_relation, analysis)
        
        # Verify
        mock_handle_replan.assert_called_once_with(
            task_owner_relation.user_id,
            node.id,
            parent_node,
            dynamic_generation
        )
        mock_waiter.store_plan.assert_called_once()
        mock_popen.assert_called_once()
    
    @patch('handle_job_feedback.index.ServerAgent')
    @patch('handle_job_feedback.index.find_dynamic_generation_by_id')
    @patch('handle_job_feedback.index.find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id')
    def test_replan_when_rest_node_count_zero(
        self,
        mock_find_branch,
        mock_find_dg,
        mock_server_agent_cls
    ):
        """Test replan when rest_node_count is zero."""
        node = Mock(spec=Node)
        node.id = 2
        node.dynamic_generation_id = "gen_123"
        
        task_owner_relation = Mock(spec=TaskUserRelation)
        task_owner_relation.user_id = "user_123"
        
        analysis = Mock(spec=Analysis)
        
        dynamic_generation = Mock(spec=DynamicGeneration)
        dynamic_generation.rest_node_count = 0
        
        branch = Mock(spec=DynamicGenerationBranch)
        branch.id = "branch_123"
        
        mock_find_branch.return_value = branch
        mock_find_dg.return_value = dynamic_generation
        
        mock_server_agent = Mock()
        mock_server_agent_cls.return_value = mock_server_agent
        
        # Execute
        handle_parent_node_replan_and_execution(node, task_owner_relation, analysis)
        
        # Should report branch done and not continue
        mock_server_agent.report_dynamic_generation_branch_done.assert_called_once_with(branch.id)
    
    @patch('handle_job_feedback.index.handle_parent_node_replan')
    @patch('handle_job_feedback.index.find_node_by_replan_source_id')
    @patch('handle_job_feedback.index.find_previous_node_by_node_id')
    @patch('handle_job_feedback.index.find_dynamic_generation_by_id')
    @patch('handle_job_feedback.index.find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id')
    def test_replan_count_limit_exceeded(
        self,
        mock_find_branch,
        mock_find_dg,
        mock_find_prev_node,
        mock_find_replaned,
        mock_handle_replan
    ):
        """Test replan when count limit is exceeded."""
        node = Mock(spec=Node)
        node.id = 2
        node.dynamic_generation_id = "gen_123"
        node.replan_source_id = 100
        
        task_owner_relation = Mock(spec=TaskUserRelation)
        task_owner_relation.user_id = "user_123"
        
        analysis = Mock(spec=Analysis)
        
        dynamic_generation = Mock(spec=DynamicGeneration)
        dynamic_generation.rest_node_count = 5
        dynamic_generation.replan_count_limit = 2
        
        branch = Mock(spec=DynamicGenerationBranch)
        
        parent_node = Mock(spec=Node)
        parent_node.id = 1
        
        # Mock 3 existing replaned nodes (exceeds limit of 2)
        replaned_nodes = [Mock(), Mock(), Mock()]
        
        mock_find_branch.return_value = branch
        mock_find_dg.return_value = dynamic_generation
        mock_find_prev_node.return_value = parent_node
        mock_find_replaned.return_value = replaned_nodes
        
        # Execute
        handle_parent_node_replan_and_execution(node, task_owner_relation, analysis)
        
        # Should not call handle_parent_node_replan
        mock_handle_replan.assert_not_called()
    
    @patch('handle_job_feedback.index.DynamicGenerationWaiter')
    @patch('handle_job_feedback.index.handle_parent_node_replan')
    @patch('handle_job_feedback.index.find_node_by_replan_source_id')
    @patch('handle_job_feedback.index.find_previous_node_by_node_id')
    @patch('handle_job_feedback.index.find_dynamic_generation_by_id')
    @patch('handle_job_feedback.index.find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id')
    def test_replan_returns_empty_plan(
        self,
        mock_find_branch,
        mock_find_dg,
        mock_find_prev_node,
        mock_find_replaned,
        mock_handle_replan,
        mock_waiter_cls
    ):
        """Test replan when no new plan is generated."""
        node = Mock(spec=Node)
        node.id = 2
        node.dynamic_generation_id = "gen_123"
        node.replan_source_id = None
        
        task_owner_relation = Mock(spec=TaskUserRelation)
        task_owner_relation.user_id = "user_123"
        
        analysis = Mock(spec=Analysis)
        
        dynamic_generation = Mock(spec=DynamicGeneration)
        dynamic_generation.rest_node_count = 5
        dynamic_generation.replan_count_limit = 3
        
        branch = Mock(spec=DynamicGenerationBranch)
        parent_node = Mock(spec=Node)
        parent_node.id = 1
        
        mock_find_branch.return_value = branch
        mock_find_dg.return_value = dynamic_generation
        mock_find_prev_node.return_value = parent_node
        mock_find_replaned.return_value = []
        
        # Mock empty replan result
        mock_handle_replan.return_value = None
        
        mock_waiter = Mock()
        mock_waiter_cls.return_value = mock_waiter
        
        # Execute
        handle_parent_node_replan_and_execution(node, task_owner_relation, analysis)
        
        # Should not store plan or execute subprocess
        mock_waiter.store_plan.assert_not_called()


class TestBugFixerAgentReplan:
    """Test BugFixerAgent replan methods."""
    
    @patch('handle_job_feedback.bug_fixer_agent.DynamicGenerationAgent')
    @patch('handle_job_feedback.bug_fixer_agent.DynamicGenerationWaiter')
    @patch('handle_job_feedback.bug_fixer_agent.handle_parent_node_replan')
    @patch('handle_job_feedback.bug_fixer_agent.find_node_by_replan_source_id')
    @patch('handle_job_feedback.bug_fixer_agent.find_previous_node_by_node_id')
    @patch('handle_job_feedback.bug_fixer_agent.find_dynamic_generation_by_id')
    def test_handle_parent_node_replan_and_execution_success(
        self,
        mock_find_dg,
        mock_find_prev_node,
        mock_find_replaned,
        mock_handle_replan,
        mock_waiter_cls,
        mock_dg_agent_cls
    ):
        """Test BugFixerAgent successful parent node replan and execution."""
        # Setup mocks
        retry_process = Mock()
        node = Mock(spec=Node)
        node.id = 2
        node.dynamic_generation_id = "gen_123"
        node.replan_source_id = None
        
        task_owner_relation = Mock(spec=TaskUserRelation)
        task_owner_relation.user_id = "user_123"
        
        task = Mock()
        analysis = Mock()
        computation = Mock()
        error_description = "Computation failed"
        
        failed_to_fix_node = Mock(spec=Node)
        failed_to_fix_node.id = 3
        failed_to_fix_node.replan_source_id = None
        
        failed_to_fix_computation = Mock()
        failed_to_fix_task = Mock()
        
        parent_node = Mock(spec=Node)
        parent_node.id = 1
        
        dynamic_generation = Mock(spec=DynamicGeneration)
        dynamic_generation.generation_id = "gen_123"
        dynamic_generation.replan_count_limit = 3
        
        mock_find_dg.return_value = dynamic_generation
        mock_find_prev_node.return_value = parent_node
        mock_find_replaned.return_value = []
        
        new_plan = {
            "name": "Revised Plan",
            "steps": "Step 1: Process data"
        }
        mock_handle_replan.return_value = new_plan
        
        mock_waiter = Mock()
        mock_waiter_cls.return_value = mock_waiter
        
        mock_dg_agent = Mock()
        mock_dg_agent_cls.return_value = mock_dg_agent
        
        # Create agent
        bug_fixer_agent = BugFixerAgent(
            retry_process,
            node,
            task_owner_relation,
            task,
            analysis,
            computation,
            error_description,
            dynamic_generation=dynamic_generation
        )
        
        # Mock the report method
        bug_fixer_agent.report_and_block_later_nodes_for_dynamic_generation_with_plan = Mock()
        
        # Execute
        bug_fixer_agent.handle_parent_node_replan_and_execution(
            failed_to_fix_node,
            failed_to_fix_computation,
            failed_to_fix_task
        )
        
        # Verify
        mock_handle_replan.assert_called_once()
        mock_waiter.store_plan.assert_called_once()
        mock_dg_agent.handle_parent_node_dynamic_generation_with_plan.assert_called_once_with(
            parent_node,
            failed_to_fix_node.id
        )
        bug_fixer_agent.report_and_block_later_nodes_for_dynamic_generation_with_plan.assert_called_once()
    
    @patch('handle_job_feedback.bug_fixer_agent.handle_parent_node_replan')
    @patch('handle_job_feedback.bug_fixer_agent.find_node_by_replan_source_id')
    @patch('handle_job_feedback.bug_fixer_agent.find_previous_node_by_node_id')
    @patch('handle_job_feedback.bug_fixer_agent.find_dynamic_generation_by_id')
    def test_handle_parent_node_replan_count_limit_exceeded(
        self,
        mock_find_dg,
        mock_find_prev_node,
        mock_find_replaned,
        mock_handle_replan
    ):
        """Test BugFixerAgent replan when count limit is exceeded."""
        retry_process = Mock()
        node = Mock(spec=Node)
        node.id = 2
        node.dynamic_generation_id = "gen_123"
        
        task_owner_relation = Mock(spec=TaskUserRelation)
        task_owner_relation.user_id = "user_123"
        
        task = Mock()
        analysis = Mock()
        computation = Mock()
        error_description = "Computation failed"
        
        failed_to_fix_node = Mock(spec=Node)
        failed_to_fix_node.id = 3
        failed_to_fix_node.replan_source_id = 100
        
        failed_to_fix_computation = Mock()
        failed_to_fix_task = Mock()
        
        parent_node = Mock(spec=Node)
        parent_node.id = 1
        
        dynamic_generation = Mock(spec=DynamicGeneration)
        dynamic_generation.generation_id = "gen_123"
        dynamic_generation.replan_count_limit = 2
        
        # Mock 3 existing replaned nodes (exceeds limit)
        replaned_nodes = [Mock(), Mock(), Mock()]
        
        mock_find_dg.return_value = dynamic_generation
        mock_find_prev_node.return_value = parent_node
        mock_find_replaned.return_value = replaned_nodes
        
        # Create agent
        bug_fixer_agent = BugFixerAgent(
            retry_process,
            node,
            task_owner_relation,
            task,
            analysis,
            computation,
            error_description,
            dynamic_generation=dynamic_generation
        )
        
        # Mock the report method
        bug_fixer_agent.report_and_block_later_nodes_for_dynamic_generation_with_plan = Mock()
        
        # Execute
        bug_fixer_agent.handle_parent_node_replan_and_execution(
            failed_to_fix_node,
            failed_to_fix_computation,
            failed_to_fix_task
        )
        
        # Should not call handle_parent_node_replan
        mock_handle_replan.assert_not_called()
        # Should still report and block
        bug_fixer_agent.report_and_block_later_nodes_for_dynamic_generation_with_plan.assert_called_once()


class TestDynamicGenerationAgentReplan:
    """Test DynamicGenerationAgent handle_parent_node_dynamic_generation_with_plan method."""
    
    @patch('handle_job_feedback.dynamic_generation_agent.create_next_level_fbs_with_plan')
    @patch('handle_job_feedback.dynamic_generation_agent.update_node')
    @patch('handle_job_feedback.dynamic_generation_agent.update_dynamic_generation')
    @patch('handle_job_feedback.dynamic_generation_agent.DynamicGenerationWaiter')
    def test_handle_parent_node_dynamic_generation_with_plan(
        self,
        mock_waiter_cls,
        mock_update_dg,
        mock_update_node,
        mock_create_fbs
    ):
        """Test handle_parent_node_dynamic_generation_with_plan method."""
        user_id = "user_123"
        parent_node = Mock(spec=Node)
        parent_node.id = 1
        parent_node.type = "computation_node"
        
        dynamic_generation = Mock(spec=DynamicGeneration)
        dynamic_generation.generation_id = "gen_123"
        dynamic_generation.user_request = "Perform analysis"
        dynamic_generation.llm_model = "gpt-4"
        dynamic_generation.max_branch = 2
        dynamic_generation.generation_mode = "only_new"
        dynamic_generation.file_ids = []
        dynamic_generation.rest_node_count = 5
        dynamic_generation.computation_resource_configure = None
        
        mock_waiter = Mock()
        mock_waiter.retrieve_plan.return_value = {
            "name": "Plan",
            "steps": "Step 1"
        }
        mock_waiter_cls.return_value = mock_waiter
        
        # Mock FB generation
        fb_list = [
            {"fb_id": 1, "fbv_id": 1, "name": "FB1"},
            {"fb_id": 2, "fbv_id": 2, "name": "FB2"}
        ]
        mock_create_fbs.return_value = fb_list
        
        # Create agent
        agent = DynamicGenerationAgent(user_id, parent_node, dynamic_generation)
        
        # Mock _check_excutable to return True
        agent._check_excutable = Mock(return_value=(True, dynamic_generation))
        
        # Mock ServerAgent
        agent.server_agent = Mock()
        agent.server_agent.create_computation_node.return_value = {"id": 100}
        
        # Execute
        with patch('handle_job_feedback.dynamic_generation_agent.find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id') as mock_find_branch:
            mock_find_branch.return_value = None
            agent.handle_parent_node_dynamic_generation_with_plan(parent_node, "replan_source_123")
        
        # Verify
        mock_create_fbs.assert_called_once()
        assert mock_update_node.call_count >= 2  # GENERATING and FINISHED states


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
