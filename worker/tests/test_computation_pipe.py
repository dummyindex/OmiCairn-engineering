"""
Unit tests for computation pipeline functionality.
Tests the get_computation_pipe method that retrieves upstream node information.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from server.service.computation import computation_service
from server.model.node import Node
from server.model.edge import Edge


class TestComputationPipe:
    """Test computation pipeline retrieval."""
    
    @pytest.fixture
    def mock_node_dao(self):
        """Mock node DAO for testing."""
        with patch('server.service.computation.node_dao') as mock:
            yield mock
    
    @pytest.fixture
    def mock_edge_dao(self):
        """Mock edge DAO for testing."""
        with patch('server.service.computation.edge_dao') as mock:
            yield mock
    
    @pytest.fixture
    def mock_porter_factory(self):
        """Mock Porter factory for S3 operations."""
        with patch('server.service.computation.PorterFactory') as mock:
            yield mock
    
    def test_get_computation_pipe_with_single_previous_node(self, mock_node_dao, mock_edge_dao, mock_porter_factory):
        """Test getting computation pipe with one previous node."""
        # Setup mock data
        target_node_id = 456
        previous_node_id = 123
        
        # Mock edge (connection between nodes)
        mock_edge = Mock(spec=Edge)
        mock_edge.source_node_id = previous_node_id
        mock_edge_dao.find_all_front_edges.return_value = [mock_edge]
        
        # Mock previous node
        mock_node = Mock(spec=Node)
        mock_node.id = previous_node_id
        mock_node.type = "Python Analysis v2"
        mock_node.function_block_version_id = 789
        mock_node_dao.find_by_id.return_value = mock_node
        
        # Mock porter (S3 file access)
        mock_porter = MagicMock()
        mock_porter.list_files.return_value = [
            "function-block-version/789/run.sh",
            "function-block-version/789/static-config.json",
            "function-block-version/789/main.py"
        ]
        
        # Mock file contents
        def mock_fetch_file_text():
            file_contents = {
                "function-block-version/789/run.sh": "#!/bin/bash\npython main.py\nexit 0",
                "function-block-version/789/static-config.json": '{"name": "Test FB", "version": "1.0.0"}',
                "function-block-version/789/main.py": "import scanpy as sc\nprint('Hello')"
            }
            target = mock_porter.set_operation_target.call_args[0][0]
            return file_contents.get(target, "")
        
        mock_porter.fetch_file_text.side_effect = mock_fetch_file_text
        mock_porter_factory.create_porter.return_value = mock_porter
        
        # Execute
        result = computation_service.get_computation_pipe(target_node_id)
        
        # Verify
        assert len(result) == 1
        assert f"Node ID: {previous_node_id}" in result[0]
        assert "Type: Python Analysis v2" in result[0]
        assert "run.sh" in result[0]
        assert "static-config.json" in result[0]
        assert "main.py" in result[0]
        assert "#!/bin/bash" in result[0]
        assert "import scanpy as sc" in result[0]
        
        # Verify DAOs were called correctly
        mock_edge_dao.find_all_front_edges.assert_called_once_with(target_node_id)
        mock_node_dao.find_by_id.assert_called_once_with(previous_node_id)
    
    def test_get_computation_pipe_with_multiple_nodes(self, mock_node_dao, mock_edge_dao, mock_porter_factory):
        """Test getting computation pipe with multiple previous nodes."""
        target_node_id = 789
        
        # Mock edges (2 previous nodes)
        edge1 = Mock(spec=Edge)
        edge1.source_node_id = 123
        edge2 = Mock(spec=Edge)
        edge2.source_node_id = 456
        mock_edge_dao.find_all_front_edges.return_value = [edge1, edge2]
        
        # Mock nodes
        node1 = Mock(spec=Node)
        node1.id = 123
        node1.type = "Python Analysis v2"
        node1.function_block_version_id = 111
        
        node2 = Mock(spec=Node)
        node2.id = 456
        node2.type = "R Analysis v2"
        node2.function_block_version_id = 222
        
        def mock_find_by_id(node_id):
            return node1 if node_id == 123 else node2
        
        mock_node_dao.find_by_id.side_effect = mock_find_by_id
        
        # Mock porter
        mock_porter = MagicMock()
        mock_porter.list_files.return_value = [
            "function-block-version/111/run.sh"
        ]
        mock_porter.fetch_file_text.return_value = "#!/bin/bash\necho 'test'"
        mock_porter_factory.create_porter.return_value = mock_porter
        
        # Execute
        result = computation_service.get_computation_pipe(target_node_id)
        
        # Verify
        assert len(result) == 2
        assert "Node ID: 456" in result[0]  # Edges are reversed
        assert "Node ID: 123" in result[1]
        
    def test_get_computation_pipe_with_data_node(self, mock_node_dao, mock_edge_dao, mock_porter_factory):
        """Test handling of data nodes (no files to display)."""
        target_node_id = 456
        
        # Mock edge
        mock_edge = Mock(spec=Edge)
        mock_edge.source_node_id = 123
        mock_edge_dao.find_all_front_edges.return_value = [mock_edge]
        
        # Mock data node
        mock_node = Mock(spec=Node)
        mock_node.id = 123
        mock_node.type = "data node: user upload"
        mock_node_dao.find_by_id.return_value = mock_node
        
        # Execute
        result = computation_service.get_computation_pipe(target_node_id)
        
        # Verify
        assert len(result) == 1
        assert "Node ID: 123" in result[0]
        assert "Type: Data Node" in result[0]
        assert "Files:" not in result[0]  # Data nodes don't show files
        
        # Porter should not be called for data nodes
        mock_porter_factory.create_porter.assert_not_called()
    
    def test_get_computation_pipe_with_binary_files(self, mock_node_dao, mock_edge_dao, mock_porter_factory):
        """Test handling of binary files (should not fetch content)."""
        target_node_id = 456
        
        # Mock edge and node
        mock_edge = Mock(spec=Edge)
        mock_edge.source_node_id = 123
        mock_edge_dao.find_all_front_edges.return_value = [mock_edge]
        
        mock_node = Mock(spec=Node)
        mock_node.id = 123
        mock_node.type = "Python Analysis v2"
        mock_node.function_block_version_id = 789
        mock_node_dao.find_by_id.return_value = mock_node
        
        # Mock porter with binary files
        mock_porter = MagicMock()
        mock_porter.list_files.return_value = [
            "function-block-version/789/run.sh",
            "function-block-version/789/data.h5ad",
            "function-block-version/789/model.pkl"
        ]
        
        def mock_fetch_file_text():
            target = mock_porter.set_operation_target.call_args[0][0]
            if target.endswith("run.sh"):
                return "#!/bin/bash\npython main.py"
            return ""
        
        mock_porter.fetch_file_text.side_effect = mock_fetch_file_text
        mock_porter_factory.create_porter.return_value = mock_porter
        
        # Execute
        result = computation_service.get_computation_pipe(target_node_id)
        
        # Verify
        assert len(result) == 1
        assert "run.sh" in result[0]
        assert "#!/bin/bash" in result[0]
        assert "[Binary file, h5ad]" in result[0]
        assert "[Binary file, pkl]" in result[0]
        
        # fetch_file_text should only be called for run.sh (text file)
        # Binary files should not have their content fetched
        assert mock_porter.fetch_file_text.call_count == 1
    
    def test_get_computation_pipe_with_no_previous_nodes(self, mock_node_dao, mock_edge_dao, mock_porter_factory):
        """Test when node has no previous nodes (e.g., first node in pipeline)."""
        target_node_id = 123
        
        # No previous edges
        mock_edge_dao.find_all_front_edges.return_value = []
        
        # Execute
        result = computation_service.get_computation_pipe(target_node_id)
        
        # Verify
        assert len(result) == 0
        assert result == []
        
        # Node DAO should not be called
        mock_node_dao.find_by_id.assert_not_called()
    
    def test_get_computation_pipe_with_null_node_type(self, mock_node_dao, mock_edge_dao, mock_porter_factory):
        """Test handling of nodes with null type (should be skipped)."""
        target_node_id = 456
        
        # Mock edge
        mock_edge = Mock(spec=Edge)
        mock_edge.source_node_id = 123
        mock_edge_dao.find_all_front_edges.return_value = [mock_edge]
        
        # Mock node with None type
        mock_node = Mock(spec=Node)
        mock_node.id = 123
        mock_node.type = None
        mock_node_dao.find_by_id.return_value = mock_node
        
        # Execute
        result = computation_service.get_computation_pipe(target_node_id)
        
        # Verify
        assert len(result) == 0
        assert result == []
    
    def test_get_computation_pipe_with_mixed_file_types(self, mock_node_dao, mock_edge_dao, mock_porter_factory):
        """Test with various file types (json, py, r, sh, txt, and others)."""
        target_node_id = 456
        
        # Setup
        mock_edge = Mock(spec=Edge)
        mock_edge.source_node_id = 123
        mock_edge_dao.find_all_front_edges.return_value = [mock_edge]
        
        mock_node = Mock(spec=Node)
        mock_node.id = 123
        mock_node.type = "Mixed Analysis v2"
        mock_node.function_block_version_id = 789
        mock_node_dao.find_by_id.return_value = mock_node
        
        # Mock porter with various file types
        mock_porter = MagicMock()
        mock_porter.list_files.return_value = [
            "function-block-version/789/run.sh",        # sh - should be read
            "function-block-version/789/config.json",   # json - should be read
            "function-block-version/789/script.py",     # py - should be read
            "function-block-version/789/analysis.R",    # r - should be read
            "function-block-version/789/README.txt",    # txt - should be read
            "function-block-version/789/data.h5ad",     # h5ad - binary, not read
            "function-block-version/789/image.PNG"      # PNG - binary, not read (uppercase extension)
        ]
        
        file_contents = {
            "function-block-version/789/run.sh": "#!/bin/bash",
            "function-block-version/789/config.json": '{"key": "value"}',
            "function-block-version/789/script.py": "import sys",
            "function-block-version/789/analysis.R": "library(dplyr)",
            "function-block-version/789/README.txt": "Documentation"
        }
        
        def mock_fetch_file_text():
            target = mock_porter.set_operation_target.call_args[0][0]
            return file_contents.get(target, "")
        
        mock_porter.fetch_file_text.side_effect = mock_fetch_file_text
        mock_porter_factory.create_porter.return_value = mock_porter
        
        # Execute
        result = computation_service.get_computation_pipe(target_node_id)
        
        # Verify
        assert len(result) == 1
        
        # Text files should have content
        assert "#!/bin/bash" in result[0]
        assert '{"key": "value"}' in result[0]
        assert "import sys" in result[0]
        assert "library(dplyr)" in result[0]
        assert "Documentation" in result[0]
        
        # Binary files should be marked
        assert "[Binary file, h5ad]" in result[0]
        assert "[Binary file, PNG]" in result[0] or "[Binary file, png]" in result[0]
        
        # Verify fetch_file_text was called correct number of times (5 text files)
        assert mock_porter.fetch_file_text.call_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
