"""
Unit tests for server dynamic generation functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestDynamicGenerationController:
    """Test dynamic generation controller APIs."""
    
    def test_plan_generate_api_success(self):
        """Test dynamic generation plan generation."""
        with patch('server.controller.dynamic_generation.request') as mock_request, \
             patch('server.controller.dynamic_generation.dynamic_generation_service') as mock_service, \
             patch('server.controller.dynamic_generation.ResponseManager') as mock_response:
            
            # Mock request
            mock_request.get_json.return_value = {
                "user_prompt": "Analyze gene expression data",
                "context": {"dataset_type": "RNA-seq"}
            }
            
            # Mock service response
            mock_plan = {
                "plan_id": "plan_123",
                "user_prompt": "Analyze gene expression data",
                "generated_steps": [
                    "Load data",
                    "Preprocess",
                    "Analyze"
                ],
                "status": "generated"
            }
            mock_service.generate_plan.return_value = mock_plan
            
            # Mock response
            mock_response.new_success_response.return_value = {
                "code": 200,
                "data": mock_plan
            }
            
            # Import and test
            from server.controller.dynamic_generation import DynamicGenerationPlanGenerateAPI
            api = DynamicGenerationPlanGenerateAPI()
            result = api.post()
            
            # Verify
            mock_service.generate_plan.assert_called_once()
            assert result["code"] == 200
    
    def test_plan_get_api_success(self):
        """Test getting dynamic generation plan."""
        with patch('server.controller.dynamic_generation.request') as mock_request, \
             patch('server.controller.dynamic_generation.dynamic_generation_service') as mock_service, \
             patch('server.controller.dynamic_generation.ResponseManager') as mock_response:
            
            # Mock request
            mock_request.args.get.return_value = "plan_123"
            
            # Mock service response
            mock_plan = {
                "plan_id": "plan_123",
                "status": "completed",
                "generated_code": "# Code here"
            }
            mock_service.get_plan.return_value = mock_plan
            
            # Mock response
            mock_response.new_success_response.return_value = {
                "code": 200,
                "data": mock_plan
            }
            
            # Import and test
            from server.controller.dynamic_generation import DynamicGenerationPlanGetAPI
            api = DynamicGenerationPlanGetAPI()
            result = api.get()
            
            # Verify
            assert result["code"] == 200
            assert result["data"]["plan_id"] == "plan_123"
    
    def test_plan_update_api_success(self):
        """Test updating dynamic generation plan."""
        with patch('server.controller.dynamic_generation.request') as mock_request, \
             patch('server.controller.dynamic_generation.dynamic_generation_service') as mock_service, \
             patch('server.controller.dynamic_generation.ResponseManager') as mock_response:
            
            # Mock request
            mock_request.get_json.return_value = {
                "plan_id": "plan_123",
                "updates": {
                    "generated_code": "# Updated code"
                }
            }
            
            # Mock service response
            mock_updated_plan = {
                "plan_id": "plan_123",
                "status": "updated",
                "generated_code": "# Updated code"
            }
            mock_service.update_plan.return_value = mock_updated_plan
            
            # Mock response
            mock_response.new_success_response.return_value = {
                "code": 200,
                "data": mock_updated_plan
            }
            
            # Import and test
            from server.controller.dynamic_generation import DynamicGenerationPlanUpdateAPI
            api = DynamicGenerationPlanUpdateAPI()
            result = api.put()
            
            # Verify
            assert result["code"] == 200
    
    def test_plan_store_api_success(self):
        """Test storing dynamic generation plan."""
        with patch('server.controller.dynamic_generation.request') as mock_request, \
             patch('server.controller.dynamic_generation.dynamic_generation_service') as mock_service, \
             patch('server.controller.dynamic_generation.AuthorityGuardianFactory') as mock_guardian, \
             patch('server.controller.dynamic_generation.ResponseManager') as mock_response:
            
            # Mock guardian
            mock_guardian_instance = Mock()
            mock_guardian_instance.get_user_id.return_value = "user_123"
            mock_guardian.get_authority_guardian.return_value = mock_guardian_instance
            
            # Mock request
            mock_request.get_json.return_value = {
                "plan_id": "plan_123",
                "name": "My Analysis Plan"
            }
            
            # Mock service response
            mock_stored_plan = {
                "plan_id": "plan_123",
                "name": "My Analysis Plan",
                "stored": True
            }
            mock_service.store_plan.return_value = mock_stored_plan
            
            # Mock response
            mock_response.new_success_response.return_value = {
                "code": 200,
                "data": mock_stored_plan
            }
            
            # Import and test
            from server.controller.dynamic_generation import DynamicGenerationPlanStoreAPI
            api = DynamicGenerationPlanStoreAPI()
            result = api.post()
            
            # Verify
            assert result["code"] == 200


class TestDynamicGenerationService:
    """Test dynamic generation service logic."""
    
    def test_generate_plan_success(self):
        """Test generating analysis plan."""
        with patch('server.service.dynamic_generation.LLMService') as mock_llm, \
             patch('server.service.dynamic_generation.dynamic_generation_dao') as mock_dao:
            
            # Mock LLM service
            mock_llm_instance = Mock()
            mock_llm_instance.generate_plan.return_value = {
                "steps": ["Step 1", "Step 2"],
                "code_outline": "# Outline"
            }
            mock_llm.return_value = mock_llm_instance
            
            # Mock DAO
            mock_plan = Mock()
            mock_plan.id = "plan_123"
            mock_dao.insert.return_value = mock_plan
            
            # Import and test
            from server.service.dynamic_generation import DynamicGenerationService
            service = DynamicGenerationService()
            result = service.generate_plan(
                "Analyze data",
                {"dataset": "RNA-seq"}
            )
            
            # Verify
            mock_llm_instance.generate_plan.assert_called_once()
            assert result.id == "plan_123"
    
    def test_execute_plan_success(self):
        """Test executing generated plan."""
        with patch('server.service.dynamic_generation.dynamic_generation_dao') as mock_dao, \
             patch('server.service.dynamic_generation.ComputationLauncher') as mock_launcher:
            
            # Mock plan
            mock_plan = Mock()
            mock_plan.id = "plan_123"
            mock_plan.generated_code = "# Code to execute"
            mock_plan.status = "ready"
            mock_dao.find_by_id.return_value = mock_plan
            
            # Mock launcher
            mock_launcher.launch_notebook.return_value = {
                "job_id": "job_123",
                "status": "submitted"
            }
            
            # Import and test
            from server.service.dynamic_generation import DynamicGenerationService
            service = DynamicGenerationService()
            result = service.execute_plan("plan_123")
            
            # Verify
            assert result["job_id"] == "job_123"
    
    def test_replan_with_feedback(self):
        """Test replanning with user feedback."""
        with patch('server.service.dynamic_generation.dynamic_generation_dao') as mock_dao, \
             patch('server.service.dynamic_generation.LLMService') as mock_llm:
            
            # Mock original plan
            mock_original_plan = Mock()
            mock_original_plan.id = "plan_123"
            mock_original_plan.generated_code = "# Original code"
            mock_dao.find_by_id.return_value = mock_original_plan
            
            # Mock LLM service
            mock_llm_instance = Mock()
            mock_llm_instance.replan_with_feedback.return_value = {
                "updated_code": "# Updated code with feedback",
                "changes": ["Added error handling"]
            }
            mock_llm.return_value = mock_llm_instance
            
            # Mock new plan
            mock_new_plan = Mock()
            mock_new_plan.id = "plan_124"
            mock_new_plan.parent_id = "plan_123"
            mock_dao.insert.return_value = mock_new_plan
            
            # Import and test
            from server.service.dynamic_generation import DynamicGenerationService
            service = DynamicGenerationService()
            result = service.replan_with_feedback(
                "plan_123",
                "Add error handling"
            )
            
            # Verify
            assert result.parent_id == "plan_123"


class TestDynamicGenerationLLMMonitor:
    """Test LLM interaction monitoring."""
    
    def test_get_generation_interactions(self):
        """Test getting LLM interactions for generation."""
        with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_session_dao') as mock_session_dao:
            
            # Mock sessions
            mock_sessions = [
                Mock(
                    id="session_1",
                    generation_id="gen_123",
                    input_tokens=100,
                    output_tokens=200,
                    model="gpt-4"
                )
            ]
            mock_session_dao.find_by_generation.return_value = mock_sessions
            
            # Import and test
            from server.service.dynamic_generation_llm_monitor import DynamicGenerationLLMMonitorService
            service = DynamicGenerationLLMMonitorService()
            result = service.get_generation_interactions("gen_123")
            
            # Verify
            assert "interactions" in result
            assert len(result["interactions"]) > 0
    
    def test_get_interaction_details(self):
        """Test getting detailed interaction information."""
        with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_session_dao') as mock_session_dao:
            
            # Mock session with details
            mock_session = Mock()
            mock_session.id = "session_1"
            mock_session.prompt = "Generate analysis code"
            mock_session.response = "# Generated code"
            mock_session.input_tokens = 100
            mock_session.output_tokens = 200
            mock_session_dao.find_by_id.return_value = mock_session
            
            # Import and test
            from server.service.dynamic_generation_llm_monitor import DynamicGenerationLLMMonitorService
            service = DynamicGenerationLLMMonitorService()
            result = service.get_interaction_details(
                "dynamic_generation",
                "session_1"
            )
            
            # Verify
            assert result["prompt"] == "Generate analysis code"
            assert result["input_tokens"] == 100
    