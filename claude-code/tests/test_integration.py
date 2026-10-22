"""
Integration tests for previous_app and close_out_app

These tests validate the complete workflow from previous_app through close_out_app
using a realistic environment setup.

NOTE: This module is an integration-test scaffold and is not yet functional.
The test bodies wrap their assertions in broad try/except blocks, so they
cannot fail meaningfully; they are therefore skipped until they are rewritten
with real assertions.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import boto3
try:  # moto >= 5
    from moto import mock_aws as mock_s3
except ImportError:  # moto < 5
    from moto import mock_s3

# Region for the moto S3 mock; moto requires some value. Override via AWS_REGION.
TEST_AWS_REGION = os.environ.get("AWS_REGION") or "test-region-1"

SCAFFOLD_SKIP_REASON = (
    "integration scaffold - not yet functional (assertions are swallowed by "
    "try/except); rewrite before enabling"
)


@unittest.skip(SCAFFOLD_SKIP_REASON)
class TestPreviousAppIntegration(unittest.TestCase):
    """Integration tests for previous_app"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.bucket_name = 'test-omicairn-bucket'
        
        self.env_vars = {
            'COMPUTATION_ID': 'integration-comp-123',
            'NODE_ID': 'integration-node-456',
            'USER_ID': 'integration-user-789',
            'BUCKET_NAME': self.bucket_name,
            'MAIN_SERVER_ACCESS_PREFIX': 'http://localhost:8080',
            'SYSTEM_AGENT_KEY': 'test-integration-key',
            'PIPE_MESSAGE_PATH': f'{self.test_dir}/pipe-message'
        }

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @mock_s3
    @patch.dict(os.environ, clear=True)
    @patch('requests.post')
    @patch('requests.get')
    def test_previous_app_full_workflow_with_s3(self, mock_get, mock_post):
        """Test complete previous_app workflow with real S3 operations"""
        # Update environment
        os.environ.update(self.env_vars)
        
        # Add previous_app to path
        sys.path.insert(0, str(Path(__file__).parent.parent / "previous_app"))
        from main import prepare
        
        # Setup mock S3
        s3_client = boto3.client('s3', region_name=TEST_AWS_REGION)
        s3_client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration={'LocationConstraint': TEST_AWS_REGION},
        )
        
        # Upload test data to S3
        test_data_id = 'test-data-123'
        s3_key = f'adata/{test_data_id}-general-s3-store/output.csv'
        s3_client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=b'col1,col2\nval1,val2'
        )
        
        # Mock API responses
        mock_login_response = Mock()
        mock_login_response.json.return_value = {'code': 200, 'data': 'test-token'}
        mock_login_response.status_code = 200
        mock_post.return_value = mock_login_response
        
        mock_plan_response = Mock()
        mock_plan_response.text = '{"plan": "test plan"}'
        mock_get.return_value = mock_plan_response
        
        # Mock ServerAPIInvoker
        with patch('main.ServerAPIInvoker') as mock_api_invoker_class:
            mock_api_invoker = Mock()
            mock_api_invoker_class.return_value = mock_api_invoker
            
            # Setup mock responses
            mock_api_invoker.get_node_information.return_value = {
                'id': 'integration-node-456',
                'type': 'computation node',
                'dynamicGenerationId': None
            }
            
            mock_api_invoker.get_computation_details.return_value = {
                'computation_basic_info': {
                    'id': 'integration-comp-123',
                    'computationParams': '{"test_param": "test_value"}',
                    'resultDataId': test_data_id
                }
            }
            
            mock_api_invoker.get_branch_path.return_value = {
                'previousNodeList': [
                    {
                        'id': 'prev-node-1',
                        'type': 'data node',
                        'dataId': test_data_id
                    }
                ],
                'previousEdgeList': []
            }
            
            mock_api_invoker.get_node_extra_files.return_value = []
            
            # Create necessary directories
            os.makedirs(f'{self.test_dir}/omicairn', exist_ok=True)
            os.makedirs(f'{self.test_dir}/omicairn/outputs/charts', exist_ok=True)
            
            with patch('builtins.open', create=True) as mock_open:
                # Configure mock to handle different file paths
                def open_side_effect(filename, mode='r', *args, **kwargs):
                    if filename.endswith('.json'):
                        if 'w' in mode:
                            mock_file = MagicMock()
                            mock_file.__enter__ = Mock(return_value=mock_file)
                            mock_file.__exit__ = Mock(return_value=False)
                            return mock_file
                    return MagicMock()
                
                mock_open.side_effect = open_side_effect
                
                # Execute
                try:
                    prepare()
                    
                    # Verify API calls were made
                    mock_api_invoker.get_node_information.assert_called()
                    mock_api_invoker.get_computation_details.assert_called()
                    mock_api_invoker.get_branch_path.assert_called()
                    
                except Exception as e:
                    # Test passes if we got this far - file writing may fail in test env
                    print(f"Expected error in test env: {e}")

    @patch.dict(os.environ, clear=True)
    def test_previous_app_with_multiple_previous_nodes(self):
        """Test previous_app with multiple previous nodes in workflow"""
        os.environ.update(self.env_vars)
        
        sys.path.insert(0, str(Path(__file__).parent.parent / "previous_app"))
        from main import prepare
        
        with patch('main.ServerAPIInvoker') as mock_api_invoker_class:
            with patch('main.boto3.client') as mock_boto3:
                mock_api_invoker = Mock()
                mock_api_invoker_class.return_value = mock_api_invoker
                
                # Setup multiple previous nodes
                mock_api_invoker.get_node_information.return_value = {
                    'id': 'integration-node-456',
                    'type': 'computation node',
                    'dynamicGenerationId': None
                }
                
                mock_api_invoker.get_computation_details.return_value = {
                    'computation_basic_info': {
                        'id': 'integration-comp-123',
                        'computationParams': '{}',
                        'resultDataId': 'data-3'
                    }
                }
                
                mock_api_invoker.get_branch_path.return_value = {
                    'previousNodeList': [
                        {'id': 'node-1', 'type': 'data node', 'dataId': 'data-1'},
                        {'id': 'node-2', 'type': 'computation node', 'dataId': None},
                        {'id': 'node-3', 'type': 'computation node', 'dataId': None}
                    ],
                    'previousEdgeList': []
                }
                
                mock_api_invoker.get_node_extra_files.return_value = []
                
                # Mock S3
                mock_s3_client = Mock()
                mock_boto3.return_value = mock_s3_client
                mock_paginator = Mock()
                mock_s3_client.get_paginator.return_value = mock_paginator
                mock_paginator.paginate.return_value = [{'Contents': []}]
                
                with patch('builtins.open', MagicMock()):
                    with patch('os.makedirs'):
                        try:
                            prepare()
                            
                            # Verify get_node_extra_files called for each node
                            self.assertEqual(mock_api_invoker.get_node_extra_files.call_count, 3)
                        except Exception as e:
                            print(f"Expected error: {e}")


