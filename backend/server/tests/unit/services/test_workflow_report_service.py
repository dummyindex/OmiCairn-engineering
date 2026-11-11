import sys
sys.path.append('../..')
from main import create_app
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from model.workflow_report import WorkflowReport
from service.workflow_report import WorkflowReportService
import json

class TestWorkflowReportService(unittest.TestCase):
    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()
        self.workflow_report_service = WorkflowReportService()
        self.workflow_report = WorkflowReport(
            id=1,
            uuid="test-uuid",
            name="Test Report",
            created_time=datetime.now(),
            updated_time=datetime.now(),
            user_id=1,
            analysis_id=1,
            node_id_list="1,2,3",
            figure_list="[]",
            url = "123",
            status = "pending"
        )
        
    def tearDown(self):
        self.ctx.pop()

    @patch('service.workflow_report.WorkflowReportService.create_report', return_value=MagicMock(to_dict=lambda: {
        "report_id": 1,
        "uuid": "test-uuid",
        "report_name": "Test Report",
        "created_time": 1625164800000,
        "updated_time": 1625164800000,
        "user_id": 1,
        "analysis_id": 1,
        "node_id_list": "1,2,3",
        "figure_list": "[]",
        "url" : "13jfdhs",
        "status" : "pending"
    }))
    def test_create_report(self, mock_create_report: MagicMock):
        response = self.client.post('/workflow-report/create', data=json.dumps({
            "report_name": "Test Report",
            "user_id": 1,
            "analysis_id": 1,
            "node_ids": "1,2,3",
            "figure_list": "[]"
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)  
        response_data = response.get_json()
        self.assertIn('data', response_data)
        self.assertIn('uuid', response_data['data'])
        self.assertEqual(response_data['data']['uuid'], "test-uuid")

    @patch('service.workflow_report.WorkflowReportService.get_report_by_uuid', return_value=MagicMock(to_dict=lambda: {
        "report_id": 1,
        "uuid": "test-uuid",
        "report_name": "Test Report",
        "create_time": 1625164800000,
        "updated_time": 1625164800000,
        "user_id": 1,
        "analysis_id": 1,
        "node_id_list": "1,2,3",
        "figure_list": "[]",
        "url" : "fdksdf",
        "status" : "pending"
    }))
    def test_get_report_by_uuid(self, mock_get_report_by_uuid: MagicMock):
        response = self.client.get('/workflow-report/get-info?uuid=test-uuid')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('data', response_data)
        self.assertEqual(response_data['data']['uuid'], "test-uuid")
        self.assertEqual(response_data['data']['name'], "Test Report")

    @patch('service.workflow_report.WorkflowReportService.get_content_by_uuid', return_value="This is a test content.")
    def test_get_report_content(self, mock_get_content_by_uuid: MagicMock):
        response = self.client.get('/workflow-report/get-presigned-url?uuid=test-uuid')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('data', response_data)
        self.assertEqual(response_data['data']['content'], "This is a test content.")

    @patch('service.workflow_report.WorkflowReportService.update_report', return_value=MagicMock(to_dict=lambda: {
        "report_id": 1,
        "uuid": "test-uuid",
        "report_name": "Updated Report",
        "createdTime": 1625164800000,
        "updated_time": 1625164800000,
        "userId": 1,
        "analysis_id": 1,
        "node_id_list": "4,5,6",
        "figure_list": "[1,,]",
        "url": "fdksdf",
        "status": "pending"
    }))
    def test_update_report(self, mock_update_report: MagicMock):
        response = self.client.post('/workflow-report/edit-info', data=json.dumps({
            "uuid": "test-uuid",
            "report_name": "Updated Report",
            "node_ids": "4,5,6",
            "figure_list": "[1,2,3]"
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('data', response_data)
        self.assertEqual(response_data['data']['uuid'], "test-uuid")
        self.assertEqual(response_data['data']['name'], "Updated Report")

    @patch('service.workflow_report.WorkflowReportService.delete_report_by_uuid')
    def test_delete_report(self, mock_delete_report_by_uuid: MagicMock):
        response = self.client.delete('/workflow-report/delete?uuid=test-uuid')
        self.assertEqual(response.status_code, 200)
        mock_delete_report_by_uuid.assert_called_once_with("test-uuid")

    @patch('service.workflow_report.WorkflowReportService.get_all_reports', return_value=[
        MagicMock(to_dict=lambda: {
            "report_id": 1,
            "uuid": "test-uuid",
            "report_name": "Test Report",
            "createdTime": 1625164800000,
            "updated_time": 1625164800000,
            "userId": 1,
            "analysis_id": 1,
            "node_id_list": "1,2,3",
            "figure_list": "[]",
            "url" : "fdksdf",
            "status": "pending"

        }),
        MagicMock(to_dict=lambda: {
            "report_id": 2,
            "uuid": "test-uuid-2",
            "report_name": "Test Report 2",
            "createdTime": 1625164800000,
            "updated_time": 1625164800000,
            "userId": 2,
            "analysis_id": 2,
            "node_id_list": "4,5,6",
            "figure_list": "[4,4,6]",
            "url" : "fdksdf",
            "status": "pending"
        })
    ])
    def test_get_all_reports(self, mock_get_all_reports: MagicMock):
        response = self.client.get('/workflow-report/list')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('data', response_data)
        self.assertEqual(len(response_data['data']), 2)
        self.assertEqual(response_data['data'][0]['uuid'], "test-uuid")
        self.assertEqual(response_data['data'][1]['uuid'], "test-uuid-2")

if __name__ == '__main__':
    unittest.main()
