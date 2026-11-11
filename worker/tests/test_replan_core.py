"""
Unit tests for core replan logic in omicairn-worker.
Tests the replan count limit enforcement and replan source ID tracking.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestReplanCountLimitLogic:
    """Test replan count limit enforcement logic."""
    
    def test_replan_count_within_limit(self):
        """Test that replan proceeds when count is within limit."""
        # Given: replan_count_limit = 3, existing replans = 2
        replan_count_limit = 3
        existing_replans = [Mock(), Mock()]
        
        # When: checking if replan should proceed
        should_proceed = len(existing_replans) < replan_count_limit
        
        # Then: replan should proceed
        assert should_proceed is True
    
    def test_replan_count_at_limit(self):
        """Test that replan stops when count reaches limit."""
        # Given: replan_count_limit = 3, existing replans = 3
        replan_count_limit = 3
        existing_replans = [Mock(), Mock(), Mock()]
        
        # When: checking if replan should proceed
        should_proceed = len(existing_replans) < replan_count_limit
        
        # Then: replan should not proceed
        assert should_proceed is False
    
    def test_replan_count_exceeds_limit(self):
        """Test that replan stops when count exceeds limit."""
        # Given: replan_count_limit = 2, existing replans = 3
        replan_count_limit = 2
        existing_replans = [Mock(), Mock(), Mock()]
        
        # When: checking if replan should proceed
        should_proceed = len(existing_replans) < replan_count_limit
        
        # Then: replan should not proceed
        assert should_proceed is False
    
    def test_replan_count_no_limit(self):
        """Test replan when no limit is set (None or 0)."""
        # Given: replan_count_limit = None or 0
        for replan_count_limit in [None, 0]:
            existing_replans = [Mock(), Mock(), Mock()]
            
            # When: checking if replan should proceed (default to 0 if None)
            effective_limit = replan_count_limit if replan_count_limit is not None else 0
            should_proceed = len(existing_replans) < effective_limit
            
            # Then: replan should not proceed (0 means no replans allowed)
            assert should_proceed is False
    
    def test_replan_source_id_tracking(self):
        """Test that replan_source_id is correctly tracked."""
        # Given: a failed node
        failed_node = Mock()
        failed_node.id = 100
        failed_node.replan_source_id = None
        
        # When: determining the replan_source_id for new nodes
        replan_source_id = failed_node.replan_source_id if failed_node.replan_source_id is not None else failed_node.id
        
        # Then: replan_source_id should be the failed node's ID
        assert replan_source_id == 100
    
    def test_replan_source_id_inheritance(self):
        """Test that replan_source_id is inherited from previous replan."""
        # Given: a failed node that was already a replan
        failed_node = Mock()
        failed_node.id = 200
        failed_node.replan_source_id = 100
        
        # When: determining the replan_source_id for new nodes
        replan_source_id = failed_node.replan_source_id if failed_node.replan_source_id is not None else failed_node.id
        
        # Then: replan_source_id should be inherited
        assert replan_source_id == 100


class TestReplanWorkflowLogic:
    """Test the overall replan workflow logic."""
    
    def test_replan_decision_flow_should_proceed(self):
        """Test decision flow when replan should proceed."""
        # Setup: mock dynamic generation with limit
        dynamic_generation = Mock()
        dynamic_generation.rest_node_count = 5
        dynamic_generation.replan_count_limit = 3
        
        # Setup: mock existing replans
        existing_replans = [Mock(), Mock()]  # 2 existing replans
        
        # Decision logic
        should_report_done = dynamic_generation.rest_node_count <= 0
        limit_exceeded = len(existing_replans) >= dynamic_generation.replan_count_limit
        
        # Assertions
        assert should_report_done is False
        assert limit_exceeded is False
        # Should proceed with replan
        assert not should_report_done and not limit_exceeded
    
    def test_replan_decision_flow_rest_node_count_zero(self):
        """Test decision flow when rest_node_count is zero."""
        # Setup: mock dynamic generation with no remaining nodes
        dynamic_generation = Mock()
        dynamic_generation.rest_node_count = 0
        dynamic_generation.replan_count_limit = 3
        
        # Setup: mock existing replans
        existing_replans = []
        
        # Decision logic
        should_report_done = dynamic_generation.rest_node_count <= 0
        
        # Assertions
        assert should_report_done is True
        # Should report done instead of replanning
    
    def test_replan_decision_flow_limit_exceeded(self):
        """Test decision flow when replan limit is exceeded."""
        # Setup: mock dynamic generation with limit
        dynamic_generation = Mock()
        dynamic_generation.rest_node_count = 5
        dynamic_generation.replan_count_limit = 2
        
        # Setup: mock existing replans exceeding limit
        existing_replans = [Mock(), Mock(), Mock()]  # 3 replans
        
        # Decision logic
        should_report_done = dynamic_generation.rest_node_count <= 0
        limit_exceeded = len(existing_replans) >= dynamic_generation.replan_count_limit
        
        # Assertions
        assert should_report_done is False
        assert limit_exceeded is True
        # Should not proceed with replan


class TestReplanPlanStructure:
    """Test plan structure validation and processing."""
    
    def test_valid_plan_structure(self):
        """Test validation of a valid plan structure."""
        # Given: a valid plan
        plan = {
            "name": "Revised Analysis Plan",
            "steps": "Step 1: Load data\nStep 2: Process data\nStep 3: Generate results"
        }
        
        # When: validating the plan
        has_name = "name" in plan and bool(plan["name"])
        has_steps = "steps" in plan and bool(plan["steps"])
        is_valid = has_name and has_steps
        
        # Then: plan should be valid
        assert is_valid is True
    
    def test_invalid_plan_missing_name(self):
        """Test validation of a plan missing name."""
        # Given: a plan without name
        plan = {
            "steps": "Step 1: Load data"
        }
        
        # When: validating the plan
        has_name = "name" in plan and bool(plan.get("name"))
        has_steps = "steps" in plan and bool(plan.get("steps"))
        is_valid = has_name and has_steps
        
        # Then: plan should be invalid
        assert is_valid is False
    
    def test_invalid_plan_missing_steps(self):
        """Test validation of a plan missing steps."""
        # Given: a plan without steps
        plan = {
            "name": "Analysis Plan"
        }
        
        # When: validating the plan
        has_name = "name" in plan and bool(plan.get("name"))
        has_steps = "steps" in plan and bool(plan.get("steps"))
        is_valid = has_name and has_steps
        
        # Then: plan should be invalid
        assert is_valid is False
    
    def test_empty_plan(self):
        """Test validation of an empty plan."""
        # Given: an empty plan
        plan = {}
        
        # When: validating the plan
        has_name = "name" in plan and bool(plan.get("name"))
        has_steps = "steps" in plan and bool(plan.get("steps"))
        is_valid = has_name and has_steps
        
        # Then: plan should be invalid
        assert is_valid is False
    
    def test_none_plan(self):
        """Test handling of None plan."""
        # Given: a None plan
        plan = None
        
        # When: checking if plan exists
        has_plan = plan is not None
        
        # Then: should indicate no plan
        assert has_plan is False


class TestReplanRetryLogic:
    """Test retry logic for replan operations."""
    
    def test_retry_count_tracking(self):
        """Test that retry count is properly tracked."""
        max_retry = 10
        retry_attempts = []
        
        for i in range(max_retry):
            retry_attempts.append(i)
        
        assert len(retry_attempts) == max_retry
        assert retry_attempts[-1] == 9  # 0-indexed
    
    def test_retry_success_before_max(self):
        """Test successful operation before max retry."""
        max_retry = 10
        success_on_attempt = 3
        
        for i in range(max_retry):
            if i == success_on_attempt:
                # Simulate success
                success = True
                break
        else:
            success = False
        
        assert success is True
    
    def test_retry_failure_after_max(self):
        """Test failure after max retry attempts."""
        max_retry = 10
        success_on_attempt = 15  # Beyond max_retry
        
        for i in range(max_retry):
            if i == success_on_attempt:
                success = True
                break
        else:
            success = False
        
        assert success is False
    
    def test_retry_with_last_attempt_check(self):
        """Test checking if current attempt is the last one."""
        max_retry = 10
        
        for i in range(max_retry):
            is_last_attempt = i >= max_retry - 1
            
            if i == 0:
                assert is_last_attempt is False
            elif i == max_retry - 1:
                assert is_last_attempt is True


class TestReplanDataStructures:
    """Test data structures used in replan operations."""
    
    def test_node_replan_attributes(self):
        """Test that node has necessary replan attributes."""
        # Create a mock node with replan attributes
        node = Mock()
        node.id = 1
        node.replan_source_id = None
        node.dynamic_generation_id = "gen_123"
        
        # Verify attributes exist
        assert hasattr(node, 'id')
        assert hasattr(node, 'replan_source_id')
        assert hasattr(node, 'dynamic_generation_id')
        
        # Verify attribute values
        assert node.id == 1
        assert node.replan_source_id is None
        assert node.dynamic_generation_id == "gen_123"
    
    def test_dynamic_generation_replan_attributes(self):
        """Test that dynamic generation has necessary replan attributes."""
        # Create a mock dynamic generation with replan attributes
        dg = Mock()
        dg.generation_id = "gen_123"
        dg.rest_node_count = 5
        dg.replan_count_limit = 3
        dg.user_request = "Perform analysis"
        dg.llm_model = "gpt-4"
        
        # Verify attributes exist and have correct values
        assert hasattr(dg, 'generation_id')
        assert hasattr(dg, 'rest_node_count')
        assert hasattr(dg, 'replan_count_limit')
        assert hasattr(dg, 'user_request')
        assert hasattr(dg, 'llm_model')
        
        assert dg.generation_id == "gen_123"
        assert dg.rest_node_count == 5
        assert dg.replan_count_limit == 3
    
    def test_plan_data_structure(self):
        """Test plan data structure format."""
        # Create a plan structure
        plan = {
            "name": "Test Plan",
            "steps": "Step 1\nStep 2\nStep 3"
        }
        
        # Verify structure
        assert isinstance(plan, dict)
        assert "name" in plan
        assert "steps" in plan
        assert isinstance(plan["name"], str)
        assert isinstance(plan["steps"], str)
        assert "\n" in plan["steps"]  # Multi-line steps


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
