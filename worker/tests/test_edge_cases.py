"""
Edge case tests for omicairn-worker.
Tests unusual scenarios, boundary conditions, and corner cases that might occur in production.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import uuid
import random
from datetime import datetime, timedelta

# Import classes under test
from handle_dynamic_generation.llm_interface import LlmInterface as DynamicLlmInterface
from handle_job_feedback.llm_interface import LlmInterface as JobFeedbackLlmInterface
from handle_visualizer.llm_interface import LlmInterface as VisualizerLlmInterface
from handle_dynamic_generation.server_agent import ServerAgent


class TestBoundaryConditions:
    """Test boundary conditions and limits."""
    
    def test_empty_input_handling(self, mock_requests, mock_logger):
        """Test handling of empty or minimal inputs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "handled_empty_input"}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = DynamicLlmInterface()
        
        # Test with empty string inputs
        response = llm_interface.dynamic_fb(
            user_request="",  # Empty request
            node_id="",       # Empty node ID
            history=[],       # Empty history
            user_id="",       # Empty user ID
            llm_model="gpt-4o"
        )
        
        # Should handle empty inputs gracefully
        assert response.status_code == 200
        
        # Verify request structure
        call_args = mock_requests['post'].call_args
        request_body = call_args[1]['json']
        assert request_body['user_request'] == ""
        assert request_body['nodeHistoryList'] == []

    def test_maximum_input_sizes(self, mock_requests, mock_logger):
        """Test handling of maximum input sizes."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "handled_large_input"}
        mock_requests['post'].return_value = mock_response
        
        # Create very large inputs
        large_user_request = "x" * 50000  # 50KB request
        large_node_id = "node_" + "x" * 1000  # Very long node ID
        
        # Large history with many nodes
        large_history = []
        for i in range(500):  # 500 nodes in history
            large_history.append({
                "node": {
                    "id": f"node_{i}",
                    "name": "x" * 1000,  # Large node name
                    "data": "y" * 5000   # Large data field
                },
                "latestComputation": {
                    "id": f"comp_{i}",
                    "result": "z" * 2000  # Large result
                }
            })
        
        llm_interface = DynamicLlmInterface()
        response = llm_interface.dynamic_fb(
            user_request=large_user_request,
            node_id=large_node_id,
            history=large_history,
            user_id="large_test_user",
            llm_model="gpt-4o"
        )
        
        # Should handle large inputs
        assert response.status_code == 200
        
        # Verify large data was included in request
        call_args = mock_requests['post'].call_args
        request_body = call_args[1]['json']
        assert len(request_body['user_request']) == 50000
        assert len(request_body['nodeHistoryList']) == 500

    def test_unicode_and_special_characters(self, mock_requests, mock_logger):
        """Test handling of unicode and special characters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "handled_unicode"}
        mock_requests['post'].return_value = mock_response
        
        # Test with various unicode and special characters
        unicode_inputs = [
            "Analyze genomic data with émojis 🧬🔬",
            # CJK sample text ("analyze genes")
            "Process data with CJK characters: \u5206\u6790\u57fa\u56e0",
            "Handle Russian text: Анализ геномных данных",
            "Arabic text processing: تحليل البيانات الجينية",
            "Mathematical symbols: ∑∫∂∇α²β³γ",
            "Special chars: !@#$%^&*()_+-=[]{}|;:'\",.<>?/`~",
            "Emoji combinations: 👨‍💻🧪🔬📊📈📉💡🎯✨🚀",
            # CJK sample "\u4e16\u754c" = "world"
            "Mixed: Hello \u4e16\u754c 🌍 Привет мир 🗺️ مرحبا بالعالم"
        ]
        
        llm_interface = DynamicLlmInterface()
        
        for unicode_input in unicode_inputs:
            response = llm_interface.dynamic_fb(
                user_request=unicode_input,
                node_id="unicode_test_node",
                history=[{
                    "node": {"id": "node1", "name": unicode_input},
                    "latestComputation": {"id": "comp1", "result": unicode_input}
                }],
                user_id="unicode_test_user",
                llm_model="gpt-4o"
            )
            
            assert response.status_code == 200

    def test_null_and_none_handling(self, mock_requests, mock_logger):
        """Test handling of null and None values."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "handled_null_values"}
        mock_requests['post'].return_value = mock_response
        
        # Test with None values (should be converted to appropriate defaults)
        llm_interface = DynamicLlmInterface()
        
        # Test with None history
        response = llm_interface.dynamic_fb(
            user_request="Test with None values",
            node_id="null_test_node",
            history=None,  # None instead of list
            user_id="null_test_user",
            llm_model="gpt-4o"
        )
        
        # Should handle None values gracefully
        assert response.status_code == 200

    def test_extremely_nested_data_structures(self, mock_requests, mock_logger):
        """Test handling of deeply nested data structures."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "handled_nested_data"}
        mock_requests['post'].return_value = mock_response
        
        # Create deeply nested structure
        def create_nested_dict(depth, current_depth=0):
            if current_depth >= depth:
                return f"value_at_depth_{current_depth}"
            return {
                f"level_{current_depth}": create_nested_dict(depth, current_depth + 1),
                f"data_{current_depth}": f"some_data_{current_depth}",
                f"list_{current_depth}": [f"item_{i}" for i in range(3)]
            }
        
        deeply_nested_history = [{
            "node": create_nested_dict(20),  # 20 levels deep
            "latestComputation": create_nested_dict(15)  # 15 levels deep
        }]
        
        llm_interface = DynamicLlmInterface()
        response = llm_interface.dynamic_fb(
            user_request="Process deeply nested data",
            node_id="nested_test_node",
            history=deeply_nested_history,
            user_id="nested_test_user",
            llm_model="gpt-4o"
        )
        
        # Should handle deeply nested structures
        assert response.status_code == 200


