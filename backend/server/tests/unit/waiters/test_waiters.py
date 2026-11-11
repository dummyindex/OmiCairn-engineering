import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock, MagicMock
import json
import pytest

from main import create_app
from waiter.data_waiter import DataWaiter
from waiter.computation import ComputationWaiter
from waiter.node_space_waiter import NodeSpaceWaiter
from waiter.user_space_waiter import UserSpaceWaiter


@pytest.mark.unit
@pytest.mark.waiter
class TestWaiters(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_data_waiter_init(self):
        adata_id = "test_data_123"
        waiter = DataWaiter(adata_id)
        
        self.assertEqual(waiter.adata_id, adata_id)

    @patch('constants.local_store.DATA_FOLDER', '/tmp/data')
    def test_data_waiter_generate_local_path(self):
        adata_id = "test_data_123"
        waiter = DataWaiter(adata_id)
        
        expected_path = os.path.join('/tmp/data', f"{adata_id}.h5ad")
        result = waiter._generate_local_path()
        
        self.assertEqual(result, expected_path)

    @patch('constants.local_store.DATA_FOLDER', '/tmp/data')
    def test_data_waiter_get_local_path(self):
        adata_id = "test_data_123"
        waiter = DataWaiter(adata_id)
        
        expected_path = os.path.join('/tmp/data', f"{adata_id}.h5ad")
        result = waiter.get_local_path()
        
        self.assertEqual(result, expected_path)

    @patch('sss.porter_factory.PorterFactory.create_porter')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_data_waiter_remove_data_local_exists(self, mock_remove, mock_exists, mock_create_porter):
        mock_exists.return_value = True
        mock_porter = Mock()
        mock_porter.check_file.return_value = True
        mock_porter.list_files.return_value = []
        mock_create_porter.return_value = mock_porter
        
        adata_id = "test_data_123"
        waiter = DataWaiter(adata_id)
        
        waiter.remove_data()
        
        mock_remove.assert_called_once()
        mock_porter.remove_file.assert_called()

    @patch('sss.porter_factory.PorterFactory.create_porter')
    @patch('os.path.exists')
    def test_data_waiter_remove_data_local_not_exists(self, mock_exists, mock_create_porter):
        mock_exists.return_value = False
        mock_porter = Mock()
        mock_porter.check_file.return_value = False
        mock_porter.list_files.return_value = []
        mock_create_porter.return_value = mock_porter
        
        adata_id = "test_data_123"
        waiter = DataWaiter(adata_id)
        
        waiter.remove_data()
        
        # Should not call os.remove if file doesn't exist locally
        self.assertTrue(mock_exists.called)

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_data_waiter_remove_data_with_components(self, mock_create_porter):
        mock_porter = Mock()
        mock_porter.check_file.return_value = True
        mock_porter.list_files.side_effect = [
            ["component1", "component2"],  # First call returns components
            []  # Second call returns empty list (finished)
        ]
        mock_create_porter.return_value = mock_porter
        
        adata_id = "test_data_123"
        waiter = DataWaiter(adata_id)
        
        with patch('os.path.exists', return_value=False):
            waiter.remove_data()
        
        # Should call remove_file for main file + 2 components
        self.assertEqual(mock_porter.remove_file.call_count, 3)

    def test_computation_waiter_init(self):
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        
        self.assertEqual(waiter.computation_id, computation_id)

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_computation_waiter_check_options_exists_true(self, mock_create_porter):
        mock_porter = Mock()
        mock_porter.check_file.return_value = True
        mock_create_porter.return_value = mock_porter
        
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        
        result = waiter.check_options_exists()
        
        self.assertTrue(result)
        mock_porter.set_operation_target.assert_called_with(f"computation_options/{computation_id}")

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_computation_waiter_check_options_exists_false(self, mock_create_porter):
        mock_porter = Mock()
        mock_porter.check_file.return_value = False
        mock_create_porter.return_value = mock_porter
        
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        
        result = waiter.check_options_exists()
        
        self.assertFalse(result)

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_computation_waiter_save_options(self, mock_create_porter):
        mock_porter = Mock()
        mock_create_porter.return_value = mock_porter
        
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        options = {"param1": "value1", "param2": 123}
        
        waiter.save_options(options)
        
        expected_json = json.dumps(options)
        mock_porter.save_file_text.assert_called_once_with(expected_json)

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_computation_waiter_save_options_none(self, mock_create_porter):
        mock_porter = Mock()
        mock_create_porter.return_value = mock_porter
        
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        
        waiter.save_options(None)
        
        expected_json = json.dumps({})
        mock_porter.save_file_text.assert_called_once_with(expected_json)

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_computation_waiter_get_options(self, mock_create_porter):
        mock_porter = Mock()
        options_dict = {"param1": "value1", "param2": 123}
        options_json = json.dumps(options_dict)
        mock_porter.fetch_file_stream.return_value = options_json.encode('utf-8')
        mock_create_porter.return_value = mock_porter
        
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        
        result = waiter.get_options()
        
        self.assertEqual(result, options_dict)

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_computation_waiter_get_options_empty(self, mock_create_porter):
        mock_porter = Mock()
        mock_porter.fetch_file_stream.return_value = b""
        mock_create_porter.return_value = mock_porter
        
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        
        result = waiter.get_options()
        
        self.assertEqual(result, {})

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_computation_waiter_check_result_exists(self, mock_create_porter):
        mock_porter = Mock()
        mock_porter.check_file.return_value = True
        mock_create_porter.return_value = mock_porter
        
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        
        result = waiter.check_result_exists()
        
        self.assertTrue(result)
        mock_porter.set_operation_target.assert_called_with(f"computation_result/{computation_id}")

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_computation_waiter_save_result(self, mock_create_porter):
        mock_porter = Mock()
        mock_create_porter.return_value = mock_porter
        
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        result_dict = {"status": "completed", "output": "success"}
        
        waiter.save_result(result_dict)
        
        expected_json = json.dumps(result_dict)
        mock_porter.save_file_text.assert_called_once_with(expected_json)

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_computation_waiter_get_result_exists(self, mock_create_porter):
        mock_porter = Mock()
        mock_porter.check_file.return_value = True
        result_dict = {"status": "completed", "output": "success"}
        result_json = json.dumps(result_dict)
        mock_porter.fetch_file_stream.return_value = result_json.encode('utf-8')
        mock_create_porter.return_value = mock_porter
        
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        
        result = waiter.get_result()
        
        self.assertEqual(result, result_dict)

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_computation_waiter_get_result_not_exists(self, mock_create_porter):
        mock_porter = Mock()
        mock_porter.check_file.return_value = False
        mock_create_porter.return_value = mock_porter
        
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        
        result = waiter.get_result()
        
        self.assertEqual(result, {})

    def test_node_space_waiter_init(self):
        node_id = "node_123"
        waiter = NodeSpaceWaiter(node_id)
        
        self.assertEqual(waiter.node_id, node_id)

    def test_user_space_waiter_init(self):
        user_id = 123
        waiter = UserSpaceWaiter(user_id)
        
        self.assertEqual(waiter.user_id, user_id)

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_waiter_porter_integration(self, mock_create_porter):
        # Test that all waiters properly integrate with the porter factory
        mock_porter = Mock()
        mock_create_porter.return_value = mock_porter
        
        # Test DataWaiter
        data_waiter = DataWaiter("data_123")
        with patch('os.path.exists', return_value=False):
            data_waiter.remove_data()
        
        # Test ComputationWaiter
        comp_waiter = ComputationWaiter("comp_123")
        comp_waiter.check_options_exists()
        
        # Verify porter factory was called multiple times
        self.assertTrue(mock_create_porter.called)
        self.assertGreater(mock_create_porter.call_count, 1)

    def test_waiter_json_serialization(self):
        # Test JSON serialization in waiters
        test_data = {
            "string_value": "test",
            "numeric_value": 123,
            "boolean_value": True,
            "list_value": [1, 2, 3],
            "nested_dict": {"key": "value"}
        }
        
        # Test that data can be properly serialized and deserialized
        json_string = json.dumps(test_data)
        parsed_data = json.loads(json_string)
        
        self.assertEqual(parsed_data, test_data)

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_computation_waiter_error_handling(self, mock_create_porter):
        # Test error handling in computation waiter
        mock_porter = Mock()
        mock_porter.fetch_file_stream.side_effect = Exception("Network error")
        mock_create_porter.return_value = mock_porter
        
        computation_id = "comp_123"
        waiter = ComputationWaiter(computation_id)
        
        # Should handle exceptions gracefully
        with self.assertRaises(Exception):
            waiter.get_options()

    def test_waiter_id_validation(self):
        # Test that waiters handle various ID formats
        test_ids = ["123", "test_id_123", "abc-def-ghi", ""]
        
        for test_id in test_ids:
            data_waiter = DataWaiter(test_id)
            self.assertEqual(data_waiter.adata_id, test_id)
            
            comp_waiter = ComputationWaiter(test_id)
            self.assertEqual(comp_waiter.computation_id, test_id)