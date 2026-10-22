"""
Unit tests for PipelineTemplateService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from service.pipeline_template import PipelineTemplateService
from model.pipeline_template import PipelineTemplate
from model.node import Node
from model.edge import Edge


@pytest.mark.unit
@pytest.mark.service
class TestPipelineTemplateService:
    """Test PipelineTemplateService business logic"""

    @pytest.fixture
    def service(self):
        return PipelineTemplateService()

    @pytest.fixture
    def sample_nodes(self):
        return [
            Node(id=1, name="Node1", x=100, y=100),
            Node(id=2, name="Node2", x=200, y=200)
        ]

    @pytest.fixture
    def sample_edges(self):
        return [
            Edge(id=1, source_node_id=1, target_node_id=2)
        ]

    # ===== Create Tests =====

    @patch('service.pipeline_template.pt_dao')
    @patch('service.pipeline_template.node_dao')
    @patch('service.pipeline_template.edge_dao')
    def test_create_template(self, mock_edge_dao, mock_node_dao, mock_pt_dao,
                            service, sample_nodes, sample_edges):
        """Test creating a pipeline template"""
        # Arrange
        mock_node_dao.find_by_id_list.return_value = sample_nodes
        mock_edge_dao.find_by_id_list.return_value = sample_edges

        mock_template = Mock(spec=PipelineTemplate)
        mock_template.id = 1
        mock_pt_dao.insert.return_value = mock_template
        mock_pt_dao.insert_user_relation.return_value = None

        # Act
        result = service.create(
            name="Test Template",
            node_id_list=[1, 2],
            edge_id_list=[1],
            owner_id=1,
            group_name="Test Group",
            description="Test description"
        )

        # Assert
        mock_node_dao.find_by_id_list.assert_called_once_with([1, 2])
        mock_edge_dao.find_by_id_list.assert_called_once_with([1])
        mock_pt_dao.insert.assert_called()

    # ===== Query Tests =====

    @patch('service.pipeline_template.pt_dao')
    def test_find_by_id(self, mock_pt_dao, service):
        """Test finding a template by ID"""
        # Arrange
        mock_template = Mock(spec=PipelineTemplate)
        mock_template.id = 1
        mock_template.name = "Test Template"
        mock_pt_dao.find_by_id.return_value = mock_template

        # Act
        result = service.find_by_id(1)

        # Assert
        assert result is not None
        mock_pt_dao.find_by_id.assert_called_once_with(1)

    # ===== Update Tests =====

    @patch('service.pipeline_template.pt_dao')
    def test_update_template(self, mock_pt_dao, service):
        """Test updating a template"""
        # Arrange
        mock_pt_dao.update.return_value = None

        # Act
        service.update(1, {'name': 'Updated Template'})

        # Assert
        mock_pt_dao.update.assert_called_once_with(1, {'name': 'Updated Template'})

    # ===== Delete Tests =====

    @patch('service.pipeline_template.pt_dao')
    def test_delete_template(self, mock_pt_dao, service):
        """Test deleting a template"""
        # Arrange
        mock_pt_dao.delete.return_value = None

        # Act
        service.delete(1)

        # Assert
        mock_pt_dao.delete.assert_called_once_with(1)


# Singleton tests
pipeline_template_service = PipelineTemplateService()

def test_pipeline_template_service_singleton():
    """Test that PipelineTemplateService can be instantiated"""
    assert pipeline_template_service is not None
    assert isinstance(pipeline_template_service, PipelineTemplateService)
