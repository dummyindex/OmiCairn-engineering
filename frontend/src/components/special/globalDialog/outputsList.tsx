import React from 'react';
import { Modal, message, Button, Empty, Input, Select, Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useState, useEffect, useCallback } from 'react';
import { useModel } from 'umi';
import {
  requestComputationOutputList,
  requestLatestComputation,
  requestOutputFileDownloadInfo,
} from '@/request/computation';
import {
  AimOutlined,
  DownloadOutlined,
  FileOutlined,
  FolderOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { requestCreateNode, requestEditNodeParams, requestNodeInfo } from '@/request/node';
import { NodeType } from '@/constants/node';
import { PresetFBs } from '@/constants/functionBlock';
import { requestCreateEdge } from '@/request/edge';
import { requestDispatchTask } from '@/request/task';
import { debounce } from 'lodash';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

const { Search } = Input;
const { Option } = Select;

interface OutputFile {
  object_key: string;
  file_name: string;
  size: number | string;
  last_modified: string;
  collected: boolean;
  mime_type: string;
}

const formatFileSize = (bytes: number | string): string => {
  if (!bytes || bytes === '-' || bytes === 0) return '-';

  const numBytes = typeof bytes === 'string' ? parseInt(bytes, 10) : bytes;
  if (isNaN(numBytes)) return '-';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const k = 1024;
  const i = Math.floor(Math.log(numBytes) / Math.log(k));

  return `${(numBytes / Math.pow(k, i)).toFixed(2)} ${units[i]}`;
};

const OutputsList = () => {
  const { outputsListInspectedNodeId, setOutputsListInspectedNodeId } = useModel('analysis');
  const { dictionary } = useModel('localization');
  const [computationId, setComputationId] = useState<number | null>(null);
  const [downloadingDict, setDownloadingDict] = useState<{ [key: string]: boolean }>({});
  const [list, setList] = useState<OutputFile[]>([]);
  const [allData, setAllData] = useState<OutputFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [fileTypeFilter, setFileTypeFilter] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const pageSize = 50;

  const refreshComputationId = async () => {
    if (!outputsListInspectedNodeId) {
      setComputationId(null);
      return;
    }
    const { data: latestComputation } = await requestLatestComputation(
      outputsListInspectedNodeId + '',
    );
    if (!latestComputation) {
      setComputationId(null);
    } else {
      setComputationId(latestComputation.id);
    }
  };

  const updateDisplayList = (data: OutputFile[], page: number) => {
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedData = data.slice(startIndex, endIndex);
    setList(paginatedData);
    setCurrentPage(page);
  };

  const refreshOutputsList = async () => {
    if (!computationId || loading) {
      setList([]);
      setAllData([]);
      return;
    }

    setLoading(true);
    try {
      let allFiles: OutputFile[] = [];
      let hasMore = true;
      let startAfter: string | null = null;

      while (hasMore) {
        const { data: outputsS3Info } = await requestComputationOutputList(computationId + '', {
          search_query: searchQuery || undefined,
          file_type_filter: fileTypeFilter || undefined,
          start_after_file_name: startAfter || undefined,
          max_keys: 1000,
        });

        const { objects, has_more, next_start_after } = outputsS3Info;
        allFiles = [...allFiles, ...objects];
        hasMore = has_more;
        startAfter = next_start_after;
      }

      setAllData(allFiles);
      setCurrentPage(1);
      updateDisplayList(allFiles, 1);
    } catch (error) {
      console.error('Failed to load outputs:', error);
      message.error('Failed to load outputs');
    } finally {
      setLoading(false);
    }
  };

  // Debounced search handler
  const debouncedSearch = useCallback(
    debounce((query: string) => {
      setSearchQuery(query);
    }, 500),
    [],
  );

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    debouncedSearch(e.target.value);
  };

  const handleFileTypeChange = (value: string) => {
    setFileTypeFilter(value);
  };

  const downloadFile = async (key: string) => {
    if (!computationId) {
      message.error('computationId is null');
      return;
    }
    setDownloadingDict({
      ...downloadingDict,
      [key]: true,
    });
    try {
      const { data: url } = await requestOutputFileDownloadInfo(computationId + '', key);
      const a = document.createElement('a');
      a.href = url;
      a.download = key;
      a.click();
    } catch (e) {
      console.error(e);
      message.error('download failed');
    } finally {
      setDownloadingDict({
        ...downloadingDict,
        [key]: false,
      });
    }
  };

  const launchVisualization = async (key: string) => {
    try {
      const h5ad_key = key.split('/').slice(2).join('/');
      if (!outputsListInspectedNodeId) {
        message.error('Inspected node id is null');
        return;
      }
      const currentNode = await requestNodeInfo(outputsListInspectedNodeId);
      if (!currentNode) {
        message.error('Current node not found');
        return;
      }
      const { data: newNode } = await requestCreateNode(
        NodeType.COMPUTATION_NODE_V2,
        currentNode.x + 200,
        currentNode.y,
        currentNode.analysisId,
        null,
        PresetFBs.VISUAL.ID + '',
        `Decompose ${h5ad_key} for Visualization`,
      );
      if (!newNode) {
        message.error('Create new node failed');
        return;
      }
      const params = {
        h5ad_key: h5ad_key,
      };
      const editResponse = await requestEditNodeParams(newNode.id, params);
      if (!editResponse) {
        message.error('Edit node params failed');
        return;
      }
      const newEdge = await requestCreateEdge(currentNode.id, newNode.id, currentNode.analysisId);
      if (!newEdge) {
        message.error('Create edge failed');
        return;
      }
      message.success('Visualization launched');
      const launchComputationResponse = await requestDispatchTask(
        currentNode.analysisId,
        [newNode.id],
        [],
      );
      if (!launchComputationResponse) {
        message.error('Launch computation failed');
        return;
      }
    } catch (e) {
      console.error(e);
      message.error('Launch visualization failed');
    }
  };

  const columns: ColumnsType<OutputFile> = [
    {
      title: dictionary.NAME || 'Name',
      dataIndex: 'file_name',
      key: 'file_name',
      sorter: (a: OutputFile, b: OutputFile) => a.file_name.localeCompare(b.file_name),
      render: (text: string, record: OutputFile) => (
        <span>
          {record.mime_type === 'folder' ? <FolderOutlined /> : <FileOutlined />}
          <span style={{ marginLeft: 8 }}>{text}</span>
        </span>
      ),
    },
    {
      title: dictionary.FILE_SIZE || 'Size',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      sorter: (a: OutputFile, b: OutputFile) => {
        const aSize = typeof a.size === 'string' ? 0 : a.size;
        const bSize = typeof b.size === 'string' ? 0 : b.size;
        return aSize - bSize;
      },
      render: (size: number | string) => formatFileSize(size),
    },
    {
      title: dictionary.TYPE || 'Type',
      dataIndex: 'mime_type',
      key: 'mime_type',
      width: 100,
      sorter: (a: OutputFile, b: OutputFile) => a.mime_type.localeCompare(b.mime_type),
      render: (type: string) => (type === 'folder' ? 'Folder' : type.toUpperCase()),
    },
    {
      title: dictionary.ACTION || 'Action',
      key: 'action',
      width: 120,
      render: (_: any, record: OutputFile) => (
        <div style={{ display: 'flex', gap: 4 }}>
          {record.mime_type !== 'folder' && record.file_name.slice(-5) === '.h5ad' && (
            <Button
              title="Launch visualization"
              size="small"
              type="link"
              icon={<AimOutlined />}
              loading={downloadingDict[record.object_key]}
              onClick={() => launchVisualization(record.object_key)}
            />
          )}
          {record.mime_type !== 'folder' && (
            <Button
              title="Download file"
              size="small"
              type="link"
              icon={<DownloadOutlined />}
              loading={downloadingDict[record.object_key]}
              onClick={() => downloadFile(record.object_key)}
            />
          )}
        </div>
      ),
    },
  ];

  useEffect(() => {
    // Reset and refresh when filters change
    refreshOutputsList();
  }, [computationId, searchQuery, fileTypeFilter]);

  useEffect(() => {
    refreshComputationId();
  }, [outputsListInspectedNodeId]);

  return (
    <Modal
      width="60vw"
      centered
      title={dictionary.OUTPUTS}
      open={!!outputsListInspectedNodeId}
      cancelText={dictionary.CLOSE}
      okButtonProps={{ style: { display: 'none' } }}
      onCancel={() => {
        setOutputsListInspectedNodeId(null);
        // Reset state when closing
        setList([]);
        setAllData([]);
        setSearchQuery('');
        setFileTypeFilter('');
        setCurrentPage(1);
        setSelectedFiles([]);
      }}
    >
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
          <Search
            placeholder="Search files..."
            allowClear
            onChange={handleSearchChange}
            style={{ flex: 1 }}
            prefix={<SearchOutlined />}
          />
          <Select
            placeholder="File Type"
            allowClear
            style={{ width: 150 }}
            onChange={handleFileTypeChange}
            value={fileTypeFilter || undefined}
          >
            <Option value="">All Types</Option>
            <Option value="folder">Folders</Option>
            <Option value="png">PNG Images</Option>
            <Option value="jpg">JPG Images</Option>
            <Option value="pdf">PDF Files</Option>
            <Option value="csv">CSV Files</Option>
            <Option value="h5ad">H5AD Files</Option>
            <Option value="txt">Text Files</Option>
            <Option value="json">JSON Files</Option>
          </Select>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Button
            size="small"
            onClick={() => {
              const selectableFiles = allData
                .filter((file) => file.mime_type !== 'folder')
                .map((file) => file.object_key);
              setSelectedFiles(selectableFiles);
            }}
            disabled={loading || allData.length === 0}
          >
            Select All
          </Button>
          <Button
            size="small"
            onClick={() => setSelectedFiles([])}
            disabled={selectedFiles.length === 0}
          >
            Clear Selection
          </Button>
          <span style={{ color: '#666', fontSize: '12px' }}>
            {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected
          </span>
          {selectedFiles.length > 0 && (
            <Button
              type="primary"
              size="small"
              icon={<DownloadOutlined />}
              onClick={async () => {
                if (!computationId) {
                  message.error('Computation ID is missing');
                  return;
                }

                try {
                  const zip = new JSZip();

                  const totalFiles = selectedFiles.length;

                  for (let i = 0; i < totalFiles; i++) {
                    const fileKey = selectedFiles[i];
                    const fileName = fileKey.split('/').pop() || fileKey;

                    message.destroy();
                    message.loading(`Downloading files... ${i + 1}/${totalFiles}`, 0);

                    try {
                      const { data: url } = await requestOutputFileDownloadInfo(
                        computationId.toString(),
                        fileKey,
                      );

                      const response = await fetch(url);
                      const blob = await response.blob();

                      zip.file(fileName, blob);
                    } catch (fileError) {
                      console.error(`Failed to download ${fileName}:`, fileError);
                      message.error(`Failed to download ${fileName}`);
                    }
                  }

                  message.destroy();
                  message.loading('Creating zip file...', 0);

                  const content = await zip.generateAsync({ type: 'blob' });

                  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
                  saveAs(content, `outputs-${timestamp}.zip`);

                  message.destroy();
                  message.success('Download completed');
                } catch (error) {
                  message.destroy();
                  console.error('Bulk download error:', error);
                  message.error('Failed to download files as zip');
                }
              }}
              style={{ marginLeft: 'auto' }}
            >
              Download as ZIP
            </Button>
          )}
        </div>
      </div>
      <Table
        columns={columns}
        dataSource={list}
        rowKey="object_key"
        loading={loading}
        rowSelection={{
          type: 'checkbox',
          selectedRowKeys: selectedFiles,
          onChange: (selectedRowKeys: React.Key[]) => {
            const currentPageKeys = list.map((item) => item.object_key);

            const selectedFilesNotOnCurrentPage = selectedFiles.filter(
              (key) => !currentPageKeys.includes(key),
            );

            const newSelectedFiles = [...selectedFilesNotOnCurrentPage, ...selectedRowKeys];

            setSelectedFiles(newSelectedFiles as string[]);
          },
          getCheckboxProps: (record: OutputFile) => ({
            disabled: record.mime_type === 'folder',
          }),
        }}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: allData.length,
          showSizeChanger: false,
          showTotal: (total: number) => `Total ${total} items`,
          onChange: (page: number) => {
            updateDisplayList(allData, page);
          },
        }}
        scroll={{ y: '50vh' }}
        locale={{
          emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No outputs" />,
        }}
      />
    </Modal>
  );
};

export default OutputsList;
