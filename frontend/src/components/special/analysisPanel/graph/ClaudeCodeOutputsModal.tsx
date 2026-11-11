import React, { useCallback, useEffect, useState } from 'react';
import { Modal, message, Button, Empty, Input, Select, Spin, Tooltip, Drawer, Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  DownloadOutlined,
  FileOutlined,
  FolderOutlined,
  SearchOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import Editor from '@monaco-editor/react';
import ReactMarkdown from 'react-markdown';
import { requestComputationOutputList, requestOutputFileDownloadInfo } from '@/request/computation';
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
  mime_type: string;
}

interface PreviewState {
  file: OutputFile | null;
  loading: boolean;
  content: string | null;
  url: string | null;
  error: string | null;
}

const PREVIEWABLE_IMAGE_TYPES = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'];
const PREVIEWABLE_TEXT_TYPES = [
  'txt',
  'py',
  'r',
  'sh',
  'json',
  'jsonl',
  'yaml',
  'yml',
  'xml',
  'html',
  'css',
  'js',
  'ts',
  'tsx',
  'jsx',
  'sql',
  'log',
];
const PREVIEWABLE_MARKDOWN_TYPES = ['md', 'markdown'];
const PREVIEWABLE_CSV_TYPES = ['csv', 'tsv'];
const PREVIEWABLE_PDF_TYPES = ['pdf'];

const isPreviewable = (mimeType: string): boolean => {
  const lowerType = mimeType.toLowerCase();
  return (
    PREVIEWABLE_IMAGE_TYPES.includes(lowerType) ||
    PREVIEWABLE_TEXT_TYPES.includes(lowerType) ||
    PREVIEWABLE_MARKDOWN_TYPES.includes(lowerType) ||
    PREVIEWABLE_CSV_TYPES.includes(lowerType) ||
    PREVIEWABLE_PDF_TYPES.includes(lowerType)
  );
};

const getMonacoLanguage = (mimeType: string): string => {
  const languageMap: { [key: string]: string } = {
    py: 'python',
    r: 'r',
    sh: 'shell',
    json: 'json',
    jsonl: 'json',
    yaml: 'yaml',
    yml: 'yaml',
    xml: 'xml',
    html: 'html',
    css: 'css',
    js: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    jsx: 'javascript',
    sql: 'sql',
    txt: 'plaintext',
    log: 'plaintext',
  };
  return languageMap[mimeType.toLowerCase()] || 'plaintext';
};

