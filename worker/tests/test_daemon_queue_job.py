"""
Unit tests for daemon/queue_job.py core functions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open, call
import os
import json
import subprocess
import sys

# Set environment variable before importing
os.environ.setdefault('DEPLOY_ENV', 'dev')
os.environ.setdefault('LOCAL_JOB_QUEUE', '/tmp/queue')

# Add daemon module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'daemon'))

from queue_job import (
    get_image_name,
    is_process_ended,
    is_container_ended,
    get_first_job,
    log_error_to_file,
)


class TestGetImageName:
    """Test get_image_name function"""

    def test_get_image_name_python_v2_default(self):
        """Test Python v2 with default preset env"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name = get_image_name("Python", None, True)
            assert image_name == "py-local-v2:default-dev"

    def test_get_image_name_python_v2_dyn(self):
        """Test Python v2 with dyn preset env"""
        # DEPLOY_ENV is already set to 'dev' at module import
        image_name = get_image_name("python", "omicairn-py-dyn-env", True)
        assert image_name == "py-local-v2:dyn-dev"

    def test_get_image_name_python_v2_mebocost(self):
        """Test Python v2 with mebocost preset env"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name = get_image_name("Python", "omicairn-py-mebocost-env", True)
            assert image_name == "py-local-v2:mebocost-dev"

    def test_get_image_name_python_v2_scvelo(self):
        """Test Python v2 with scvelo preset env"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name = get_image_name("Python", "omicairn-py-scvelo-env", True)
            assert image_name == "py-local-v2:scvelo-dev"

    def test_get_image_name_python_v2_scanpy(self):
        """Test Python v2 with scanpy preset env"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name = get_image_name("Python", "omicairn-py-sc-env", True)
            assert image_name == "py-local-v2:scanpy-dev"

    def test_get_image_name_python_v2_scfates(self):
        """Test Python v2 with scfates preset env"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name = get_image_name("Python", "omicairn-py-scfates-env", True)
            assert image_name == "py-local-v2:scfates-dev"

    def test_get_image_name_r_v2_default(self):
        """Test R v2 with default preset env"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name = get_image_name("R", None, True)
            assert image_name == "r-local-v2:dev-latest"

    def test_get_image_name_r_v2_metaboanalyst(self):
        """Test R v2 with metaboanalyst preset env"""
        # DEPLOY_ENV is already set to 'dev' at module import
        image_name = get_image_name("r", "omicairn-r-metaboanalyst-env", True)
        assert image_name == "r-local-v2:metaboanalyst-dev-latest"

    def test_get_image_name_bash_v2(self):
        """Test Bash v2"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name = get_image_name("Bash", None, True)
            assert image_name == "bash-local-v2:dev-latest"

    def test_get_image_name_python_v1_default(self):
        """Test Python v1 with default preset env"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name = get_image_name("Python", None, False)
            assert image_name == "py-local:default-dev"

    def test_get_image_name_python_v1_dyn(self):
        """Test Python v1 with dyn preset env"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name = get_image_name("Python", "omicairn-py-dyn-env", False)
            assert image_name == "py-local:dyn-dev"

    def test_get_image_name_r_v1(self):
        """Test R v1"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name = get_image_name("R", "custom-env", False)
            assert image_name == "r-local:custom-env"

    def test_get_image_name_bash_v1(self):
        """Test Bash v1"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name = get_image_name("Bash", "custom-env", False)
            assert image_name == "bash-local:custom-env"

    def test_get_image_name_unsupported_language_v2(self):
        """Test unsupported language for v2"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            with pytest.raises(ValueError, match="Unsupported program language"):
                get_image_name("Java", None, True)

    def test_get_image_name_unsupported_language_v1(self):
        """Test unsupported language for v1"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            with pytest.raises(ValueError, match="Unsupported program language"):
                get_image_name("Go", None, False)

    def test_get_image_name_case_insensitive(self):
        """Test that language is case insensitive"""
        with patch.dict(os.environ, {'DEPLOY_ENV': 'dev'}):
            image_name1 = get_image_name("python", None, True)
            image_name2 = get_image_name("PYTHON", None, True)
            image_name3 = get_image_name("Python", None, True)
            assert image_name1 == image_name2 == image_name3


class TestIsProcessEnded:
    """Test is_process_ended function"""

    @patch('os.kill')
    def test_is_process_ended_running(self, mock_kill):
        """Test process is still running"""
        mock_kill.return_value = None  # No exception means process exists
        
        result = is_process_ended(12345)
        
        assert result is False
        mock_kill.assert_called_once_with(12345, 0)

    @patch('os.kill')
    def test_is_process_ended_terminated(self, mock_kill):
        """Test process has ended"""
        mock_kill.side_effect = OSError("No such process")
        
        result = is_process_ended(12345)
        
        assert result is True
        mock_kill.assert_called_once_with(12345, 0)


