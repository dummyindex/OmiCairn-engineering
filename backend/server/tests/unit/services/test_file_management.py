"""
Unit tests for FileManagementService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from io import BytesIO

from service.file_management import FileManagementService


@pytest.mark.unit
@pytest.mark.service
class TestFileManagementService:
    """Test FileManagementService business logic"""

    @pytest.fixture
    def service(self):
        with patch('service.file_management.PorterFactory.create_porter'):
            return FileManagementService()

    @pytest.fixture
    def mock_porter(self, service):
        """Mock porter object"""
        service.porter = MagicMock()
        return service.porter

    def test_list_files(self, service, mock_porter):
        """Test listing files"""
        # Arrange
        mock_porter.set_operation_target.return_value = None
        mock_porter.list_files.return_value = [
            'v3-chat-workspace/123/file1.txt',
            'v3-chat-workspace/123/file2.csv'
        ]
        mock_porter.get_file_info.side_effect = [
            {'Size': 1024, 'LastModified': datetime(2024, 1, 1, 12, 0, 0)},
            {'Size': 2048, 'LastModified': datetime(2024, 1, 2, 12, 0, 0)}
        ]

        # Act
        result = service.list_files('123', 'v3-chat-workspace/123')

        # Assert
        assert len(result) == 2
        assert result[0]['name'] == 'file1.txt'
        assert result[1]['name'] == 'file2.csv'
        mock_porter.list_files.assert_called_once()

    def test_list_files_error(self, service, mock_porter):
        """Test listing files - failure"""
        # Arrange
        mock_porter.list_files.side_effect = Exception("S3 error")

        # Act & Assert
        with pytest.raises(Exception, match="S3 error"):
            service.list_files('123', 'v3-chat-workspace/123')

    def test_delete_file_by_id(self, service, mock_porter):
        """Test deleting a file"""
        # Arrange
        mock_porter.set_operation_target.return_value = None
        mock_porter.remove_file.return_value = None

        # Act
        result = service.delete_file_by_id('v3-chat-workspace/123/file.txt')

        # Assert
        assert result is True
        mock_porter.set_operation_target.assert_called_once_with('v3-chat-workspace/123/file.txt')
        mock_porter.remove_file.assert_called_once()

    def test_delete_file_error(self, service, mock_porter):
        """Test deleting a file - failure"""
        # Arrange
        mock_porter.remove_file.side_effect = Exception("Delete failed")

        # Act & Assert
        with pytest.raises(Exception, match="Delete failed"):
            service.delete_file_by_id('file.txt')

    def test_upload_file(self, service, mock_porter):
        """Test uploading a file"""
        # Arrange
        file_stream = BytesIO(b"test content")
        mock_porter.set_operation_target.return_value = None
        mock_porter.save_file_stream.return_value = None
        mock_porter.get_file_info.return_value = {
            'Size': 1024,
            'LastModified': datetime(2024, 1, 1, 12, 0, 0)
        }

        # Act
        result = service.upload_file('123', file_stream, 'test.txt')

        # Assert
        assert result is not None
        assert result['name'] == 'test.txt'
        assert result['id'] == 'v3-chat-workspace/123/test.txt'
        mock_porter.save_file_stream.assert_called_once()

    def test_format_file_size_bytes(self, service):
        """Test file size formatting - bytes"""
        result = service._format_file_size(512)
        assert result == "512 Bytes"

    def test_format_file_size_kb(self, service):
        """Test file size formatting - KB"""
        result = service._format_file_size(2048)
        assert result == "2.00 KB"

    def test_format_file_size_mb(self, service):
        """Test file size formatting - MB"""
        result = service._format_file_size(1048576)
        assert result == "1.00 MB"

    def test_format_file_size_gb(self, service):
        """Test file size formatting - GB"""
        result = service._format_file_size(1073741824)
        assert result == "1.00 GB"


# Singleton tests
def test_file_management_service_creation():
    """Test that FileManagementService can be instantiated"""
    with patch('service.file_management.PorterFactory.create_porter'):
        service = FileManagementService()
        assert service is not None
        assert isinstance(service, FileManagementService)
