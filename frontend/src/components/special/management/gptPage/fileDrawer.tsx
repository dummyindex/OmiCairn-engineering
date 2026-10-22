import { requestDeleteFile, requestGetFileList } from '@/request/fileManagement';
import {
  DeleteOutlined,
  FileOutlined,
  FolderOpenOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { Button, Drawer, message, Popconfirm, Tree } from 'antd';
import React, { useEffect, useState } from 'react';

interface FileItem {
  id: string;
  name: string;
  size?: string;
  lastModified?: string;
}

interface TreeNode {
  title: React.ReactNode;
  key: string;
  children?: TreeNode[];
  isLeaf?: boolean;
  fileData?: FileItem;
  _childrenMap?: { [key: string]: TreeNode };
}

interface FileDrawerProps {
  visible: boolean;
  onClose: () => void;
  selectedFiles: string[];
  onSelectFiles: (fileIds: string[]) => void;
  analysisId?: string | number;
  attachedFolder?: any;
  isEditable?: boolean;
}

const buildFileTree = (
  files: FileItem[],
  selectedFiles: string[],
  onFileSelect: (fileId: string) => void,
  onDeleteFile: (fileId: string) => void,
  disabled: boolean = false,
): TreeNode[] => {
  const tree: { [key: string]: TreeNode } = {};

  files.forEach((file) => {
    const idParts = file.id.split('/');
    if (idParts.length < 3) return;

    const pathParts = idParts.slice(2);
    let currentLevel = tree;

    for (let i = 0; i < pathParts.length - 1; i++) {
      const folderName = pathParts[i];
      if (!currentLevel[folderName]) {
        currentLevel[folderName] = {
          title: (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <FolderOpenOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              <span>{folderName}</span>
            </div>
          ),
          key: pathParts.slice(0, i + 1).join('/'),
          children: [],
        };
      }

      if (!currentLevel[folderName]._childrenMap) {
        currentLevel[folderName]._childrenMap = {};
      }
      currentLevel = currentLevel[folderName]._childrenMap;
    }

    const fileName = pathParts[pathParts.length - 1];
    const displayName = file.name || fileName;
    const isSelected = selectedFiles.includes(file.id);

    currentLevel[fileName] = {
      title: (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            width: '100%',
            padding: '4px 8px',
            background: isSelected ? '#e6f7ff' : 'transparent',
            borderRadius: '4px',
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.5 : 1,
          }}
          onClick={(e) => {
            e.stopPropagation();
            if (!disabled) {
              onFileSelect(file.id);
            }
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
            <FileOutlined style={{ marginRight: 8, color: '#666' }} />
            <div>
              <div
                style={{
                  fontSize: '13px',
                  fontWeight: isSelected ? 'bold' : 'normal',
                }}
              >
                {displayName}
              </div>
              <div style={{ fontSize: '11px', color: '#666' }}>
                {file.size && `${file.size} • `}
                {file.lastModified}
              </div>
            </div>
          </div>
          <Popconfirm
            title="Delete file"
            description="Are you sure you want to delete this file?"
            onConfirm={(e) => {
              e?.stopPropagation();
              onDeleteFile(file.id);
            }}
            onCancel={(e) => e?.stopPropagation()}
            okText="Yes"
            cancelText="No"
          >
            <Button
              size="small"
              type="text"
              icon={<DeleteOutlined />}
              style={{ color: '#ff4d4f' }}
              onClick={(e) => e.stopPropagation()}
              disabled={disabled}
            />
          </Popconfirm>
        </div>
      ),
      key: file.id,
      isLeaf: true,
      fileData: file,
    };
  });

  const convertToArray = (obj: { [key: string]: TreeNode }): TreeNode[] => {
    return Object.values(obj)
      .sort((a, b) => {
        if (!a.isLeaf && b.isLeaf) return -1;
        if (a.isLeaf && !b.isLeaf) return 1;
        return (a.key || '').localeCompare(b.key || '');
      })
      .map((node) => {
        const result = { ...node };
        if (node._childrenMap && Object.keys(node._childrenMap).length > 0) {
          result.children = convertToArray(node._childrenMap);
        }
        delete result._childrenMap;
        return result;
      });
  };

  return convertToArray(tree);
};

const FileDrawer: React.FC<FileDrawerProps> = ({
  visible,
  onClose,
  selectedFiles,
  onSelectFiles,
  analysisId,
  attachedFolder,
  isEditable,
}) => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(false);

  const handleFileSelect = (fileId: string) => {
    if (attachedFolder) {
      message.warning(
        'Cannot select workspace files when a folder is attached. Please remove the folder first.',
      );
      return;
    }

    const isSelected = selectedFiles.includes(fileId);
    if (isSelected) {
      onSelectFiles(selectedFiles.filter((id) => id !== fileId));
    } else {
      onSelectFiles([...selectedFiles, fileId]);
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      const response = await requestDeleteFile(fileId);
      if (response?.code === 200) {
        const updatedFiles = files.filter((file) => file.id !== fileId);
        setFiles(updatedFiles);
        onSelectFiles(selectedFiles.filter((id) => id !== fileId));

        const tree = buildFileTree(
          updatedFiles,
          selectedFiles.filter((id) => id !== fileId),
          handleFileSelect,
          handleDeleteFile,
          !isEditable,
        );
        setTreeData(tree);
        message.success('File deleted successfully');
      } else {
        message.error(response?.message || 'Failed to delete file');
      }
    } catch (error) {
      console.error('Error deleting file:', error);
      message.error('Failed to delete file');
    }
  };

  const loadFiles = async () => {
    if (analysisId == null) {
      setFiles([]);
      setTreeData([]);
      return;
    }
    setLoading(true);
    try {
      const response = await requestGetFileList(analysisId);
      if (response?.code === 200) {
        const fileData = response.data || [];
        setFiles(fileData);

        const isDisabled = attachedFolder != null || !isEditable;
        const tree = buildFileTree(
          fileData,
          selectedFiles,
          handleFileSelect,
          handleDeleteFile,
          isDisabled,
        );
        setTreeData(tree);
      } else {
        message.error(response?.message || 'Failed to load files');
      }
    } catch (error) {
      console.error('Error loading files:', error);
      message.error('Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible) {
      loadFiles();
    }
  }, [visible]);

  useEffect(() => {
    if (files.length > 0) {
      const isDisabled = attachedFolder != null || !isEditable;
      const tree = buildFileTree(
        files,
        selectedFiles,
        handleFileSelect,
        handleDeleteFile,
        isDisabled,
      );
      setTreeData(tree);
    }
  }, [selectedFiles, attachedFolder]);

  const clearAllSelections = () => {
    if (attachedFolder) {
      message.warning('Cannot modify workspace selections when a folder is attached.');
      return;
    }
    onSelectFiles([]);
  };

  return (
    <Drawer
      title="File Manager"
      placement="right"
      onClose={onClose}
      open={visible}
      width={600}
      mask={false}
    >
      <div style={{ height: '95vh' }}>
        <div
          style={{
            padding: '12px',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <span>File Manager</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              size="small"
              onClick={clearAllSelections}
              style={{ fontSize: '12px' }}
              disabled={!isEditable}
            >
              Clear All
            </Button>
          </div>
        </div>

        <div style={{ padding: '12px', height: 'calc(100% - 120px)', overflow: 'auto' }}>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: '12px' }}>
            Selected {selectedFiles.length} files
          </div>

          {attachedFolder && (
            <div
              style={{
                padding: '8px 12px',
                background: '#fff2e8',
                border: '1px solid #ffcc99',
                borderRadius: '6px',
                marginBottom: '12px',
                fontSize: '12px',
                color: '#d46b08',
              }}
            >
              You already attached a folder. Workspace file selection is disabled.
            </div>
          )}

          {loading ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <LoadingOutlined /> Loading files...{' '}
            </div>
          ) : (
            <div style={{ overflow: 'auto', maxHeight: '600px' }}>
              {treeData.length > 0 ? (
                <Tree
                  showLine
                  defaultExpandAll
                  treeData={treeData}
                  selectable={false}
                  style={{ fontSize: '13px' }}
                />
              ) : (
                <div style={{ textAlign: 'center', color: '#999', padding: '40px 20px' }}>
                  <FileOutlined style={{ fontSize: '32px', marginBottom: '16px' }} />
                  <div>No files found</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </Drawer>
  );
};

export default FileDrawer;
