import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")
from main import create_app
import unittest
from unittest.mock import patch, MagicMock
from flask import jsonify

from service.analysis import analysis_service

class TestTotalComputationTimeAPI(unittest.TestCase):
    # Set up
    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()
        # The endpoint now checks analysis authority; stub the guardian (no DB in unit tests).
        self.guardian_patcher = patch('controller.analysis.AuthorityGuardianFactory.get_authority_guardian')
        self.guardian_patcher.start()

    # Tear down
    def tearDown(self):
        self.guardian_patcher.stop()
        self.ctx.pop()

    @patch('service.analysis.analysis_service.calculate_total_duration', return_value=100)
    def test_get_total_computation_time(self, mock_calculate_total_duration: MagicMock):
        response = self.client.get('/analysis/total-computation-time?analysis_id=1')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('data', response_data)
        self.assertIn('total_duration', response_data['data'])
        self.assertEqual(response_data['data']['total_duration'], 100)
        mock_calculate_total_duration.assert_called_once_with('1')

    @patch('service.analysis.analysis_service.calculate_total_duration', return_value=100)
    def test_get_total_computation_time_invalid_id(self, mock_calculate_total_duration: MagicMock):
        response = self.client.get('/analysis/total-computation-time?analysis_id=invalid_id')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('data', response_data)
        self.assertIn('total_duration', response_data['data'])
        self.assertEqual(response_data['data']['total_duration'], 100)
        mock_calculate_total_duration.assert_called_once_with('invalid_id')
