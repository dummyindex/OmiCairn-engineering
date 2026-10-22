import React, { useState, useEffect } from 'react';
import { Modal, Tree, Spin, message, Empty, Button, Space, Tooltip } from 'antd';
import { FolderOutlined, FileOutlined, LoadingOutlined, DownloadOutlined } from '@ant-design/icons';
import Editor from '@monaco-editor/react';
import { requestFBVersionStructure, requestFBVersionContent } from '@/request/functionBlock';
import { requestPreviousNodeList } from '@/request/node';
import type { DataNode } from 'antd/es/tree';
import './FBStructureDialog.less';

interface FBStructureDialogProps {
  visible: boolean;
  functionBlockVersionId: string | null;
  nodeId?: string;
  nodeName?: string;
  onClose: () => void;
}

// eslint-disable-next-line @typescript-eslint/consistent-indexed-object-style
interface StructureData {
  [key: string]: 'file' | StructureData;
}

const FBStructureDialog: React.FC<FBStructureDialogProps> = ({
  visible,
  functionBlockVersionId,
  nodeId,
  nodeName,
  onClose,
}) => {
  const [treeData, setTreeData] = useState<DataNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [loadingStructure, setLoadingStructure] = useState(false);
  const [loadingContent, setLoadingContent] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [downloadingCurrent, setDownloadingCurrent] = useState(false);
  const [downloadingAll, setDownloadingAll] = useState(false);

  // Convert file structure to Ant Design Tree format
  const convertToTreeData = (structure: StructureData, parentPath = ''): DataNode[] => {
    const treeNodes: DataNode[] = [];

    for (const [name, value] of Object.entries(structure)) {
      const fullPath = parentPath ? `${parentPath}/${name}` : name;
      const isFile = value === 'file';

      const treeNode: DataNode = {
        title: name,
        key: fullPath,
        icon: isFile ? <FileOutlined /> : <FolderOutlined />,
        isLeaf: isFile,
      };

      // If it's a directory (object), recursively convert children
      if (!isFile && typeof value === 'object') {
        treeNode.children = convertToTreeData(value, fullPath);
      }

      treeNodes.push(treeNode);
    }

    // Sort: directories first, then files, both alphabetically
    return treeNodes.sort((a, b) => {
      if (a.isLeaf === b.isLeaf) {
        return String(a.title).localeCompare(String(b.title));
      }
      return a.isLeaf ? 1 : -1;
    });
  };

  // Load file content by file path
  const loadFileContent = async (filePath: string) => {
    setSelectedFile(filePath);
    setLoadingContent(true);

    try {
      if (!functionBlockVersionId) {
        throw new Error('No function block version ID');
      }

      const response = await requestFBVersionContent(functionBlockVersionId, filePath);

      if (response.code !== 200) {
        throw new Error(response.message || 'Failed to load file content');
      }

      setFileContent(response.data || '');
    } catch (error: any) {
      console.error('Error loading file content:', error);
      message.error(`Failed to load file: ${error.message}`);
      setFileContent('');
    } finally {
      setLoadingContent(false);
    }
  };

  const loadStructure = async () => {
    if (!functionBlockVersionId) return;

    setLoadingStructure(true);
    try {
      const response = await requestFBVersionStructure(functionBlockVersionId);

      if (response.code !== 200) {
        throw new Error(response.message || 'Failed to load structure');
      }

      console.log('FB Structure response:', response);

      const structure = response.data;
      const treeNodes = convertToTreeData(structure);
      setTreeData(treeNodes);

      // Auto expand root level
      const rootKeys = treeNodes.map((node) => node.key);
      setExpandedKeys(rootKeys);

      // Auto open run.sh if it exists
      const runShNode = treeNodes.find((node) => node.key === 'run.sh');
      if (runShNode && runShNode.isLeaf) {
        // Load run.sh content automatically
        loadFileContent('run.sh');
      }
    } catch (error: any) {
      console.error('Error loading structure:', error);
      message.error(`Failed to load structure: ${error.message}`);
    } finally {
      setLoadingStructure(false);
    }
  };

  // Load file content when a file is selected
  const handleFileSelect = async (selectedKeys: React.Key[], info: any) => {
    if (selectedKeys.length === 0) return;

    const filePath = selectedKeys[0] as string;

    // Check if it's a file (leaf node)
    const selectedNode = info.node;
    if (!selectedNode.isLeaf) {
      // It's a directory, just toggle expand
      return;
    }

    loadFileContent(filePath);
  };

  // Get file language for syntax highlighting
  const getFileLanguage = (fileName: string | null): string => {
    if (!fileName) return 'plaintext';

    const extension = fileName.split('.').pop()?.toLowerCase();
    const languageMap: Record<string, string> = {
      py: 'python',
      js: 'javascript',
      jsx: 'javascript',
      ts: 'typescript',
      tsx: 'typescript',
      json: 'json',
      html: 'html',
      css: 'css',
      less: 'less',
      scss: 'scss',
      md: 'markdown',
      sh: 'shell',
      bash: 'shell',
      yaml: 'yaml',
      yml: 'yaml',
      xml: 'xml',
      r: 'r',
      sql: 'sql',
      txt: 'plaintext',
    };

    return languageMap[extension || ''] || 'plaintext';
  };

  const handleClose = () => {
    setTreeData([]);
    setSelectedFile(null);
    setFileContent('');
    setExpandedKeys([]);
    onClose();
  };

  const getAllFilesFromStructure = (struct: StructureData, parentPath: string = ''): string[] => {
    const files: string[] = [];
    for (const [name, value] of Object.entries(struct)) {
      const fullPath = parentPath ? `${parentPath}/${name}` : name;
      if (value === 'file') {
        files.push(fullPath);
      } else if (typeof value === 'object') {
        files.push(...getAllFilesFromStructure(value, fullPath));
      }
    }
    return files;
  };

  const handleDownloadCurrentNode = async () => {
    if (!functionBlockVersionId) {
      message.error('No function block version available');
      return;
    }

    try {
      setDownloadingCurrent(true);
      message.loading({ content: 'Fetching file structure...', key: 'download-current' });

      const structureResponse = await requestFBVersionStructure(functionBlockVersionId);
      if (structureResponse.code !== 200) {
        throw new Error(structureResponse.message || 'Failed to get file structure');
      }

      const structure = structureResponse.data;
      const allFiles = getAllFilesFromStructure(structure);

      if (allFiles.length === 0) {
        throw new Error('No files found in this function block');
      }

      message.loading({
        content: `Downloading ${allFiles.length} files...`,
        key: 'download-current',
      });

      const JSZip = (await import('jszip')).default;
      const zip = new JSZip();

      // Download file content
      for (const filePath of allFiles) {
        try {
          const contentResponse = await requestFBVersionContent(functionBlockVersionId, filePath);
          if (contentResponse.code === 200 && contentResponse.data) {
            zip.file(filePath, contentResponse.data);
          }
        } catch (e) {
          console.warn(`Failed to download file ${filePath}`);
        }
      }

      message.loading({ content: 'Creating zip file...', key: 'download-current' });

      // Generate and download the zip
      const zipBlob = await zip.generateAsync({ type: 'blob' });
      const downloadUrl = URL.createObjectURL(zipBlob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = nodeName
        ? `${nodeName.replace(/[^a-zA-Z0-9_-]/g, '_')}_code.zip`
        : 'code.zip';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(downloadUrl);

      message.success({ content: 'Download completed', key: 'download-current' });
    } catch (error: any) {
      console.error('Error downloading current node code:', error);
      message.error({ content: `Failed to download: ${error.message}`, key: 'download-current' });
    } finally {
      setDownloadingCurrent(false);
    }
  };

  const handleDownloadAllPrecedingNodes = async () => {
    if (!nodeId) {
      message.error('No node information available');
      return;
    }

    try {
      setDownloadingAll(true);
      message.loading({ content: 'Fetching preceding nodes...', key: 'download-all' });

      const { data: previousNodes } = await requestPreviousNodeList(nodeId, true);

      // Filter for computation nodes with FB versions
      const nodesWithFB = previousNodes.filter(
        (node: any) =>
          node.functionBlockVersionId &&
          (node.type === 'computation node' ||
            node.type === 'computation node v2' ||
            node.type === 'notebook node'),
      );

      if (nodesWithFB.length === 0) {
        message.warning({ content: 'No nodes with code found', key: 'download-all' });
        return;
      }

      message.loading({
        content: `Preparing download for ${nodesWithFB.length} nodes...`,
        key: 'download-all',
      });

      const JSZip = (await import('jszip')).default;
      const zip = new JSZip();

      let successCount = 0;

      for (let i = 0; i < nodesWithFB.length; i++) {
        const node = nodesWithFB[i];
        try {
          message.loading({
            content: `Downloading ${i + 1}/${nodesWithFB.length}: ${node.name}...`,
            key: 'download-all',
          });

          const structureResponse = await requestFBVersionStructure(node.functionBlockVersionId);
          if (structureResponse.code !== 200) continue;

          const structure = structureResponse.data;
          const folderName = node.name.replace(/[^a-zA-Z0-9_-]/g, '_');
          const nodeFolder = zip.folder(folderName);

          const allFiles = getAllFilesFromStructure(structure);

          // Download each file content
          for (const filePath of allFiles) {
            try {
              const contentResponse = await requestFBVersionContent(
                node.functionBlockVersionId,
                filePath,
              );
              if (contentResponse.code === 200 && contentResponse.data) {
                nodeFolder?.file(filePath, contentResponse.data);
              }
            } catch (e) {
              console.warn(`Failed to download file ${filePath} from node ${node.name}`);
            }
          }

          successCount++;
        } catch (error) {
          console.error(`Error processing node ${node.name}:`, error);
        }
      }

      if (successCount === 0) {
        message.error({ content: 'Failed to download any node code', key: 'download-all' });
        return;
      }

      message.loading({ content: 'Creating zip file...', key: 'download-all' });

      // Generate and download the zip
      const zipBlob = await zip.generateAsync({ type: 'blob' });
      const downloadUrl = URL.createObjectURL(zipBlob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = nodeName
        ? `${nodeName.replace(/[^a-zA-Z0-9_-]/g, '_')}_prev_pipeline_code.zip`
        : 'pipeline_code.zip';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(downloadUrl);

      message.success({
        content: `Downloaded code from ${successCount} nodes`,
        key: 'download-all',
      });
    } catch (error: any) {
      console.error('Error downloading all nodes code:', error);
      message.error({ content: `Failed to download: ${error.message}`, key: 'download-all' });
    } finally {
      setDownloadingAll(false);
    }
  };

  // Load directory structure
  useEffect(() => {
    if (visible && functionBlockVersionId) {
      loadStructure();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, functionBlockVersionId]);

  return (
    <Modal
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>View Code</span>
          <Space>
            <div style={{ marginRight: 24 }}>
              <Tooltip title="Download current node code as zip">
                <Button
                  type="text"
                  icon={<DownloadOutlined />}
                  onClick={handleDownloadCurrentNode}
                  loading={downloadingCurrent}
                  disabled={!functionBlockVersionId || downloadingCurrent || downloadingAll}
                >
                  Current Node
                </Button>
              </Tooltip>
              {nodeId && (
                <Tooltip title="Download all preceding nodes code as zip">
                  <Button
                    type="text"
                    icon={<DownloadOutlined />}
                    onClick={handleDownloadAllPrecedingNodes}
                    loading={downloadingAll}
                    disabled={downloadingCurrent || downloadingAll}
                  >
                    All Preceding Nodes
                  </Button>
                </Tooltip>
              )}
            </div>
          </Space>
        </div>
      }
      open={visible}
      onCancel={handleClose}
      footer={null}
      width="70vw"
      style={{ top: 20 }}
      bodyStyle={{ height: '85vh', padding: 0 }}
      className="fb-structure-dialog"
    >
      <div className="fb-structure-container">
        {/* Left Panel - File Tree */}
        <div className="fb-structure-left">
          <div className="fb-structure-header">File Structure</div>
          <div className="fb-structure-tree">
            {loadingStructure ? (
              <div className="fb-structure-loading">
                <Spin size="large" tip="Loading structure..." />
              </div>
            ) : treeData.length > 0 ? (
              <Tree
                showIcon
                treeData={treeData}
                onSelect={handleFileSelect}
                expandedKeys={expandedKeys}
                onExpand={(keys) => setExpandedKeys(keys)}
                selectedKeys={selectedFile ? [selectedFile] : []}
              />
            ) : (
              <Empty description="No structure data" />
            )}
          </div>
        </div>

        {/* Right Panel - File Content */}
        <div className="fb-structure-right">
          <div className="fb-structure-header">
            {selectedFile || 'Select a file to view content'}
          </div>
          <div className="fb-structure-content">
            {loadingContent ? (
              <div className="fb-structure-loading">
                <Spin
                  indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />}
                  tip="Loading file content..."
                />
              </div>
            ) : selectedFile ? (
              <Editor
                height="100%"
                language={getFileLanguage(selectedFile)}
                value={fileContent}
                theme="vs-dark"
                options={{
                  readOnly: true,
                  minimap: { enabled: true },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                  wordWrap: 'on',
                }}
              />
            ) : (
              <Empty
                description="Select a file from the left panel to view its content"
                style={{ marginTop: '20%' }}
              />
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default FBStructureDialog;
