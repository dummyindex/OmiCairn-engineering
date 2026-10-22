"""
Unit tests for Analysis Controller
"""
import pytest
from unittest.mock import Mock, patch
import json


@pytest.mark.unit
@pytest.mark.controller
class TestAnalysisController:
    """Test Analysis Controller API endpoints"""

    @patch('controller.analysis.analysis_service')
    def test_get_public_analysis_info(self, mock_analysis_service, client):
        """Test getting public analysis info"""
        # Arrange
        mock_info = {
            'id': 1,
            'name': 'Public Analysis',
            'description': 'Test analysis'
        }
        mock_analysis_service.get_info.return_value = mock_info

        # Act
        response = client.get('/api/analysis/public/info?analysis_id=1')

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['name'] == 'Public Analysis'
        mock_analysis_service.get_info.assert_called_once_with('1')

    @patch('controller.analysis.AuthorityGuardianFactory.get_authority_guardian')
    @patch('controller.analysis.analysis_service')
    def test_get_analysis_info_authenticated(self, mock_analysis_service,
                                            mock_guardian_factory, client):
        """Test getting analysis info - authenticated"""
        # Arrange
        mock_guardian = Mock()
        mock_guardian_factory.return_value = mock_guardian

        mock_info = {
            'id': 1,
            'name': 'My Analysis',
            'description': 'Test analysis'
        }
        mock_analysis_service.get_info.return_value = mock_info

        # Act
        response = client.get('/api/analysis/info?analysis_id=1')

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['name'] == 'My Analysis'

    @patch('controller.analysis.analysis_service')
    def test_get_public_analysis_list(self, mock_analysis_service, client):
        """Test getting the public analysis list"""
        # Arrange
        mock_list = [
            {'id': 1, 'name': 'Analysis 1'},
            {'id': 2, 'name': 'Analysis 2'}
        ]
        mock_analysis_service.get_info_list.return_value = mock_list

        # Act
        response = client.get('/api/analysis/public/list')

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 2

    @patch('controller.analysis.AuthorityGuardianFactory.get_authority_guardian')
    @patch('controller.analysis.analysis_service')
    def test_get_user_analysis_list(self, mock_analysis_service,
                                    mock_guardian_factory, client):
        """Test getting the user's analysis list"""
        # Arrange
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 1
        mock_guardian_factory.return_value = mock_guardian

        mock_list = [
            {'id': 1, 'name': 'My Analysis 1'},
            {'id': 2, 'name': 'My Analysis 2'}
        ]
        mock_analysis_service.get_info_list.return_value = mock_list

        # Act
        response = client.get('/api/analysis/list')

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 2
        mock_analysis_service.get_info_list.assert_called_once_with(1, add_latest_visit_time=True)

    @patch('controller.analysis.AuthorityGuardianFactory.get_authority_guardian')
    @patch('controller.analysis.analysis_service')
    def test_create_analysis_success(self, mock_analysis_service,
                                     mock_guardian_factory, client):
        """Test creating an analysis - success"""
        # Arrange
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 1
        mock_guardian_factory.return_value = mock_guardian

        mock_analysis_service.get_info_list.return_value = []  # No existing analyses

        mock_result = {'id': 1, 'name': 'New Analysis'}
        mock_analysis_service.create.return_value = mock_result

        # Act
        response = client.post('/api/analysis/create', data={
            'name': 'New Analysis',
            'description': 'Test description'
        })

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['name'] == 'New Analysis'
        mock_analysis_service.create.assert_called_once()


    @patch('controller.analysis.AuthorityGuardianFactory.get_authority_guardian')
    @patch('controller.analysis.analysis_service')
    def test_validate_analysis_password(self, mock_analysis_service,
                                       mock_guardian_factory, client):
        """Test verifying the analysis password"""
        # Arrange
        mock_guardian = Mock()
        mock_guardian.check_authority.return_value = True
        mock_guardian_factory.return_value = mock_guardian

        mock_analysis_service.validate_password.return_value = True

        # Act
        response = client.get('/api/analysis/validate?analysis_id=1&password=test123')

        # Assert
        assert response.status_code == 200
        mock_guardian.check_authority.assert_called_once_with('1')
        mock_analysis_service.validate_password.assert_called_once_with('1', 'test123')
