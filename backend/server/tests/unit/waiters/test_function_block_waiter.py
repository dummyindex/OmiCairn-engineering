import sys
sys.path.append('../..')
import unittest
from unittest.mock import patch, MagicMock
import json

from waiter.function_block_v1_waiter import FunctionBlockV1Waiter
from constants.sss import FUNCTION_BLOCK_VERSION_PREFIX, BUCKET_NAME


class TestFunctionBlockV1Waiter(unittest.TestCase):
    """Test the functionality of the FunctionBlockV1Waiter class"""
    
    def setUp(self):
        """Set up before each test"""
        self.function_block_version_id = "test_fb_version_123"
        self.python_waiter = FunctionBlockV1Waiter(
            function_block_version_id=self.function_block_version_id,
            programming_language="Python"
        )
        self.r_waiter = FunctionBlockV1Waiter(
            function_block_version_id=self.function_block_version_id,
            programming_language="R"
        )
        self.none_waiter = FunctionBlockV1Waiter(
            function_block_version_id=self.function_block_version_id,
            programming_language=None
        )
    
    def tearDown(self):
        """Clean up after each test"""
        pass
    
    def test_init_with_python_language(self):
        """Test initialization for the Python language"""
        self.assertEqual(self.python_waiter.function_block_version_id, self.function_block_version_id)
        self.assertEqual(self.python_waiter.programming_language, "Python")
        self.assertEqual(self.python_waiter.requirements_file_name, "requirements.txt")
        self.assertEqual(self.python_waiter.core_code_file_name, "function_block.py")
        self.assertEqual(self.python_waiter.install_script_file_name, "install.sh")
        self.assertEqual(self.python_waiter.static_config_file_name, "static-config.json")
    
    def test_init_with_r_language(self):
        """Test initialization for the R language"""
        self.assertEqual(self.r_waiter.function_block_version_id, self.function_block_version_id)
        self.assertEqual(self.r_waiter.programming_language, "R")
        self.assertEqual(self.r_waiter.requirements_file_name, "libs.R")
        self.assertEqual(self.r_waiter.core_code_file_name, "function_block.R")
        self.assertEqual(self.r_waiter.install_script_file_name, "install.sh")
        self.assertEqual(self.r_waiter.static_config_file_name, "static-config.json")
    
    def test_init_with_none_language(self):
        """Test initialization with language None (should log a warning)"""
        self.assertEqual(self.none_waiter.function_block_version_id, self.function_block_version_id)
        self.assertEqual(self.none_waiter.programming_language, None)
        self.assertEqual(self.none_waiter.requirements_file_name, "libs.R")  # defaults to R
        self.assertEqual(self.none_waiter.core_code_file_name, "function_block.R")  # defaults to R
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_fetch_static_config_success(self, mock_porter_factory):
        """Test successfully fetching the static config"""
        # Mock static config data
        mock_config = {
            "name": "test_function_block",
            "version": "1.0.0",
            "description": "Test function block"
        }
        mock_config_json = json.dumps(mock_config)
        mock_config_bytes = mock_config_json.encode('utf-8')
        
        # Set up mock objects
        mock_porter = MagicMock()
        mock_porter.fetch_file_stream.return_value = mock_config_bytes
        mock_porter_factory.return_value = mock_porter
        
        # Run the test
        result = self.python_waiter.fetch_static_config()
        
        # Verify results
        self.assertEqual(result, mock_config)
        mock_porter_factory.assert_called_once()
        mock_porter.set_operation_target.assert_called_once_with(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/static-config.json"
        )
        mock_porter.fetch_file_stream.assert_called_once()
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_fetch_core_code_success(self, mock_porter_factory):
        """Test successfully fetching the core code"""
        # Mock core code
        mock_code = "def test_function():\n    return 'Hello World'"
        mock_code_bytes = mock_code.encode('utf-8')
        
        # Set up mock objects
        mock_porter = MagicMock()
        mock_porter.fetch_file_stream.return_value = mock_code_bytes
        mock_porter_factory.return_value = mock_porter
        
        # Run the test
        result = self.python_waiter.fetch_core_code()
        
        # Verify results
        self.assertEqual(result, mock_code)
        mock_porter_factory.assert_called_once()
        mock_porter.set_operation_target.assert_called_once_with(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/function_block.py"
        )
        mock_porter.fetch_file_stream.assert_called_once()
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_fetch_requirement_content_success(self, mock_porter_factory):
        """Test successfully fetching the requirements file content"""
        # Mock requirements file content
        mock_requirements = "pandas==1.3.0\nnumpy==1.21.0"
        mock_requirements_bytes = mock_requirements.encode('utf-8')
        
        # Set up mock objects
        mock_porter = MagicMock()
        mock_porter.fetch_file_stream.return_value = mock_requirements_bytes
        mock_porter_factory.return_value = mock_porter
        
        # Run the test
        result = self.python_waiter.fetch_requirement_content()
        
        # Verify results
        self.assertEqual(result, mock_requirements)
        mock_porter_factory.assert_called_once()
        mock_porter.set_operation_target.assert_called_once_with(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/requirements.txt"
        )
        mock_porter.fetch_file_stream.assert_called_once()
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_fetch_requirement_content_no_such_key(self, mock_porter_factory):
        """Test fetching requirements file content when the file does not exist"""
        # Configure the mock to raise a NoSuchKey exception
        mock_porter = MagicMock()
        mock_porter.fetch_file_stream.side_effect = Exception("NoSuchKey: The specified key does not exist")
        mock_porter_factory.return_value = mock_porter
        
        # Run the test
        result = self.python_waiter.fetch_requirement_content()
        
        # Verify results
        self.assertIsNone(result)
        mock_porter_factory.assert_called_once()
        mock_porter.set_operation_target.assert_called_once_with(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/requirements.txt"
        )
        mock_porter.fetch_file_stream.assert_called_once()
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_fetch_install_script_success(self, mock_porter_factory):
        """Test successfully fetching the install script"""
        # Mock install script content
        mock_script = "#!/bin/bash\necho 'Installing dependencies...'"
        mock_script_bytes = mock_script.encode('utf-8')
        
        # Set up mock objects
        mock_porter = MagicMock()
        mock_porter.fetch_file_stream.return_value = mock_script_bytes
        mock_porter_factory.return_value = mock_porter
        
        # Run the test
        result = self.python_waiter.fetch_install_script()
        
        # Verify results
        self.assertEqual(result, mock_script)
        mock_porter_factory.assert_called_once()
        mock_porter.set_operation_target.assert_called_once_with(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/install.sh"
        )
        mock_porter.fetch_file_stream.assert_called_once()
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_fetch_install_script_no_such_key(self, mock_porter_factory):
        """Test fetching the install script when the file does not exist"""
        # Configure the mock to raise a NoSuchKey exception
        mock_porter = MagicMock()
        mock_porter.fetch_file_stream.side_effect = Exception("NoSuchKey: The specified key does not exist")
        mock_porter_factory.return_value = mock_porter
        
        # Run the test
        result = self.python_waiter.fetch_install_script()
        
        # Verify results
        self.assertIsNone(result)
        mock_porter_factory.assert_called_once()
        mock_porter.set_operation_target.assert_called_once_with(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/install.sh"
        )
        mock_porter.fetch_file_stream.assert_called_once()
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_get_raw_fb_zip_upload_info(self, mock_porter_factory):
        """Test fetching upload info for the original function block ZIP"""
        # Mock upload info
        mock_upload_info = {
            "url": "https://example.com/upload",
            "fields": {
                "key": f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}.raw-fb-zip",
                "policy": "mock_policy"
            }
        }
        
        # Set up mock objects
        mock_porter = MagicMock()
        mock_porter.get_presigned_post.return_value = mock_upload_info
        mock_porter_factory.return_value = mock_porter
        
        file_size = 1024
        
        # Run the test
        result = self.python_waiter.get_raw_fb_zip_upload_info(file_size)
        
        # Verify results
        self.assertEqual(result, mock_upload_info)
        mock_porter_factory.assert_called_once()
        mock_porter.set_operation_target.assert_called_once_with(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}.raw-fb-zip"
        )
        mock_porter.get_presigned_post.assert_called_once_with(file_size, 60 * 60)
    
    def test_fetch_doc(self):
        """Test fetching documentation (currently an empty implementation)"""
        result = self.python_waiter.fetch_doc()
        self.assertIsNone(result)
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_fetch_preview_images_list_success(self, mock_porter_factory):
        """Test successfully fetching the preview image list"""
        # Mock image file list
        mock_image_files = [
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/preview-images/image1.png",
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/preview-images/image2.jpg"
        ]
        
        # Mock presigned URLs
        mock_urls = [
            "https://example.com/image1.png?signature=abc123",
            "https://example.com/image2.jpg?signature=def456"
        ]
        
        # Set up mock objects
        mock_porter = MagicMock()
        mock_porter.list_files.return_value = mock_image_files
        mock_porter.get_presigned_url.side_effect = mock_urls
        mock_porter_factory.return_value = mock_porter
        
        # Run the test
        result = self.python_waiter.fetch_preview_images_list()
        
        # Verify results
        self.assertEqual(result, mock_urls)
        mock_porter_factory.assert_called_once()
        # Verify set_operation_target was called the correct number of times (1 for listing files + 1 per image file, 2 images)
        self.assertEqual(mock_porter.set_operation_target.call_count, 3)
        # Verify the list-files target call
        mock_porter.set_operation_target.assert_any_call(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/preview-images/"
        )
        # Verify the list_files call
        mock_porter.list_files.assert_called_once_with(recursive=False)
        # Verify the get_presigned_url calls
        self.assertEqual(mock_porter.get_presigned_url.call_count, 2)
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_fetch_preview_images_list_empty(self, mock_porter_factory):
        """Test fetching an empty preview image list"""
        # Configure the mock to return an empty list
        mock_porter = MagicMock()
        mock_porter.list_files.return_value = []
        mock_porter_factory.return_value = mock_porter
        
        # Run the test
        result = self.python_waiter.fetch_preview_images_list()
        
        # Verify results
        self.assertEqual(result, [])
        mock_porter_factory.assert_called_once()
        mock_porter.set_operation_target.assert_called_once_with(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/preview-images/"
        )
        mock_porter.list_files.assert_called_once_with(recursive=False)
        # Verify get_presigned_url was not called
        mock_porter.get_presigned_url.assert_not_called()
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_fetch_static_config_json_decode_error(self, mock_porter_factory):
        """Test JSON parse error when fetching the static config"""
        # Mock invalid JSON content
        mock_invalid_json = "invalid json content"
        mock_invalid_json_bytes = mock_invalid_json.encode('utf-8')
        
        # Set up mock objects
        mock_porter = MagicMock()
        mock_porter.fetch_file_stream.return_value = mock_invalid_json_bytes
        mock_porter_factory.return_value = mock_porter
        
        # Run the test and expect a JSON decode error
        with self.assertRaises(json.JSONDecodeError):
            self.python_waiter.fetch_static_config()
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_fetch_core_code_with_r_language(self, mock_porter_factory):
        """Test fetching core code for the R language"""
        # Mock R code
        mock_r_code = "test_function <- function() {\n  return('Hello World')\n}"
        mock_r_code_bytes = mock_r_code.encode('utf-8')
        
        # Set up mock objects
        mock_porter = MagicMock()
        mock_porter.fetch_file_stream.return_value = mock_r_code_bytes
        mock_porter_factory.return_value = mock_porter
        
        # Run the test
        result = self.r_waiter.fetch_core_code()
        
        # Verify results
        self.assertEqual(result, mock_r_code)
        mock_porter.set_operation_target.assert_called_once_with(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/function_block.R"
        )
    
    @patch('waiter.function_block_v1_waiter.PorterFactory.create_porter')
    def test_fetch_requirement_content_with_r_language(self, mock_porter_factory):
        """Test fetching the requirements file for the R language"""
        # Mock R requirements file content
        mock_r_libs = "library(dplyr)\nlibrary(ggplot2)"
        mock_r_libs_bytes = mock_r_libs.encode('utf-8')
        
        # Set up mock objects
        mock_porter = MagicMock()
        mock_porter.fetch_file_stream.return_value = mock_r_libs_bytes
        mock_porter_factory.return_value = mock_porter
        
        # Run the test
        result = self.r_waiter.fetch_requirement_content()
        
        # Verify results
        self.assertEqual(result, mock_r_libs)
        mock_porter.set_operation_target.assert_called_once_with(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/libs.R"
        )


if __name__ == '__main__':
    unittest.main()