@unittest.skip(SCAFFOLD_SKIP_REASON)
class TestCloseOutAppIntegration(unittest.TestCase):
    """Integration tests for close_out_app"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.charts_dir = os.path.join(self.test_dir, 'charts')
        os.makedirs(self.charts_dir, exist_ok=True)
        
        self.bucket_name = 'test-omicairn-bucket'
        
        self.env_vars = {
            'COMPUTATION_ID': 'integration-comp-123',
            'NODE_ID': 'integration-node-456',
            'USER_ID': 'integration-user-789',
            'BUCKET_NAME': self.bucket_name,
            'COMPUTATION_SERVER_HOST': 'http://localhost:9090',
            'MAIN_SERVER_HOST': 'http://localhost:8080',
            'SYSTEM_AGENT_KEY': 'test-integration-key',
            'PIPELINE_SUCCESS': '1'
        }

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @mock_s3
    @patch.dict(os.environ, clear=True)
    @patch('requests.post')
    def test_close_out_app_full_workflow(self, mock_post):
        """Test complete close_out_app workflow with S3 uploads"""
        os.environ.update(self.env_vars)
        
        sys.path.insert(0, str(Path(__file__).parent.parent / "close_out_app"))
        from main import close_out
        
        # Setup mock S3
        s3_client = boto3.client('s3', region_name=TEST_AWS_REGION)
        s3_client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration={'LocationConstraint': TEST_AWS_REGION},
        )
        
        # Create test chart files
        chart_path = os.path.join(self.charts_dir, 'test_plot.png')
        with open(chart_path, 'wb') as f:
            f.write(b'fake png data')
        
        # Mock API responses
        mock_login_response = Mock()
        mock_login_response.json.return_value = {'code': 200, 'data': 'test-token'}
        mock_login_response.status_code = 200
        
        mock_finished_response = Mock()
        mock_finished_response.json.return_value = {'code': 200, 'data': 'success'}
        mock_finished_response.status_code = 200
        
        mock_post.side_effect = [mock_login_response, mock_finished_response]
        
        with patch('main.get_s3_client') as mock_get_s3:
            mock_get_s3.return_value = s3_client
            
            with patch('main.APIClient') as mock_api_client_class:
                mock_api_client = Mock()
                mock_api_client_class.return_value = mock_api_client
                
                mock_api_client.get_computation_details.return_value = {
                    'computation_basic_info': {
                        'resultDataId': 'result-data-123'
                    }
                }
                
                mock_api_client.create_figure.return_value = {
                    'key': f'figures/integration-comp-123/test_plot.png',
                    'thumbnailKey': f'figures/integration-comp-123/thumbnail_test_plot.png'
                }
                
                mock_api_client.report_finished.return_value = True
                
                with patch('main.upload_charts') as mock_upload_charts:
                    with patch('main.upload_s3_folder') as mock_upload_folder:
                        mock_upload_charts.return_value = 1
                        mock_upload_folder.return_value = ['output.csv']
                        
                        try:
                            close_out()
                            
                            # Verify critical functions were called
                            mock_upload_charts.assert_called_once()
                            mock_upload_folder.assert_called_once()
                            mock_api_client.report_finished.assert_called_once()
                            
                        except Exception as e:
                            print(f"Expected error: {e}")


@unittest.skip(SCAFFOLD_SKIP_REASON)
class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end integration tests for the complete workflow"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.bucket_name = 'test-e2e-bucket'
        
        # Create directory structure
        os.makedirs(f'{self.test_dir}/omicairn/outputs/charts', exist_ok=True)
        
        self.env_vars = {
            'COMPUTATION_ID': 'e2e-comp-123',
            'NODE_ID': 'e2e-node-456',
            'USER_ID': 'e2e-user-789',
            'BUCKET_NAME': self.bucket_name,
            'MAIN_SERVER_ACCESS_PREFIX': 'http://localhost:8080',
            'COMPUTATION_SERVER_HOST': 'http://localhost:9090',
            'SYSTEM_AGENT_KEY': 'test-e2e-key',
            'PIPELINE_SUCCESS': '1',
            'PIPE_MESSAGE_PATH': f'{self.test_dir}/pipe-message'
        }

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @mock_s3
    @patch.dict(os.environ, clear=True)
    @patch('requests.post')
    @patch('requests.get')
    def test_complete_workflow_previous_to_close_out(self, mock_get, mock_post):
        """Test complete workflow from previous_app through close_out_app"""
        os.environ.update(self.env_vars)
        
        # Setup S3
        s3_client = boto3.client('s3', region_name=TEST_AWS_REGION)
        s3_client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration={'LocationConstraint': TEST_AWS_REGION},
        )
        
        # Upload input data
        input_data_id = 'input-data-123'
        s3_client.put_object(
            Bucket=self.bucket_name,
            Key=f'adata/{input_data_id}-general-s3-store/input.csv',
            Body=b'data'
        )
        
        # Mock API responses
        mock_login_response = Mock()
        mock_login_response.json.return_value = {'code': 200, 'data': 'token'}
        mock_login_response.status_code = 200
        mock_post.return_value = mock_login_response
        
        # Step 1: Run previous_app
        sys.path.insert(0, str(Path(__file__).parent.parent / "previous_app"))
        from previous_app.main import prepare as previous_prepare
        
        with patch('previous_app.main.ServerAPIInvoker') as mock_prev_api:
            mock_api = Mock()
            mock_prev_api.return_value = mock_api
            
            mock_api.get_node_information.return_value = {
                'id': 'e2e-node-456',
                'type': 'computation node',
                'dynamicGenerationId': None
            }
            
            mock_api.get_computation_details.return_value = {
                'computation_basic_info': {
                    'id': 'e2e-comp-123',
                    'computationParams': '{}',
                    'resultDataId': 'output-data-123'
                }
            }
            
            mock_api.get_branch_path.return_value = {
                'previousNodeList': [
                    {
                        'id': 'input-node',
                        'type': 'data node',
                        'dataId': input_data_id
                    }
                ],
                'previousEdgeList': []
            }
            
            mock_api.get_node_extra_files.return_value = []
            
            inputs_dict = {}
            
            with patch('builtins.open', MagicMock()):
                with patch('os.makedirs'):
                    try:
                        # This will partially execute - good enough for integration test
                        previous_prepare()
                    except Exception as e:
                        print(f"Previous app completed: {e}")
        
        # Step 2: Simulate computation (would run Claude Code here)
        # For testing, just create output files
        output_file = f'{self.test_dir}/omicairn/outputs/result.csv'
        with open(output_file, 'w') as f:
            f.write('output_col1,output_col2\nresult1,result2')
        
        # Create a chart
        chart_file = f'{self.test_dir}/omicairn/outputs/charts/analysis_plot.png'
        with open(chart_file, 'wb') as f:
            f.write(b'fake chart data')
        
        # Step 3: Run close_out_app
        sys.path.insert(0, str(Path(__file__).parent.parent / "close_out_app"))
        from close_out_app.main import close_out
        
        with patch('close_out_app.main.get_s3_client') as mock_get_s3:
            mock_get_s3.return_value = s3_client
            
            with patch('close_out_app.main.APIClient') as mock_close_api:
                mock_api_client = Mock()
                mock_close_api.return_value = mock_api_client
                
                mock_api_client.get_computation_details.return_value = {
                    'computation_basic_info': {
                        'resultDataId': 'output-data-123'
                    }
                }
                
                mock_api_client.create_figure.return_value = {
                    'key': 'figures/e2e-comp-123/plot.png',
                    'thumbnailKey': 'figures/e2e-comp-123/thumbnail_plot.png'
                }
                
                mock_api_client.report_finished.return_value = True
                
                with patch('close_out_app.main.upload_charts') as mock_charts:
                    with patch('close_out_app.main.upload_s3_folder') as mock_folder:
                        mock_charts.return_value = 1
                        mock_folder.return_value = ['result.csv']
                        
                        try:
                            close_out()
                            
                            # Verify completion was reported
                            mock_api_client.report_finished.assert_called()
                            
                        except Exception as e:
                            print(f"Close out completed: {e}")


if __name__ == '__main__':
    unittest.main()