class TestUnusualScenarios:
    """Test unusual and unexpected scenarios."""
    
    def test_simultaneous_identical_requests(self, mock_requests, mock_logger):
        """Test handling of multiple identical requests."""
        call_count = 0
        
        def track_calls(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            response = Mock()
            response.status_code = 200
            response.json.return_value = {"data": f"response_{call_count}"}
            return response
        
        mock_requests['post'].side_effect = track_calls
        
        llm_interface = DynamicLlmInterface()
        
        # Make multiple identical requests
        identical_request_params = {
            "user_request": "Identical request",
            "node_id": "identical_node",
            "history": [{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
            "user_id": "identical_user",
            "llm_model": "gpt-4o"
        }
        
        responses = []
        for _ in range(5):
            response = llm_interface.dynamic_fb(**identical_request_params)
            responses.append(response)
        
        # All requests should be processed
        assert len(responses) == 5
        assert all(r.status_code == 200 for r in responses)
        assert call_count == 5

    def test_rapid_sequential_requests(self, mock_requests, mock_logger):
        """Test handling of rapid sequential requests."""
        import time
        
        responses = []
        for i in range(10):
            responses.append(Mock(
                status_code=200,
                json=lambda i=i: {"data": f"rapid_response_{i}"}
            ))
        
        mock_requests['post'].side_effect = responses
        
        llm_interface = DynamicLlmInterface()
        results = []
        start_time = time.time()
        
        # Make rapid requests
        for i in range(10):
            response = llm_interface.dynamic_fb(
                user_request=f"Rapid request {i}",
                node_id=f"rapid_node_{i}",
                history=[],
                user_id="rapid_user",
                llm_model="gpt-4o"
            )
            results.append(response)
        
        end_time = time.time()
        
        # Should handle all rapid requests
        assert len(results) == 10
        assert all(r.status_code == 200 for r in results)
        
        # Should complete reasonably quickly
        assert end_time - start_time < 1.0

    def test_mixed_success_failure_patterns(self, mock_requests, mock_logger):
        """Test handling of mixed success/failure patterns."""
        # Create alternating success/failure pattern
        responses = []
        for i in range(20):
            if i % 3 == 0:  # Every 3rd request fails
                responses.append(Mock(
                    status_code=500,
                    json=lambda: {"error": "Intermittent failure"}
                ))
            else:
                responses.append(Mock(
                    status_code=200,
                    json=lambda i=i: {"data": f"success_{i}"}
                ))
        
        mock_requests['post'].side_effect = responses
        
        llm_interface = DynamicLlmInterface()
        results = []
        
        for i in range(20):
            response = llm_interface.dynamic_fb(
                user_request=f"Mixed pattern request {i}",
                node_id=f"mixed_node_{i}",
                history=[],
                user_id="mixed_user",
                llm_model="gpt-4o"
            )
            results.append(response)
        
        # Verify pattern: every 3rd should fail
        for i, result in enumerate(results):
            if i % 3 == 0:
                assert result.status_code == 500
            else:
                assert result.status_code == 200

    def test_invalid_model_specifications(self, mock_requests, mock_logger):
        """Test handling of invalid model specifications."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid model"}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = DynamicLlmInterface()
        
        invalid_models = [
            "",                    # Empty model
            "nonexistent-model",   # Non-existent model
            "gpt-999",            # Invalid version
            "model with spaces",   # Spaces in model name
            "\u6a21\u578b",  # Non-ASCII (CJK) model name ("model")
            "a" * 1000,           # Extremely long model name
            None,                 # None value
            123,                  # Numeric model name
            {"model": "object"}   # Object instead of string
        ]
        
        for invalid_model in invalid_models:
            try:
                response = llm_interface.dynamic_fb(
                    user_request="Test invalid model",
                    node_id="invalid_model_node",
                    history=[],
                    user_id="invalid_model_user",
                    llm_model=invalid_model
                )
                # Some invalid models might still result in requests
                # The server should handle the validation
            except (TypeError, AttributeError):
                # Some invalid models might cause client-side errors
                # This is acceptable behavior
                pass


class TestCornerCaseDataScenarios:
    """Test corner cases in data handling."""
    
    def test_circular_reference_handling(self, mock_requests, mock_logger):
        """Test handling of circular references in data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "handled_circular_refs"}
        mock_requests['post'].return_value = mock_response
        
        # Create data with circular references
        node_data = {"id": "circular_node", "name": "Circular Node"}
        comp_data = {"id": "circular_comp", "node": node_data}
        node_data["computation"] = comp_data  # Circular reference
        
        history = [{
            "node": node_data,
            "latestComputation": comp_data
        }]
        
        llm_interface = DynamicLlmInterface()
        
        # JSON serialization should handle circular references
        # (or raise appropriate error)
        try:
            response = llm_interface.dynamic_fb(
                user_request="Test circular references",
                node_id="circular_test_node",
                history=history,
                user_id="circular_test_user",
                llm_model="gpt-4o"
            )
            assert response.status_code == 200
        except (ValueError, TypeError):
            # Circular reference error is acceptable
            pass

    def test_timestamp_boundary_conditions(self, mock_requests, mock_logger):
        """Test timestamp boundary conditions."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "handled_timestamps"}
        mock_requests['post'].return_value = mock_response
        
        # Test with various timestamp edge cases
        timestamp_cases = [
            0,                           # Unix epoch
            -1,                          # Before epoch
            1,                           # First second after epoch
            2147483647,                  # Year 2038 problem (32-bit max)
            4294967295,                  # 32-bit unsigned max
            946684800000,                # Y2K (January 1, 2000)
            253402300799000,             # Year 9999 (distant future)
        ]
        
        llm_interface = DynamicLlmInterface()
        
        for timestamp in timestamp_cases:
            history = [{
                "node": {
                    "id": "timestamp_node",
                    "createdTime": timestamp,
                    "lastModified": timestamp
                },
                "latestComputation": {
                    "id": "timestamp_comp",
                    "startTime": timestamp,
                    "endTime": timestamp
                }
            }]
            
            response = llm_interface.dynamic_fb(
                user_request=f"Test timestamp {timestamp}",
                node_id="timestamp_test_node",
                history=history,
                user_id="timestamp_test_user",
                llm_model="gpt-4o"
            )
            
            assert response.status_code == 200

    def test_extreme_numeric_values(self, mock_requests, mock_logger):
        """Test handling of extreme numeric values."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "handled_extreme_numbers"}
        mock_requests['post'].return_value = mock_response
        
        # Test with extreme numeric values
        extreme_numbers = [
            0,                           # Zero
            -0,                          # Negative zero
            float('inf'),                # Positive infinity
            float('-inf'),               # Negative infinity
            float('nan'),                # Not a number
            1.7976931348623157e+308,     # Maximum float
            -1.7976931348623157e+308,    # Minimum float
            2.2250738585072014e-308,     # Smallest positive float
            9223372036854775807,         # Maximum 64-bit int
            -9223372036854775808,        # Minimum 64-bit int
        ]
        
        llm_interface = DynamicLlmInterface()
        
        for number in extreme_numbers:
            try:
                history = [{
                    "node": {
                        "id": "numeric_node",
                        "x_coordinate": number,
                        "y_coordinate": number * 2 if not (isinstance(number, float) and 
                                                          (number != number or number == float('inf') or number == float('-inf'))) else 0
                    },
                    "latestComputation": {
                        "id": "numeric_comp",
                        "cpu_usage": number if isinstance(number, (int, float)) and number == number and number != float('inf') and number != float('-inf') else 50.0,
                        "memory_usage": abs(number) if isinstance(number, (int, float)) and number == number and number != float('inf') and number != float('-inf') else 1024
                    }
                }]
                
                response = llm_interface.dynamic_fb(
                    user_request=f"Test extreme number {number}",
                    node_id="numeric_test_node",
                    history=history,
                    user_id="numeric_test_user",
                    llm_model="gpt-4o"
                )
                
                assert response.status_code == 200
                
            except (ValueError, OverflowError, TypeError):
                # Some extreme values might cause client-side errors
                # This is acceptable behavior
                pass

    def test_malformed_json_in_responses(self, mock_requests, mock_logger):
        """Test handling of malformed JSON in API responses."""
        # Mock malformed responses
        malformed_responses = [
            Mock(status_code=200, json=Mock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))),
            Mock(status_code=200, text='{"incomplete": json'),
            Mock(status_code=200, text='{"valid": "json", "but": {"missing": "closing"}'),
            Mock(status_code=200, text=''),  # Empty response
            Mock(status_code=200, text='null'),
            Mock(status_code=200, text='undefined'),
        ]
        
        llm_interface = DynamicLlmInterface()
        
        for malformed_response in malformed_responses:
            mock_requests['post'].return_value = malformed_response
            
            response = llm_interface.dynamic_fb(
                user_request="Test malformed JSON",
                node_id="malformed_test_node",
                history=[],
                user_id="malformed_test_user",
                llm_model="gpt-4o"
            )
            
            # Should return the response object (JSON parsing might fail later)
            assert response is not None
            assert hasattr(response, 'status_code')
            
            # JSON parsing errors should be handled gracefully
            try:
                response.json()
            except json.JSONDecodeError:
                # This is expected for malformed JSON
                pass