class TestIsContainerEnded:
    """Test is_container_ended function"""

    @patch('subprocess.run')
    def test_is_container_ended_running(self, mock_run):
        """Test container is still running"""
        mock_result = Mock()
        mock_result.stdout = "'true'"
        mock_run.return_value = mock_result
        
        result = is_container_ended("container_123")
        
        assert result is False
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_is_container_ended_stopped(self, mock_run):
        """Test container has stopped"""
        mock_result = Mock()
        mock_result.stdout = "'false'"
        mock_run.return_value = mock_result
        
        result = is_container_ended("container_123")
        
        assert result is True
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_is_container_ended_not_exists(self, mock_run):
        """Test container does not exist"""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'docker')
        
        result = is_container_ended("container_123")
        
        assert result is True


class TestGetFirstJob:
    """Test get_first_job function"""

    @patch('os.listdir')
    @patch('os.path.getctime')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_first_job_single_file(self, mock_file, mock_getctime, mock_listdir):
        """Test getting first job with single file"""
        with patch.dict(os.environ, {'LOCAL_JOB_QUEUE': '/tmp/queue'}):
            from queue_job import LOCAL_JOB_QUEUE
            
            mock_listdir.return_value = ['job1.json']
            mock_getctime.return_value = 1000
            
            test_job = {"computation_id": "comp_123", "program_language": "Python"}
            mock_file.return_value.read.return_value = json.dumps(test_job)
            
            with patch('queue_job.LOCAL_JOB_QUEUE', '/tmp/queue'):
                job = get_first_job()
            
            assert job == test_job
            mock_listdir.assert_called_once()

    @patch('os.listdir')
    @patch('os.path.getctime')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_first_job_multiple_files(self, mock_file, mock_getctime, mock_listdir):
        """Test getting first job with multiple files"""
        with patch.dict(os.environ, {'LOCAL_JOB_QUEUE': '/tmp/queue'}):
            mock_listdir.return_value = ['job3.json', 'job1.json', 'job2.json']
            
            # job1 is oldest
            def getctime_side_effect(path):
                if 'job1' in path:
                    return 1000
                elif 'job2' in path:
                    return 2000
                elif 'job3' in path:
                    return 3000
                return 0
            
            mock_getctime.side_effect = getctime_side_effect
            
            test_job = {"computation_id": "comp_oldest", "program_language": "Python"}
            mock_file.return_value.read.return_value = json.dumps(test_job)
            
            with patch('queue_job.LOCAL_JOB_QUEUE', '/tmp/queue'):
                job = get_first_job()
            
            assert job == test_job

    @patch('os.listdir')
    def test_get_first_job_empty_queue(self, mock_listdir):
        """Test getting first job when queue is empty"""
        with patch.dict(os.environ, {'LOCAL_JOB_QUEUE': '/tmp/queue'}):
            mock_listdir.return_value = []
            
            with patch('queue_job.LOCAL_JOB_QUEUE', '/tmp/queue'):
                job = get_first_job()
            
            assert job is None

    @patch('os.listdir')
    def test_get_first_job_only_done_files(self, mock_listdir):
        """Test getting first job when only .done files exist"""
        with patch.dict(os.environ, {'LOCAL_JOB_QUEUE': '/tmp/queue'}):
            mock_listdir.return_value = ['job1.json.done', 'job2.json.done']
            
            with patch('queue_job.LOCAL_JOB_QUEUE', '/tmp/queue'):
                job = get_first_job()
            
            assert job is None

    @patch('os.listdir')
    @patch('os.path.getctime')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_first_job_filters_done_files(self, mock_file, mock_getctime, mock_listdir):
        """Test that .done files are filtered out"""
        with patch.dict(os.environ, {'LOCAL_JOB_QUEUE': '/tmp/queue'}):
            mock_listdir.return_value = ['job1.json', 'job2.json.done', 'job3.json']
            
            def getctime_side_effect(path):
                if 'job1' in path:
                    return 1000
                elif 'job3' in path:
                    return 500  # job3 is oldest
                return 0
            
            mock_getctime.side_effect = getctime_side_effect
            
            test_job = {"computation_id": "comp_3", "program_language": "Python"}
            mock_file.return_value.read.return_value = json.dumps(test_job)
            
            with patch('queue_job.LOCAL_JOB_QUEUE', '/tmp/queue'):
                job = get_first_job()
            
            assert job == test_job


class TestLogErrorToFile:
    """Test log_error_to_file function"""

    @patch('builtins.open', new_callable=mock_open)
    @patch('time.strftime')
    def test_log_error_to_file_success(self, mock_strftime, mock_file):
        """Test successfully logging error to file"""
        mock_strftime.return_value = "2024-01-01 12:00:00"
        
        log_error_to_file("Test error message")
        
        mock_file.assert_called_once_with("/tmp/local-queue_errors.log", "a", encoding='utf-8')
        handle = mock_file()
        
        # Verify write calls
        write_calls = handle.write.call_args_list
        assert len(write_calls) == 2
        assert "Test error message" in write_calls[0][0][0]
        assert "2024-01-01 12:00:00" in write_calls[0][0][0]

    @patch('builtins.open', new_callable=mock_open)
    @patch('queue_job.logger')
    def test_log_error_to_file_failure(self, mock_logger, mock_file):
        """Test error handling when file write fails"""
        mock_file.side_effect = Exception("Permission denied")
        
        log_error_to_file("Test error message")
        
        # Should log the error
        mock_logger.error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