interface ClaudeCodeOutputsModalProps {
  visible: boolean;
  computationId: string | null;
  loadingComputationId?: boolean;
  onClose: () => void;
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

const PreviewContent = ({
  file,
  content,
  url,
}: {
  file: OutputFile;
  content: string | null;
  url: string | null;
}) => {
  const mimeType = file.mime_type.toLowerCase();

  if (PREVIEWABLE_IMAGE_TYPES.includes(mimeType) && url) {
    return (
      <div style={{ textAlign: 'center', padding: 16 }}>
        <img
          src={url}
          alt={file.file_name}
          style={{
            maxWidth: '100%',
            maxHeight: 'calc(100vh - 200px)',
            objectFit: 'contain',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}
        />
      </div>
    );
  }

  if (PREVIEWABLE_PDF_TYPES.includes(mimeType) && url) {
    return (
      <iframe
        src={url}
        title={file.file_name}
        style={{
          width: '100%',
          height: 'calc(100vh - 150px)',
          border: 'none',
        }}
      />
    );
  }

  if (PREVIEWABLE_MARKDOWN_TYPES.includes(mimeType) && content) {
    return (
      <div
        style={{
          padding: 16,
          backgroundColor: '#fff',
          borderRadius: 4,
          maxHeight: 'calc(100vh - 150px)',
          overflowY: 'auto',
        }}
        className="markdown-preview"
      >
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    );
  }

  if (PREVIEWABLE_CSV_TYPES.includes(mimeType) && content) {
    const delimiter = mimeType === 'tsv' ? '\t' : ',';
    const lines = content.split('\n').filter((line) => line.trim());
    const headers = lines[0]?.split(delimiter) || [];
    const dataRows = lines.slice(1, 101);

    const columns = headers.map((header, index) => ({
      title: header.trim(),
      dataIndex: `col_${index}`,
      key: `col_${index}`,
      ellipsis: true,
    }));

    const dataSource = dataRows.map((row, rowIndex) => {
      const cells = row.split(delimiter);
      const rowData: { [key: string]: string } = { key: `row_${rowIndex}` };
      cells.forEach((cell, cellIndex) => {
        rowData[`col_${cellIndex}`] = cell.trim();
      });
      return rowData;
    });

    return (
      <div style={{ maxHeight: 'calc(100vh - 150px)', overflowY: 'auto' }}>
        <div style={{ marginBottom: 8, color: '#666', fontSize: 12 }}>
          Showing first {Math.min(100, dataRows.length)} of {lines.length - 1} rows
        </div>
        <Table
          columns={columns}
          dataSource={dataSource}
          pagination={false}
          scroll={{ x: 'max-content' }}
          size="small"
          bordered
        />
      </div>
    );
  }

  if (content) {
    return (
      <div style={{ height: 'calc(100vh - 150px)' }}>
        <Editor
          height="100%"
          language={getMonacoLanguage(mimeType)}
          value={content}
          theme="vs-light"
          options={{
            readOnly: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            fontSize: 13,
          }}
        />
      </div>
    );
  }

  return <Empty description="Unable to preview this file" />;
};

const getFileIcon = (mimeType: string) => {
  const iconStyle = { marginRight: 8 };
  if (mimeType === 'folder') return <FolderOutlined style={iconStyle} />;
  if (['png', 'jpg', 'jpeg', 'gif', 'svg'].includes(mimeType)) {
    return <FileOutlined style={{ ...iconStyle, color: '#52c41a' }} />;
  }
  if (['py', 'r', 'sh'].includes(mimeType)) {
    return <FileOutlined style={{ ...iconStyle, color: '#1890ff' }} />;
  }
  if (['csv', 'tsv', 'json', 'jsonl'].includes(mimeType)) {
    return <FileOutlined style={{ ...iconStyle, color: '#fa8c16' }} />;
  }
  return <FileOutlined style={iconStyle} />;
};

const ClaudeCodeOutputsModal = ({
  visible,
  computationId,
  loadingComputationId = false,
  onClose,
}: ClaudeCodeOutputsModalProps) => {
  const [downloadingDict, setDownloadingDict] = useState<{ [key: string]: boolean }>({});
  const [list, setList] = useState<OutputFile[]>([]);
  const [allData, setAllData] = useState<OutputFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [fileTypeFilter, setFileTypeFilter] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [preview, setPreview] = useState<PreviewState>({
    file: null,
    loading: false,
    content: null,
    url: null,
    error: null,
  });
  const pageSize = 50;

  const updateDisplayList = (data: OutputFile[], page: number) => {
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedData = data.slice(startIndex, endIndex);
    setList(paginatedData);
    setCurrentPage(page);
  };

  const refreshOutputsList = useCallback(async () => {
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
        const { data: outputsS3Info } = await requestComputationOutputList(computationId, {
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
  }, [computationId, searchQuery, fileTypeFilter]);

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
      message.error('Computation ID is missing');
      return;
    }
    setDownloadingDict((prev) => ({ ...prev, [key]: true }));
    try {
      const { data: url } = await requestOutputFileDownloadInfo(computationId, key);
      if (url) {
        const a = document.createElement('a');
        a.href = url;
        a.download = key;
        a.click();
      } else {
        message.error('Failed to get download URL');
      }
    } catch (e) {
      console.error(e);
      message.error('Download failed');
    } finally {
      setDownloadingDict((prev) => ({ ...prev, [key]: false }));
    }
  };

  const previewFile = async (file: OutputFile) => {
    if (!computationId) {
      message.error('Computation ID is missing');
      return;
    }

    const mimeType = file.mime_type.toLowerCase();

    setPreview({
      file,
      loading: true,
      content: null,
      url: null,
      error: null,
    });

    try {
      const { data: presignedUrl } = await requestOutputFileDownloadInfo(
        computationId,
        file.object_key,
      );
      if (!presignedUrl) {
        throw new Error('Failed to get presigned URL');
      }

      if (PREVIEWABLE_IMAGE_TYPES.includes(mimeType) || PREVIEWABLE_PDF_TYPES.includes(mimeType)) {
        setPreview((prev) => ({
          ...prev,
          loading: false,
          url: presignedUrl,
        }));
        return;
      }

      const fetchResponse = await fetch(presignedUrl);
      if (!fetchResponse.ok) {
        throw new Error('Failed to fetch file content');
      }

      const text = await fetchResponse.text();

      const maxSize = 5 * 1024 * 1024;
      const content =
        text.length > maxSize ? text.substring(0, maxSize) + '\n\n... (Content truncated)' : text;

      setPreview((prev) => ({
        ...prev,
        loading: false,
        content,
        url: presignedUrl,
      }));
    } catch (error) {
      console.error('Preview failed:', error);
      setPreview((prev) => ({
        ...prev,
        loading: false,
        error: 'Failed to load file preview',
      }));
    }
  };

  const closePreview = () => {
    setPreview({
      file: null,
      loading: false,
      content: null,
      url: null,
      error: null,
    });
  };

  const downloadSelectedAsZip = async () => {
    if (!computationId || selectedFiles.length === 0) return;

    try {
      const zip = new JSZip();
      const totalFiles = selectedFiles.length;

      for (let i = 0; i < totalFiles; i++) {
        const fileKey = selectedFiles[i];
        const fileName = fileKey.split('/').pop() || fileKey;

        message.destroy();
        message.loading(`Downloading files... ${i + 1}/${totalFiles}`, 0);

        try {
          const { data: url } = await requestOutputFileDownloadInfo(computationId, fileKey);
          if (url) {
            const response = await fetch(url);
            const blob = await response.blob();
            zip.file(fileName, blob);
          }
        } catch (fileError) {
          console.error(`Failed to download ${fileName}:`, fileError);
        }
      }

      message.destroy();
      message.loading('Creating zip file...', 0);

      const content = await zip.generateAsync({ type: 'blob' });
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      saveAs(content, `claude-code-outputs-${timestamp}.zip`);

      message.destroy();
      message.success('Download completed');
    } catch (error) {
      message.destroy();
      console.error('Bulk download error:', error);
      message.error('Failed to download files as zip');
    }
  };

  const columns: ColumnsType<OutputFile> = [
    {
      title: 'Name',
      dataIndex: 'file_name',
      key: 'file_name',
      sorter: (a: OutputFile, b: OutputFile) => a.file_name.localeCompare(b.file_name),
      render: (text: string, record: OutputFile) => (
        <span>
          {getFileIcon(record.mime_type)}
          <span style={{ marginLeft: 8 }}>{text}</span>
        </span>
      ),
    },
    {
      title: 'Size',
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
      title: 'Type',
      dataIndex: 'mime_type',
      key: 'mime_type',
      width: 100,
      sorter: (a: OutputFile, b: OutputFile) => a.mime_type.localeCompare(b.mime_type),
      render: (type: string) => (type === 'folder' ? 'Folder' : type.toUpperCase()),
    },
    {
      title: 'Action',
      key: 'action',
      width: 120,
      render: (_: any, record: OutputFile) => (
        <div style={{ display: 'flex', gap: 4 }}>
          {record.mime_type !== 'folder' && isPreviewable(record.mime_type) && (
            <Tooltip title="Preview">
              <Button
                size="small"
                type="link"
                icon={<EyeOutlined />}
                onClick={() => previewFile(record)}
              />
            </Tooltip>
          )}
          {record.mime_type !== 'folder' && (
            <Tooltip title="Download">
              <Button
                size="small"
                type="link"
                icon={<DownloadOutlined />}
                loading={downloadingDict[record.object_key]}
                onClick={() => downloadFile(record.object_key)}
              />
            </Tooltip>
          )}
        </div>
      ),
    },
  ];

  useEffect(() => {
    if (visible && computationId) {
      refreshOutputsList();
    }
  }, [visible, computationId, searchQuery, fileTypeFilter]);

  useEffect(() => {
    if (!visible) {
      setList([]);
      setAllData([]);
      setSearchQuery('');
      setFileTypeFilter('');
      setCurrentPage(1);
      setSelectedFiles([]);
      closePreview();
    }
  }, [visible]);

  return (
    <Modal
      width="70vw"
      centered
      title={`Agent Outputs${allData.length > 0 ? ` (${allData.length} files)` : ''}`}
      open={visible}
      cancelText="Close"
      okButtonProps={{ style: { display: 'none' } }}
      onCancel={onClose}
    >
      {loadingComputationId ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin />
          <span style={{ marginLeft: 8 }}>Loading computation...</span>
        </div>
      ) : !computationId ? (
        <Empty description="No computation found for this node" />
      ) : (
        <>
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
                <Option value="py">Python Files</Option>
                <Option value="md">Markdown Files</Option>
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
                  onClick={downloadSelectedAsZip}
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
        </>
      )}

      <Drawer
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {preview.file && getFileIcon(preview.file.mime_type)}
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {preview.file?.file_name || 'File Preview'}
            </span>
            <Button
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => {
                if (preview.file) {
                  downloadFile(preview.file.object_key);
                }
              }}
            >
              Download
            </Button>
          </div>
        }
        placement="right"
        width="60vw"
        open={preview.file !== null}
        onClose={closePreview}
        destroyOnClose
      >
        {preview.loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
            <p style={{ marginTop: 16, color: '#666' }}>Loading preview...</p>
          </div>
        ) : preview.error ? (
          <Empty description={preview.error} />
        ) : preview.file ? (
          <PreviewContent file={preview.file} content={preview.content} url={preview.url} />
        ) : null}
      </Drawer>
    </Modal>
  );
};

export default ClaudeCodeOutputsModal;
