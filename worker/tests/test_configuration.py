"""
Configuration and environment tests for omicairn-worker.
Tests configuration loading, environment variable handling, and system setup scenarios.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
import json

# Import configuration-related modules
from server.config import *
from constants.gpt_server import *
from constants.computation import *


class TestEnvironmentVariables:
    """Test environment variable handling."""
    
    def test_required_environment_variables(self):
        """Test that required environment variables are properly loaded."""
        required_vars = [
            'MYSQL_IP',
            'MYSQL_PORT', 
            'MYSQL_DATABASE',
            'MYSQL_USERNAME',
            'MYSQL_PASSWORD',
            'GPT_WORKFLOW_SERVER_HOST',
            'GPT_WORKFLOW_SERVER_PORT',
            'MAIN_SERVER_HOST',
            'COMPUTATION_SERVER_HOST'
        ]
        
        for var in required_vars:
            # Environment variables should be set by conftest.py
            assert var in os.environ
            assert os.environ[var] is not None
            assert len(os.environ[var]) > 0

    def test_environment_variable_defaults(self):
        """Test default values for environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            # Test with empty environment
            
            # Some variables should have defaults
            default_mappings = {
                'GPT_WORKFLOW_SERVER_PORT': '5000',
                'MYSQL_PORT': '3306'
            }
            
            for var, default_value in default_mappings.items():
                # Set default and test
                os.environ.setdefault(var, default_value)
                assert os.environ[var] == default_value

    def test_environment_variable_type_conversion(self):
        """Test type conversion of environment variables."""
        with patch.dict(os.environ, {
            'TEST_PORT': '8080',
            'TEST_BOOL': 'true',
            'TEST_INT': '12345',
            'TEST_FLOAT': '3.14159'
        }):
            # Test integer conversion
            port = int(os.environ.get('TEST_PORT', '0'))
            assert port == 8080
            assert isinstance(port, int)
            
            # Test boolean conversion
            bool_val = os.environ.get('TEST_BOOL', 'false').lower() == 'true'
            assert bool_val is True
            
            # Test float conversion
            float_val = float(os.environ.get('TEST_FLOAT', '0.0'))
            assert float_val == 3.14159
            assert isinstance(float_val, float)

    def test_missing_required_variables(self):
        """Test behavior when required environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Critical variables should cause issues when missing
            critical_vars = ['MYSQL_IP', 'MYSQL_DATABASE']
            
            for var in critical_vars:
                # Should handle missing variables gracefully
                value = os.environ.get(var)
                assert value is None

    def test_environment_variable_validation(self):
        """Test validation of environment variable values."""
        test_cases = [
            ('MYSQL_PORT', '65536', False),  # Port too high
            ('MYSQL_PORT', '0', False),      # Port too low
            ('MYSQL_PORT', 'not_a_number', False),  # Invalid format
            ('MYSQL_PORT', '3306', True),    # Valid port
            ('GPT_WORKFLOW_SERVER_HOST', '', False),  # Empty host
            ('GPT_WORKFLOW_SERVER_HOST', 'localhost', True),  # Valid host
        ]
        
        for var, value, should_be_valid in test_cases:
            with patch.dict(os.environ, {var: value}):
                env_value = os.environ.get(var)
                
                if var.endswith('_PORT'):
                    try:
                        port_num = int(env_value)
                        is_valid = 1 <= port_num <= 65535
                    except ValueError:
                        is_valid = False
                elif var.endswith('_HOST'):
                    is_valid = len(env_value.strip()) > 0
                else:
                    is_valid = True
                
                assert is_valid == should_be_valid

    def test_sensitive_environment_variables(self):
        """Test handling of sensitive environment variables."""
        sensitive_vars = [
            'MYSQL_PASSWORD',
            'SYSTEM_AGENT_KEY',
            'API_SECRET_KEY'
        ]
        
        for var in sensitive_vars:
            if var in os.environ:
                # Sensitive variables should not be empty
                value = os.environ[var]
                assert len(value) > 0
                
                # Should not contain obvious test values
                insecure_values = ['password', 'secret', 'test', '123456']
                assert value.lower() not in insecure_values


if __name__ == '__main__':
    pytest.main([__file__, '-v'])