import React, { useState, useEffect } from 'react';
import { Modal, Upload, Table, Button, message, Progress, Space, Typography } from 'antd';
import {
  DeleteOutlined,
  InboxOutlined,
  FileOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import {
  requestNodeParamFiles,
  requestUploadParamFile,
  requestDeleteParamFile,
} from '@/request/node';
import { uploadFileToS3 } from '@/request/awsOperation';
import type { UploadFile } from 'antd/es/upload/interface';

const { Dragger } = Upload;
const { Text } = Typography;

interface ExtraFilesDialogProps {
  visible: boolean;
  onCancel: () => void;
  onOk?: (files: UploadFile[]) => void;
  title?: string;
  maxFileSize?: number; // MB
  nodeId: string;
}

const ExtraFilesDialog: React.FC<ExtraFilesDialogProps> = ({
  visible,
  nodeId,
  onCancel,
  onOk,
  title = 'Extra files',
  maxFileSize = 100,
}) => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load the list of existing files
  useEffect(() => {
    const loadExistingFiles = async () => {
      if (visible && nodeId) {
        setLoading(true);
        try {
          const response = await requestNodeParamFiles(nodeId);
          if (response.code === 200 && response.data) {
            // Convert files returned by the server into UploadFile format
            const existingFiles: UploadFile[] = response.data.map((file: any, index: number) => {
              // Extract the file name from the Key (e.g. "node-space/26409/params-files/Output.txt" -> "Output.txt")
              const fileName = file.Key ? file.Key.split('/').pop() : 'Unknown';
              return {
                uid: file.Key || `existing-${index}`,
                name: fileName || 'Unknown',
                size: file.Size || 0,
                status: 'done' as const,
                percent: 100,
                url: file.Key, // Use the Key as the identifier
                uploadInfo: {
                  object_key: file.Key,
                  presigned_url: file.Key,
                },
              };
            });
            setFileList(existingFiles);
          }
        } catch (error: any) {
          console.error('Failed to load existing files:', error);
          message.error('Failed to load existing files');
        } finally {
          setLoading(false);
        }
      }
    };

    loadExistingFiles();
  }, [visible, nodeId]);

  // Handle file upload
  const handleFileChange = async (info: any) => {
    const { fileList: uploadFileList } = info;

    // Find newly added files (files not in the current fileList)
    const newFiles = uploadFileList.filter(
      (file: UploadFile) => !fileList.find((f) => f.uid === file.uid),
    );

    if (newFiles.length > 0) {
      setUploading(true);

      // Merge the existing file list with the new files
      const updatedFileList = [...fileList, ...newFiles];
      setFileList(updatedFileList);

      // Process newly uploaded files
      for (const file of newFiles) {
        if (file.originFileObj && !file.url) {
          try {
            // Check the file size
            const fileSizeMB = file.size! / (1024 * 1024);
            if (fileSizeMB > maxFileSize) {
              file.status = 'error';
              file.response = `File size exceeds ${maxFileSize}MB`;
              message.error(`${file.name} exceeds maximum file size (${maxFileSize}MB)`);
              setFileList([...updatedFileList]);
              continue;
            }

            // Set the file status to uploading
            file.status = 'uploading';
            file.percent = 0;
            setFileList([...updatedFileList]);

            // 1. Call requestUploadParamFile to get the upload information
            const { data: uploadInfo } = await requestUploadParamFile(
              nodeId,
              file.name,
              file.size!,
            );

            // 2. Call uploadFileToS3 to upload the file
            await uploadFileToS3(file.originFileObj as File, uploadInfo, (progress) => {
              file.percent = progress;
              setFileList([...updatedFileList]);
            });

            // Upload succeeded; save the upload information
            file.status = 'done';
            file.percent = 100;
            file.uploadInfo = uploadInfo;
            file.url = uploadInfo.presigned_url || uploadInfo.object_key;
            setFileList([...updatedFileList]);

            message.success(`${file.name} uploaded successfully`);
          } catch (error: any) {
            console.error('File upload error:', error);
            file.status = 'error';
            file.response = error.message || 'Upload failed';
            setFileList([...updatedFileList]);
            message.error(`${file.name} upload failed`);
          }
        }
      }

      setUploading(false);
    }
  };

  // Delete a file
  const handleRemove = async (file: UploadFile) => {
    try {
      // If the file has already been uploaded to the server (has uploadInfo.object_key), call the delete API
      if (file.status === 'done' && file.uploadInfo?.object_key) {
        setLoading(true);
        const response = await requestDeleteParamFile(nodeId, file.name);
        if (response.code === 200) {
          const newFileList = fileList.filter((item) => item.uid !== file.uid);
          setFileList(newFileList);
          message.success(`${file.name} deleted successfully`);
        } else {
          message.error(`Failed to delete ${file.name}`);
        }
      } else {
        // If the file is still uploading or failed, just remove it from the list
        const newFileList = fileList.filter((item) => item.uid !== file.uid);
        setFileList(newFileList);
        message.success(`${file.name} removed`);
      }
    } catch (error: any) {
      console.error('Failed to delete file:', error);
      message.error(`Failed to delete ${file.name}`);
    } finally {
      setLoading(false);
    }
  };

  // Custom upload logic (prevents the default behaviour)
  const beforeUpload = () => {
    return false; // Prevent automatic upload
  };

  // Handle the Cancel button
  const handleCancel = () => {
    setFileList([]);
    onCancel();
  };

  // Handle the OK button
  const handleOk = () => {
    const successfulFiles = fileList.filter((file) => file.status === 'done');
    if (onOk) {
      onOk(successfulFiles);
    }
    handleCancel();
  };

  // Render the file status icon
  const renderStatusIcon = (status?: string) => {
    switch (status) {
      case 'uploading':
        return <SyncOutlined spin style={{ color: '#1890ff' }} />;
      case 'done':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <FileOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  // Format the file size
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  // Table column configuration
  const columns = [
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      align: 'center' as const,
      render: (status: string) => renderStatusIcon(status),
    },
    {
      title: 'File Name',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      render: (name: string) => (
        <Space>
          <FileOutlined />
          <Text ellipsis={{ tooltip: name }}>{name}</Text>
        </Space>
      ),
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: 'Progress',
      dataIndex: 'percent',
      key: 'percent',
      width: 150,
      render: (percent: number, record: UploadFile) => {
        if (record.status === 'uploading') {
          return <Progress percent={Math.round(percent || 0)} size="small" />;
        }
        if (record.status === 'done') {
          return <Progress percent={100} size="small" status="success" />;
        }
        if (record.status === 'error') {
          return <Progress percent={percent || 0} size="small" status="exception" />;
        }
        return '-';
      },
    },
    {
      title: 'Action',
      key: 'action',
      width: 100,
      align: 'center' as const,
      render: (_: any, record: UploadFile) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleRemove(record)}
          disabled={record.status === 'uploading'}
        >
          Delete
        </Button>
      ),
    },
  ];

  return (
    <Modal
      title={title}
      open={visible}
      onCancel={handleCancel}
      onOk={handleOk}
      width={800}
      centered
      okText="Confirm"
      cancelText="Cancel"
      confirmLoading={loading}
      okButtonProps={{
        disabled: uploading || loading || fileList.filter((f) => f.status === 'done').length === 0,
      }}
      maskClosable={!uploading && !loading}
      closable={!uploading && !loading}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Upload area */}
        <div>
          <Dragger
            multiple
            fileList={[]}
            onChange={handleFileChange}
            beforeUpload={beforeUpload}
            showUploadList={false}
            disabled={uploading || loading}
            accept=".txt,.csv,.json,.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.zip,.tar,.gz"
            style={{
              background: '#fafafa',
              borderRadius: '8px',
            }}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text" style={{ fontSize: 16, fontWeight: 500 }}>
              Click or drag file to this area to upload
            </p>
            <p className="ant-upload-hint" style={{ color: '#8c8c8c' }}>
              Support for single or bulk upload. File size limit: {maxFileSize}MB per file.
            </p>
          </Dragger>
        </div>

        {/* File list */}
        <div>
          <div
            style={{
              marginBottom: 12,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Text strong style={{ fontSize: 14 }}>
              File List ({fileList.length})
            </Text>
            {fileList.length > 0 && (
              <Button
                size="small"
                danger
                onClick={() => {
                  setFileList([]);
                  message.success('All files cleared');
                }}
                disabled={uploading || loading}
              >
                Clear All
              </Button>
            )}
          </div>
          <Table
            columns={columns}
            dataSource={fileList}
            rowKey="uid"
            pagination={false}
            size="small"
            loading={loading}
            locale={{ emptyText: loading ? 'Loading files...' : 'No files uploaded yet' }}
            scroll={{ y: 300 }}
            style={{
              border: '1px solid #f0f0f0',
              borderRadius: '4px',
            }}
          />
        </div>

        {/* Statistics */}
        {fileList.length > 0 && (
          <div
            style={{
              padding: '12px',
              background: '#f5f5f5',
              borderRadius: '4px',
              display: 'flex',
              justifyContent: 'space-around',
            }}
          >
            <Text>
              <strong>Total:</strong> {fileList.length}
            </Text>
            <Text>
              <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 4 }} />
              <strong>Success:</strong> {fileList.filter((f) => f.status === 'done').length}
            </Text>
            <Text>
              <SyncOutlined spin style={{ color: '#1890ff', marginRight: 4 }} />
              <strong>Uploading:</strong> {fileList.filter((f) => f.status === 'uploading').length}
            </Text>
            <Text>
              <CloseCircleOutlined style={{ color: '#ff4d4f', marginRight: 4 }} />
              <strong>Failed:</strong> {fileList.filter((f) => f.status === 'error').length}
            </Text>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default ExtraFilesDialog;
