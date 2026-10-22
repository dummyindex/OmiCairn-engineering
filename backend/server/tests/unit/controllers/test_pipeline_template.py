"""
Unit tests for PipelineTemplate Controller
"""
import pytest
from unittest.mock import Mock, patch
import json

from controller.pipeline_template import (
    PipelineTemplateCreateAPI,
    PipelineTemplateListGetAPI,
    PipelineTemplateGroupNameListGetAPI
)


@pytest.mark.unit
@pytest.mark.controller
class TestPipelineTemplateController:
    """Test PipelineTemplate Controller API endpoints"""

    @patch('controller.pipeline_template.AuthorityGuardianFactory.get_authority_guardian')
    @patch('controller.pipeline_template.pt_service')
    def test_create_template_success(self, mock_pt_service, mock_guardian_factory, client):
        """Test creating a pipeline template - success"""
        # Arrange
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 1
        mock_guardian.check_authority.return_value = True
        mock_guardian_factory.return_value = mock_guardian

        mock_template = Mock()
        mock_template.id = 1
        mock_template.name = "Test Template"
        mock_pt_service.create.return_value = mock_template

        # Act
        response = client.post('/api/pipeline_template/create',
            data=json.dumps({
                'name': 'Test Template',
                'node_id_list': [1, 2, 3],
                'edge_id_list': [1, 2],
                'group_name': 'Test Group',
                'description': 'Test description'
            }),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        mock_pt_service.create.assert_called_once()

    @patch('controller.pipeline_template.AuthorityGuardianFactory.get_authority_guardian')
    @patch('controller.pipeline_template.pt_service')
    def test_create_template_missing_params(self, mock_pt_service, mock_guardian_factory, client):
        """Test creating a pipeline template - missing parameters"""
        # Arrange
        mock_guardian = Mock()
        mock_guardian_factory.return_value = mock_guardian

        # Act
        response = client.post('/api/pipeline_template/create',
            data=json.dumps({
                'name': 'Test Template'
                # Missing required fields
            }),
            content_type='application/json'
        )

        # Assert
        # Should fail validation
        mock_pt_service.create.assert_not_called()

    @patch('controller.pipeline_template.AuthorityGuardianFactory.get_authority_guardian')
    @patch('controller.pipeline_template.pt_service')
    def test_get_template_list(self, mock_pt_service, mock_guardian_factory, client):
        """Test getting the template list"""
        # Arrange
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 1
        mock_guardian_factory.return_value = mock_guardian

        mock_templates = [
            Mock(id=1, name="Template 1"),
            Mock(id=2, name="Template 2")
        ]
        mock_pt_service.get_list_by_owner_id_and_group_name.return_value = mock_templates

        # Act
        response = client.get('/api/pipeline_template/list?group_name=Test+Group')

        # Assert
        assert response.status_code == 200
        mock_pt_service.get_list_by_owner_id_and_group_name.assert_called_once_with(1, 'Test Group')

    @patch('controller.pipeline_template.AuthorityGuardianFactory.get_authority_guardian')
    @patch('controller.pipeline_template.pt_service')
    def test_get_group_name_list(self, mock_pt_service, mock_guardian_factory, client):
        """Test getting the group name list"""
        # Arrange
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 1
        mock_guardian_factory.return_value = mock_guardian

        mock_groups = ['Group 1', 'Group 2', 'Group 3']
        mock_pt_service.get_group_name_list_by_user_id.return_value = mock_groups

        # Act
        response = client.get('/api/pipeline_template/group_names')

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 3
        mock_pt_service.get_group_name_list_by_user_id.assert_called_once_with(1)

    @patch('controller.pipeline_template.AuthorityGuardianFactory.get_authority_guardian')
    @patch('controller.pipeline_template.pt_service')
    def test_get_function_blocks_by_template(self, mock_pt_service, mock_guardian_factory, client):
        """Test getting the template's function block list"""
        # Arrange
        mock_guardian = Mock()
        mock_guardian.check_authority.return_value = True
        mock_guardian_factory.return_value = mock_guardian

        mock_blocks = [
            Mock(id=1, name="Block 1"),
            Mock(id=2, name="Block 2")
        ]
        mock_pt_service.get_function_block_list_by_pipeline_template_id.return_value = mock_blocks

        # Act
        response = client.get('/api/pipeline_template/function_blocks?pipeline_template_id=1')

        # Assert
        assert response.status_code == 200
        mock_guardian.check_authority.assert_called_once_with('1')
        mock_pt_service.get_function_block_list_by_pipeline_template_id.assert_called_once()
