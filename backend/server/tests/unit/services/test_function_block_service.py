import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock, MagicMock, mock_open
import pytest
import json
import tempfile
import zipfile
from io import BytesIO

from main import create_app
from service.function_block_v1 import FunctionBlockV1Service
from constants.function_block import FunctionBlockVersionState
from exception.request.parameter_invalid import ParameterInvalidException


@pytest.mark.service
@pytest.mark.unit
class TestFunctionBlockService(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.fb_service = FunctionBlockV1Service()

    def tearDown(self):
        self.ctx.pop()

    @patch('dao.function_block_v1.function_block_v1_dao.find_by_id')
    def test_get_function_block_by_id(self, mock_find_by_id):
        mock_fb = Mock()
        mock_fb.id = 1
        mock_fb.name = "test_fb"
        mock_find_by_id.return_value = mock_fb
        
        result = self.fb_service.get_function_block_by_id(1)
        
        self.assertEqual(result, mock_fb)
        mock_find_by_id.assert_called_once_with(1)

    @patch('dao.function_block_v1.function_block_v1_dao.find_all')
    def test_get_all_function_blocks(self, mock_find_all):
        mock_fbs = [Mock(id=1), Mock(id=2)]
        mock_find_all.return_value = mock_fbs
        
        result = self.fb_service.get_all_function_blocks()
        
        self.assertEqual(len(result), 2)
        mock_find_all.assert_called_once()

    @patch('dao.function_block_v1.function_block_v1_dao.search_by_name')
    def test_search_function_blocks_by_name(self, mock_search):
        mock_fbs = [Mock(name="test_fb")]
        mock_search.return_value = mock_fbs
        
        result = self.fb_service.search_function_blocks_by_name("test")
        
        self.assertEqual(len(result), 1)
        mock_search.assert_called_once_with("test")

    def test_validate_function_block_params(self):
        # Test parameter validation
        valid_params = {"param1": "value1", "param2": 123}
        invalid_params = {"": "empty_key", "param1": None}
        
        result = self.fb_service._validate_params(valid_params)
        self.assertTrue(result)
        
        with self.assertRaises(Exception):
            self.fb_service._validate_params(invalid_params)

    @patch('service.function_block_v1.shutil.rmtree')
    @patch('service.function_block_v1.tempfile.mkdtemp')
    @patch('service.function_block_v1.PorterFactory.create_porter')
    @patch('service.function_block_v1.FunctionBlockTool.complete_args')
    @patch('dao.function_block_v1.function_block_v1_dao.update')
    @patch('dao.function_block_v1.function_block_v1_dao.update_version')
    @patch('dao.function_block_v1.function_block_v1_dao.find_version_by_id')
    def test_preprocess_function_block_version_directly_success(
        self, 
        mock_find_version,
        mock_update_version,
        mock_update,
        mock_complete_args,
        mock_create_porter,
        mock_mkdtemp,
        mock_rmtree
    ):
        """Test successful preprocessing of a function block version"""
        # Setup mock data
        function_block_version_id = 123
        function_block_id = 456
        
        # Mock function block version
        mock_fb_version = Mock()
        mock_fb_version.id = function_block_version_id
        mock_fb_version.function_block_id = function_block_id
        mock_fb_version.program_language = "Python"
        mock_find_version.return_value = mock_fb_version
        
        # Mock temp directory
        temp_dir = "mock_temp_dir"
        mock_mkdtemp.return_value = temp_dir
        
        # Mock static config
        static_config = {
            "name": "test_fb",
            "alt_name": "Test FB",
            "args": [{"name": "arg1", "type": "string"}],
            "document_url": "http://example.com/doc",
            "description": "Test function block",
            "tag": "test",
            "source": "test_source",
            "program_language": "Python",
            "plot_only": False,
            "runtime_version": "3.9",
            "preset_env": "default",
            "is_v2": True
        }
        
        # Mock completed args
        completed_args = [{"name": "arg1", "type": "string", "required": True}]
        mock_complete_args.return_value = completed_args
        
        # Mock porter (S3 operations)
        mock_porter = MagicMock()
        mock_create_porter.return_value = mock_porter
        
        # Create a mock zip file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('static-config.json', json.dumps(static_config))
            zip_file.writestr('index.py', 'print("Hello World")')
        zip_buffer.seek(0)
        
        # Mock porter.fetch_file to save the zip content
        def mock_fetch_file(local_path):
            with open(local_path, 'wb') as f:
                f.write(zip_buffer.getvalue())
        
        mock_porter.fetch_file.side_effect = mock_fetch_file
        mock_porter.list_files.return_value = []
        
        # Execute the method
        with patch('builtins.open', side_effect=open):
            with patch('os.path.exists', return_value=True):
                with patch('os.walk', return_value=[
                    (f'{temp_dir}/raw-fb', [], ['static-config.json', 'index.py'])
                ]):
                    self.fb_service.preprocess_function_block_version_directly(function_block_version_id)
        
        # Verify the method calls
        # 1. Version should be fetched
        mock_find_version.assert_called_with(function_block_version_id)
        
        # 2. State should be updated to PREHANDLING
        mock_update_version.assert_any_call(function_block_version_id, {
            "state": FunctionBlockVersionState.PREHANDLING.value
        })
        
        # 3. Args should be completed
        mock_complete_args.assert_called_once()
        
        # 4. Version should be updated with final values
        expected_update_call = {
            "args": json.dumps(completed_args),
            "document_url": static_config["document_url"],
            "description": static_config["description"],
            "tag": static_config["tag"],
            "source": static_config["source"],
            "program_language": static_config["program_language"],
            "plot_only": static_config["plot_only"],
            "runtime_version": static_config["runtime_version"],
            "preset_env": static_config["preset_env"],
            "alt_name": static_config["alt_name"],
            "name": static_config["name"],
            "is_v2": static_config["is_v2"],
            "state": FunctionBlockVersionState.OK.value
        }
        mock_update_version.assert_called_with(function_block_version_id, expected_update_call)
        
        # 5. Function block should be updated
        mock_update.assert_called_once_with(function_block_id, {
            "current_version_id": function_block_version_id,
            "alt_name": static_config["alt_name"]
        })
        
        # 6. Temp directory should be cleaned up
        mock_rmtree.assert_called_once_with(temp_dir)

    @patch('dao.function_block_v1.function_block_v1_dao.find_version_by_id')
    def test_preprocess_function_block_version_directly_invalid_version(self, mock_find_version):
        """Test preprocessing with invalid function block version ID"""
        function_block_version_id = 999
        mock_find_version.return_value = None
        
        with self.assertRaises(ParameterInvalidException) as context:
            self.fb_service.preprocess_function_block_version_directly(function_block_version_id)
        
        self.assertIn("invalid function block version", str(context.exception))

    @patch('service.function_block_v1.tempfile.mkdtemp')
    @patch('service.function_block_v1.PorterFactory.create_porter')
    @patch('dao.function_block_v1.function_block_v1_dao.update_version')
    @patch('dao.function_block_v1.function_block_v1_dao.find_version_by_id')
    def test_preprocess_function_block_version_directly_missing_static_config(
        self,
        mock_find_version,
        mock_update_version,
        mock_create_porter,
        mock_mkdtemp
    ):
        """Test preprocessing when static-config.json is missing"""
        function_block_version_id = 123
        
        # Mock function block version
        mock_fb_version = Mock()
        mock_fb_version.id = function_block_version_id
        mock_fb_version.function_block_id = 456
        mock_find_version.return_value = mock_fb_version
        
        # Mock temp directory
        temp_dir = "mock_temp_dir"
        mock_mkdtemp.return_value = temp_dir
        
        # Mock porter
        mock_porter = MagicMock()
        mock_create_porter.return_value = mock_porter
        
        # Create a zip without static-config.json
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('index.py', 'print("Hello World")')
        zip_buffer.seek(0)
        
        def mock_fetch_file(local_path):
            with open(local_path, 'wb') as f:
                f.write(zip_buffer.getvalue())
        
        mock_porter.fetch_file.side_effect = mock_fetch_file
        
        # Execute and expect exception
        with patch('builtins.open', side_effect=open):
            with patch('os.path.exists', return_value=False):
                with self.assertRaises(Exception) as context:
                    self.fb_service.preprocess_function_block_version_directly(function_block_version_id)
                
                self.assertIn("lack of static_config.json", str(context.exception))

    @patch('service.function_block_v1.shutil.rmtree')
    @patch('service.function_block_v1.tempfile.mkdtemp')
    @patch('service.function_block_v1.PorterFactory.create_porter')
    @patch('service.function_block_v1.FunctionBlockTool.complete_args')
    @patch('dao.function_block_v1.function_block_v1_dao.update_version')
    @patch('dao.function_block_v1.function_block_v1_dao.find_version_by_id')
    def test_preprocess_function_block_version_directly_with_default_values(
        self,
        mock_find_version,
        mock_update_version,
        mock_complete_args,
        mock_create_porter,
        mock_mkdtemp,
        mock_rmtree
    ):
        """Test preprocessing with minimal static-config.json (using default values)"""
        function_block_version_id = 123
        function_block_id = 456
        
        # Mock function block version
        mock_fb_version = Mock()
        mock_fb_version.id = function_block_version_id
        mock_fb_version.function_block_id = function_block_id
        mock_find_version.return_value = mock_fb_version
        
        # Mock temp directory
        temp_dir = "mock_temp_dir"
        mock_mkdtemp.return_value = temp_dir
        
        # Minimal static config
        static_config = {
            "name": "test_fb"
        }
        
        mock_complete_args.return_value = []
        
        # Mock porter
        mock_porter = MagicMock()
        mock_create_porter.return_value = mock_porter
        
        # Create mock zip
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('static-config.json', json.dumps(static_config))
        zip_buffer.seek(0)
        
        def mock_fetch_file(local_path):
            with open(local_path, 'wb') as f:
                f.write(zip_buffer.getvalue())
        
        mock_porter.fetch_file.side_effect = mock_fetch_file
        mock_porter.list_files.return_value = []
        
        # Execute
        with patch('builtins.open', side_effect=open):
            with patch('os.path.exists', return_value=True):
                with patch('os.walk', return_value=[
                    (f'{temp_dir}/raw-fb', [], ['static-config.json'])
                ]):
                    self.fb_service.preprocess_function_block_version_directly(function_block_version_id)
        
        # Verify default values are used
        final_update_call = mock_update_version.call_args_list[-1][0][1]
        self.assertEqual(final_update_call["name"], "test_fb")
        self.assertEqual(final_update_call["program_language"], "Python")
        self.assertFalse(final_update_call["plot_only"])
        self.assertFalse(final_update_call["is_v2"])
        self.assertEqual(final_update_call["state"], FunctionBlockVersionState.OK.value)

    @patch('dao.function_block_v1.function_block_v1_dao.find_version_by_is_v2_and_user_id')
    def test_get_existing_public_fbvs_v2(self, mock_find_version):
        """Test getting all public FBv2 versions"""
        # Mock v2 function block versions
        mock_fbv1 = Mock()
        mock_fbv1.id = 1
        mock_fbv1.name = "FB v2 Test 1"
        mock_fbv1.is_v2 = True
        
        mock_fbv2 = Mock()
        mock_fbv2.id = 2
        mock_fbv2.name = "FB v2 Test 2"
        mock_fbv2.is_v2 = True
        
        mock_fbv3 = Mock()
        mock_fbv3.id = 3
        mock_fbv3.name = "FB v2 Test 3"
        mock_fbv3.is_v2 = True
        
        mock_versions = [mock_fbv1, mock_fbv2, mock_fbv3]
        mock_find_version.return_value = mock_versions
        
        # Execute
        result = self.fb_service.get_existing_public_fbvs_v2()
        
        # Verify
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 2)
        self.assertEqual(result[2].id, 3)
        self.assertTrue(all(fbv.is_v2 for fbv in result))
        
        # Verify DAO was called with correct parameters
        from constants.authority import SpecialUserId
        mock_find_version.assert_called_once_with(True, SpecialUserId.PUBLIC.value)

    @patch('dao.function_block_v1.function_block_v1_dao.find_version_by_is_v2_and_user_id')
    def test_get_existing_public_fbvs_v2_empty_result(self, mock_find_version):
        """Test getting public FBv2 versions when none exist"""
        mock_find_version.return_value = []
        
        # Execute
        result = self.fb_service.get_existing_public_fbvs_v2()
        
        # Verify
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)
        
        # Verify DAO was called
        from constants.authority import SpecialUserId
        mock_find_version.assert_called_once_with(True, SpecialUserId.PUBLIC.value)