class TestResourceExhaustionScenarios:
    """Test scenarios that might exhaust system resources."""
    
    def test_memory_intensive_operations(self, mock_requests, mock_logger):
        """Test memory-intensive operations."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "memory_test_complete"}
        mock_requests['post'].return_value = mock_response
        
        # Create memory-intensive data
        large_objects = []
        for i in range(10):  # Create multiple large objects
            large_object = {
                "id": f"large_object_{i}",
                "data": ["x" * 10000 for _ in range(100)],  # 1MB of data per object
                "nested": {
                    "level1": {
                        "level2": {
                            "level3": ["y" * 5000 for _ in range(50)]
                        }
                    }
                }
            }
            large_objects.append(large_object)
        
        llm_interface = DynamicLlmInterface()
        response = llm_interface.create_workflow_report(
            node_ids=[obj["id"] for obj in large_objects],
            computation_details_list=large_objects,
            analysis_id="memory_test_analysis",
            uuid_str="memory_test_uuid",
            user_id="memory_test_user"
        )
        
        # Should handle large data structures
        assert response.status_code == 200
        
        # Cleanup
        del large_objects

    def test_high_frequency_requests(self, mock_requests, mock_logger):
        """Test high-frequency request patterns."""
        request_count = 0
        
        def count_requests(*args, **kwargs):
            nonlocal request_count
            request_count += 1
            return Mock(
                status_code=200,
                json=lambda: {"data": f"high_freq_response_{request_count}"}
            )
        
        mock_requests['post'].side_effect = count_requests
        
        llm_interface = DynamicLlmInterface()
        
        # Make high-frequency requests
        import time
        start_time = time.time()
        
        for i in range(50):  # 50 rapid requests
            response = llm_interface.dynamic_fb(
                user_request=f"High frequency request {i}",
                node_id=f"freq_node_{i}",
                history=[],
                user_id="freq_test_user",
                llm_model="gpt-4o"
            )
            assert response.status_code == 200
        
        end_time = time.time()
        
        # Verify all requests were processed
        assert request_count == 50
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])