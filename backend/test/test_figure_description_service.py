import unittest
from unittest.mock import patch, MagicMock, Mock
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from service.figure_description import FigureDescriptionService


class TestFigureDescriptionService(unittest.TestCase):
    
    def setUp(self):
        self.service = FigureDescriptionService()
        self.test_figure_uuid = 'test-uuid-123.png'
        self.test_figure_name = 'test_plot.png'
        self.test_node_name = 'Test Node'
        self.test_user_id = 'test-user-123'
    
    @patch('service.figure_description.attached_data_service.get_figure_download_info')
    @patch.object(FigureDescriptionService, '__init__', lambda x: None)
    def test_generate_figure_description_success(self, mock_get_url):
        service = FigureDescriptionService()
        service.llm_interface = MagicMock()
        
        mock_get_url.return_value = 'https://example.com/figure.png'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'description': 'Test description'
        }
        service.llm_interface.generate_figure_description.return_value = mock_response
        
        result = service.generate_figure_description(
            self.test_figure_uuid,
            self.test_figure_name,
            self.test_node_name,
            self.test_user_id
        )
        
        self.assertEqual(result.status_code, 200)
        mock_get_url.assert_called_once_with(self.test_figure_uuid)
        service.llm_interface.generate_figure_description.assert_called_once_with(
            figure_url='https://example.com/figure.png',
            figure_uuid=self.test_figure_uuid,
            figure_name=self.test_figure_name,
            node_name=self.test_node_name,
            user_id=self.test_user_id
        )
    
    @patch('service.figure_description.attached_data_service.get_figure_download_info')
    def test_generate_figure_description_no_url(self, mock_get_url):
        mock_get_url.return_value = None
        
        result = self.service.generate_figure_description(
            self.test_figure_uuid,
            self.test_figure_name
        )
        
        self.assertIsNone(result)
        mock_get_url.assert_called_once_with(self.test_figure_uuid)
    
    @patch('service.figure_description.attached_data_service.get_figure_download_info')
    @patch.object(FigureDescriptionService, '__init__', lambda x: None)
    def test_batch_generate_descriptions(self, mock_get_url):
        service = FigureDescriptionService()
        service.llm_interface = MagicMock()
        
        test_figures = [
            {
                'figure_uuid': 'uuid1',
                'figure_name': 'fig1.png',
                'node_name': 'Node1'
            },
            {
                'figure_uuid': 'uuid2',
                'figure_name': 'fig2.png',
                'node_name': 'Node2'
            }
        ]
        
        mock_get_url.side_effect = ['https://example.com/fig1.png', 'https://example.com/fig2.png']
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'successful': 2,
                'failed': 0
            }
        }
        service.llm_interface.batch_generate_figure_descriptions.return_value = mock_response
        
        result = service.batch_generate_descriptions(test_figures, self.test_user_id)
        
        self.assertEqual(result.status_code, 200)
        self.assertEqual(mock_get_url.call_count, 2)
        service.llm_interface.batch_generate_figure_descriptions.assert_called_once()
        
        call_args = service.llm_interface.batch_generate_figure_descriptions.call_args[1]
        self.assertEqual(len(call_args['figures']), 2)
        self.assertEqual(call_args['figures'][0]['figure_url'], 'https://example.com/fig1.png')
        self.assertEqual(call_args['user_id'], self.test_user_id)
    
    @patch.object(FigureDescriptionService, '__init__', lambda x: None)
    def test_get_figure_description_exists(self):
        service = FigureDescriptionService()
        service.porter = MagicMock()
        
        service.porter.check_file.return_value = True
        service.porter.fetch_file_stream.return_value = b'Test description content'
        
        result = service.get_figure_description('test-uuid.png')
        
        self.assertEqual(result, 'Test description content')
        service.porter.set_operation_target.assert_called_with('figure-descriptions/test-uuid.txt')
        service.porter.check_file.assert_called_once()
        service.porter.fetch_file_stream.assert_called_once()
    
    @patch.object(FigureDescriptionService, '__init__', lambda x: None)
    def test_get_figure_description_not_exists(self):
        service = FigureDescriptionService()
        service.porter = MagicMock()
        
        service.porter.check_file.return_value = False
        
        result = service.get_figure_description('test-uuid.png')
        
        self.assertIsNone(result)
        service.porter.set_operation_target.assert_called_with('figure-descriptions/test-uuid.txt')
        service.porter.check_file.assert_called_once()
        service.porter.fetch_file_stream.assert_not_called()
    
    @patch.object(FigureDescriptionService, '__init__', lambda x: None)
    def test_check_description_exists(self):
        service = FigureDescriptionService()
        service.porter = MagicMock()
        
        service.porter.check_file.return_value = True
        
        result = service.check_description_exists('test-uuid.png')
        
        self.assertTrue(result)
        service.porter.set_operation_target.assert_called_with('figure-descriptions/test-uuid.txt')
        service.porter.check_file.assert_called_once()
    
    def test_batch_generate_descriptions_no_valid_figures(self):
        test_figures = [
            {
                'figure_uuid': 'uuid1',
                # Missing figure_name
            },
            {
                'figure_name': 'fig2.png',
                # Missing figure_uuid
            }
        ]
        
        result = self.service.batch_generate_descriptions(test_figures, self.test_user_id)
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'No valid figures to process')
    
    @patch('service.figure_description.attached_data_service.get_figure_download_info')
    def test_error_handling_in_generate_description(self, mock_get_url):
        mock_get_url.side_effect = Exception("Connection error")
        
        result = self.service.generate_figure_description(
            self.test_figure_uuid,
            self.test_figure_name
        )
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()