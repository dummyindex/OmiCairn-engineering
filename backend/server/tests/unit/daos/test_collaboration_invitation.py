"""
Unit tests for CollaborationInvitationDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.collaboration_invitation import CollaborationInvitationDao, collaboration_invitation_dao
from model.collaboration_invitation import CollaborationInvitation


@pytest.mark.unit
@pytest.mark.dao
class TestCollaborationInvitationDao:
    """Test CollaborationInvitationDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return CollaborationInvitationDao()

    @pytest.fixture
    def sample_invitation(self):
        return CollaborationInvitation(
            id=1,
            analysis_id=1,
            inviter_id=1,
            invitee_id=2,
            status="pending",
            created_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_invitation):
        """Test inserting an invitation"""
        # Arrange
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        # Act
        result = dao.insert(sample_invitation)

        # Assert
        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @patch('model.collaboration_invitation.CollaborationInvitation.query')
    def test_find_by_id(self, mock_query, dao, sample_invitation):
        """Test finding an invitation by ID"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_invitation

        # Act
        result = dao.find_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1

    @patch('model.collaboration_invitation.CollaborationInvitation.query')
    def test_find_by_invitee_id(self, mock_query, dao, sample_invitation):
        """Test finding by invitee ID"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [sample_invitation]

        # Act
        result = dao.find_by_invitee_id(2)

        # Assert
        assert len(result) == 1

    @patch('model.collaboration_invitation.CollaborationInvitation.query')
    def test_update(self, mock_query, dao):
        """Test updating an invitation"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = 1

        # Act
        dao.update(1, {'status': 'accepted'})

        # Assert
        mock_filter.update.assert_called_once()

    @patch('model.collaboration_invitation.CollaborationInvitation.query')
    def test_delete(self, mock_query, dao):
        """Test deleting an invitation"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = 1

        # Act
        dao.delete(1)

        # Assert
        mock_filter.delete.assert_called_once()

    def test_singleton_instance(self):
        """Test singleton pattern"""
        assert collaboration_invitation_dao is not None
        assert isinstance(collaboration_invitation_dao, CollaborationInvitationDao)
