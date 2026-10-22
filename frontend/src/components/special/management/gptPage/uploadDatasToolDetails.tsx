import { UploadType, UploadFromType } from '@/constants/data';
import { Layout, Menu, Card, Form, Upload, Button, Input, Select, Progress, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useState, useEffect, useRef } from 'react';
import {
  requestCreateDataFrame,
  requestAnndataUploadInfo,
  requestCheckAnndataUpload,
  requestDataInfo,
} from '@/request/data';
import { requestImportDatas } from '@/request/analysis';
import { requestUploadToAWS, uploadFileToAWS } from '@/request/awsOperation';
import { requestV3ToolCallBack, requestV3UpdateChatSubTask } from '@/request/chat';

interface ItemType {
  label: string;
  key: string;
  disabled?: boolean;
  style?: React.CSSProperties;
  title?: string;
}

const speciesOptions = [
  { value: 'Mus musculus (Mouse)', label: 'Mus musculus (Mouse)' },
  { value: 'Homo sapiens (Human)', label: 'Homo sapiens (Human)' },
  { value: 'Danio rerio (Zebrafish)', label: 'Danio rerio (Zebrafish)' },
  { value: 'Drosophila melanogaster (Fruit fly)', label: 'Drosophila melanogaster (Fruit fly)' },
  { value: 'Caenorhabditis elegans (Nematode)', label: 'Caenorhabditis elegans (Nematode)' },
  { value: 'Rattus norvegicus (Rat)', label: 'Rattus norvegicus (Rat)' },
  { value: 'Arabidopsis thaliana (Thale cress)', label: 'Arabidopsis thaliana (Thale cress)' },
  {
    value: "Saccharomyces cerevisiae (Baker's yeast)",
    label: "Saccharomyces cerevisiae (Baker's yeast)",
  },
  { value: 'Gallus gallus (Chicken)', label: 'Gallus gallus (Chicken)' },
  { value: 'Sus scrofa (Pig)', label: 'Sus scrofa (Pig)' },
  { value: 'Bos taurus (Cattle)', label: 'Bos taurus (Cattle)' },
  { value: 'Macaca mulatta (Rhesus monkey)', label: 'Macaca mulatta (Rhesus monkey)' },
  {
    value: 'Xenopus tropicalis (Western clawed frog)',
    label: 'Xenopus tropicalis (Western clawed frog)',
  },
  { value: 'Others', label: 'Others' },
];

const UploadFormBox = ({ form, status, onSubmit, uploadProgress, hasDataId }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const isReadonly = status !== 'idle' && hasDataId;

  const getButtonText = () => {
    if (status === 'idle') {
      return hasDataId ? 'Continue' : 'Import';
    }
    if (status === 'uploaded') return 'Continue';
    if (status === 'preprocessing') return 'Preprocessing...';
    if (status === 'preprocessed') return 'Continue';
    if (status === 'completed') return 'Completed';
    if (status === 'error') return 'Continue';
    return 'Import';
  };

  const isButtonDisabled = () => {
    if (status === 'completed') return true;
    if (status === 'preprocessing') return true;
    if (!hasDataId && !file) return true; // A new upload requires a file
    return false;
  };

  const handleFileChange = (info: any) => {
    const { fileList } = info;
    if (fileList.length > 0) {
      const selectedFile = fileList[0].originFileObj || fileList[0];
      setFile(selectedFile);
      form.setFieldsValue({ file: selectedFile.name });
    } else {
      setFile(null);
      form.setFieldsValue({ file: null });
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (!file) {
        message.error('Please select a file to upload');
        return;
      }

      setUploading(true);
      await onSubmit({ ...values, file });
    } catch (error) {
      console.error('Form validation error:', error);
    } finally {
      setUploading(false);
    }
  };

  const uploadProps = {
    beforeUpload: () => false, // Prevent auto upload
    onChange: handleFileChange,
    accept: '.h5ad',
    showUploadList: false,
    disabled: isReadonly,
  };

  return (
    <div style={{ padding: '20px' }}>
      <Form form={form} layout="vertical">
        <Form.Item
          label="Name"
          name="name"
          rules={[{ required: true, message: 'Please enter a name' }]}
        >
          <Input placeholder="Enter dataset name" disabled={isReadonly} />
        </Form.Item>

        <Form.Item
          label="Species"
          name="species"
          rules={[{ required: true, message: 'Please select a species' }]}
        >
          <Select
            placeholder="Select species"
            options={speciesOptions}
            disabled={isReadonly}
            showSearch
            filterOption={(input, option) =>
              option?.label?.toLowerCase().indexOf(input.toLowerCase()) >= 0
            }
          />
        </Form.Item>

        <Form.Item
          label="Description"
          name="description"
          rules={[{ required: true, message: 'Please enter a description' }]}
        >
          <Input.TextArea placeholder="Enter dataset description" rows={3} disabled={isReadonly} />
        </Form.Item>

        <Form.Item
          label="File"
          name="file"
          rules={[{ required: !hasDataId, message: 'Please select a file' }]}
        >
          <div>
            {!hasDataId ? (
              <>
                <Upload {...uploadProps}>
                  <Button icon={<UploadOutlined />} disabled={isReadonly}>
                    Select File
                  </Button>
                </Upload>
                {file && (
                  <div style={{ marginTop: '8px', color: '#666' }}>
                    Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </div>
                )}
              </>
            ) : (
              <Input disabled={true} placeholder="File already uploaded" />
            )}
          </div>
        </Form.Item>

        {uploadProgress > 0 && uploadProgress < 100 && (
          <Form.Item>
            <Progress percent={uploadProgress} status="active" />
          </Form.Item>
        )}

        <Form.Item>
          <Button
            type="primary"
            onClick={handleSubmit}
            loading={uploading || status === 'preprocessing'}
            disabled={isButtonDisabled()}
          >
            {getButtonText()}
          </Button>
        </Form.Item>

        {status === 'error' && (
          <div style={{ color: '#ff4d4f', marginTop: '16px' }}>
            Upload failed. Please try again.
          </div>
        )}

        {(status === 'uploaded' || status === 'preprocessing' || status === 'preprocessed') && (
          <div style={{ color: '#1890ff', marginTop: '16px' }}>Processing... Please wait.</div>
        )}

        {status === 'completed' && (
          <div style={{ color: '#52c41a', marginTop: '16px' }}>Upload completed successfully!</div>
        )}
      </Form>
    </div>
  );
};

const UploadDatasToolDetails = ({ subTask, analysisId }) => {
  const subTaskStatus = subTask?.status;
  const currentDetails = JSON.parse(subTask?.outputs || '{}');

  const [form] = Form.useForm();
  const [uploadType, setUploadType] = useState<string>(UploadType.ANNDATA);
  const [uploadProgress, setUploadProgress] = useState(0);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const toolCallbackCalledRef = useRef<boolean>(false);

  const { data_id: dataId, status = 'idle' } = currentDetails;

  const loadDataInfo = async (dataId: string) => {
    try {
      const { data } = await requestDataInfo(dataId);
      form.setFieldsValue({
        name: data.name,
        species: data.species,
        description: data.description,
        file: data.filename || 'Uploaded file',
      });
    } catch (error) {
      console.error('Failed to load data info:', error);
    }
  };

  const updateSubTaskOutputs = async (newOutputs: any) => {
    try {
      console.log('subTaskId', subTask.id);
      await requestV3UpdateChatSubTask(subTask.id, {
        outputs: JSON.stringify(newOutputs),
      });
    } catch (error) {
      console.error('Failed to update subtask outputs:', error);
    }
  };

  const startPolling = (dataId: string) => {
    // If already polling, clear it first
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    // Reset the callback-called flag
    toolCallbackCalledRef.current = false;

    const interval = setInterval(async () => {
      try {
        const { data } = await requestDataInfo(dataId);

        if (data.state === 'ok') {
          clearInterval(interval);
          pollingIntervalRef.current = null;

          // Update status to preprocessed
          await updateSubTaskOutputs({
            status: 'preprocessed',
            data_id: dataId,
          });

          // Import data to analysis
          if (analysisId) {
            await requestImportDatas(analysisId, [dataId]);
          }

          // Update status to completed
          await updateSubTaskOutputs({
            status: 'completed',
            data_id: dataId,
          });

          // Ensure requestV3ToolCallBack is called only once
          if (!toolCallbackCalledRef.current) {
            toolCallbackCalledRef.current = true;
            await requestV3ToolCallBack(subTask.id, {
              status: 'completed',
              data_id: dataId,
              data: data,
            });
          }
        } else if (data.state === 'error') {
          clearInterval(interval);
          pollingIntervalRef.current = null;

          await updateSubTaskOutputs({
            status: 'error',
            data_id: dataId,
            error: data.error || 'Processing failed',
          });

          // Ensure requestV3ToolCallBack is called only once
          if (!toolCallbackCalledRef.current) {
            toolCallbackCalledRef.current = true;
            await requestV3ToolCallBack(subTask.id, {
              status: 'error',
              data_id: dataId,
              data: data,
            });
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 3000); // Poll every 3 seconds

    pollingIntervalRef.current = interval;
  };

  const handleSubmit = async (formData: any) => {
    const { name, species, description, file } = formData;
    let currentDataId = dataId;

    try {
      // If there is no dataId, create the data frame starting from step 6.1
      if (!currentDataId) {
        // 6.1. Create data frame
        const { data: dataFrame } = await requestCreateDataFrame(
          UploadFromType.FROMUPLOADEDDIRECTLY,
          name,
          UploadType.ANNDATA,
          species,
          description,
        );

        currentDataId = dataFrame.id;

        // 6.2. Get upload info
        const { data: uploadInfo } = await requestAnndataUploadInfo(currentDataId, file.size);

        // 6.3. Upload file
        if (uploadInfo.multipart) {
          await requestUploadToAWS(
            file,
            uploadInfo.partInfoList,
            uploadInfo.part_count,
            uploadInfo.part_size,
            uploadInfo.object_key,
            uploadInfo.uploadId,
            (progress: number) => {
              setUploadProgress(Math.ceil(progress));
            },
          );
        } else {
          const abortController = new AbortController();
          await uploadFileToAWS(
            file,
            uploadInfo.presigned_url,
            abortController,
            (progress: number) => {
              setUploadProgress(Math.ceil(progress));
            },
          );
        }

        // 6.4. Update status to uploaded
        await updateSubTaskOutputs({
          status: 'uploaded',
          data_id: currentDataId,
        });

        // 6.5. Start preprocessing
        await requestCheckAnndataUpload(currentDataId);

        // 6.6. Update status to preprocessing
        await updateSubTaskOutputs({
          status: 'preprocessing',
          data_id: currentDataId,
        });
      }

      // If the status is uploaded but preprocessing has not started, continue the preprocessing flow
      if (status === 'uploaded') {
        // 6.5. Start preprocessing
        await requestCheckAnndataUpload(currentDataId);

        // 6.6. Update status to preprocessing
        await updateSubTaskOutputs({
          status: 'preprocessing',
          data_id: currentDataId,
        });
      }

      // If the status is preprocessed but the import is not finished, continue the import flow
      if (status === 'preprocessed') {
        // Import data to analysis
        if (analysisId) {
          await requestImportDatas(analysisId, [currentDataId]);
        }

        // Update status to completed
        await updateSubTaskOutputs({
          status: 'completed',
          data_id: currentDataId,
        });

        message.success('Data import completed successfully!');
        setUploadProgress(0);
        return;
      }

      // 6.6. Start polling (for preprocessing and any status that needs monitoring)
      if (status !== 'completed' && status !== 'error') {
        startPolling(currentDataId);
      }

      setUploadProgress(0);
      message.success('Processing started successfully...');
    } catch (error: any) {
      console.error('Upload error:', error);
      message.error('Operation failed: ' + (error?.message || 'Unknown error'));

      if (currentDataId) {
        await updateSubTaskOutputs({
          status: 'error',
          data_id: currentDataId,
          error: error?.message || 'Operation failed',
        });
      }
    }
  };

  useEffect(() => {
    // Check the status when the component first loads
    if (dataId) {
      loadDataInfo(dataId);

      // If the status is preprocessing, start polling
      if (status === 'preprocessing' && subTaskStatus !== 'finished') {
        startPolling(dataId);
      }
    }

    // If the subTask status becomes finished, reset the callback flag
    if (subTaskStatus === 'finished') {
      toolCallbackCalledRef.current = true; // Prevent calling it again
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [dataId, status, subTaskStatus]);

  const items: ItemType[] = [
    {
      label: UploadType.ANNDATA,
      key: UploadType.ANNDATA,
    },
  ];

  if (subTaskStatus === 'finished') {
    const { status, data_id, data, error } = currentDetails;

    if (status === 'error') {
      return (
        <Card title="Upload Details" size="small" style={{ marginBottom: '16px' }}>
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: '12px',
                fontSize: '14px',
                fontWeight: 600,
                color: '#ff4d4f',
              }}
            >
              <span
                style={{
                  width: '8px',
                  height: '8px',
                  backgroundColor: '#ff4d4f',
                  borderRadius: '50%',
                  marginRight: '8px',
                }}
              ></span>
              Upload Failed
            </div>

            <div style={{ marginBottom: '12px' }}>
              <div
                style={{
                  fontSize: '12px',
                  color: '#666',
                  marginBottom: '4px',
                  fontWeight: 500,
                }}
              >
                Error Message
              </div>
              <div
                style={{
                  fontSize: '12px',
                  color: '#ff4d4f',
                  padding: '10px',
                  backgroundColor: '#fff2f0',
                  borderRadius: '4px',
                  border: '1px solid #ffccc7',
                  minHeight: '40px',
                  lineHeight: '1.5',
                }}
              >
                {error || 'Unknown error occurred during upload'}
              </div>
            </div>

            {data_id && (
              <div style={{ marginBottom: '12px' }}>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#666',
                    marginBottom: '4px',
                    fontWeight: 500,
                  }}
                >
                  Data ID
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#333',
                    padding: '4px 8px',
                    backgroundColor: '#f5f5f5',
                    borderRadius: '4px',
                    fontFamily: 'monospace',
                  }}
                >
                  {data_id}
                </div>
              </div>
            )}

            <div
              style={{
                fontSize: '12px',
                color: '#666',
                marginBottom: '4px',
                fontWeight: 500,
              }}
            >
              Status
            </div>
            <div
              style={{
                fontSize: '12px',
                color: '#ff4d4f',
                padding: '4px 8px',
                backgroundColor: '#fff2f0',
                borderRadius: '4px',
                border: '1px solid #ffccc7',
                fontWeight: 500,
              }}
            >
              Error
            </div>
          </div>
        </Card>
      );
    }

    // status === 'completed' or another success status
    return (
      <Card title="Upload Details" size="small" style={{ marginBottom: '16px' }}>
        <div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '12px',
              fontSize: '14px',
              fontWeight: 600,
              color: '#52c41a',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                backgroundColor: '#52c41a',
                borderRadius: '50%',
                marginRight: '8px',
              }}
            ></span>
            Upload Completed Successfully
          </div>

          <div style={{ marginBottom: '12px' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
                marginBottom: '12px',
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#666',
                    marginBottom: '4px',
                    fontWeight: 500,
                  }}
                >
                  Dataset Name
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#333',
                    padding: '4px 8px',
                    backgroundColor: '#f5f5f5',
                    borderRadius: '4px',
                  }}
                >
                  {data?.name || 'N/A'}
                </div>
              </div>

              <div>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#666',
                    marginBottom: '4px',
                    fontWeight: 500,
                  }}
                >
                  Species
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#333',
                    padding: '4px 8px',
                    backgroundColor: '#f5f5f5',
                    borderRadius: '4px',
                  }}
                >
                  {data?.species || 'N/A'}
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <div
                style={{
                  fontSize: '12px',
                  color: '#666',
                  marginBottom: '4px',
                  fontWeight: 500,
                }}
              >
                Description
              </div>
              <div
                style={{
                  fontSize: '12px',
                  color: '#333',
                  padding: '10px',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '4px',
                  minHeight: '40px',
                  lineHeight: '1.5',
                }}
              >
                {data?.description || 'No description available'}
              </div>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#666',
                    marginBottom: '4px',
                    fontWeight: 500,
                  }}
                >
                  Status
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#52c41a',
                    padding: '4px 8px',
                    backgroundColor: '#f6ffed',
                    borderRadius: '4px',
                    border: '1px solid #b7eb8f',
                    fontWeight: 500,
                  }}
                >
                  {status || 'Completed'}
                </div>
              </div>

              <div>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#666',
                    marginBottom: '4px',
                    fontWeight: 500,
                  }}
                >
                  Data ID
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#333',
                    padding: '4px 8px',
                    backgroundColor: '#f5f5f5',
                    borderRadius: '4px',
                    fontFamily: 'monospace',
                  }}
                >
                  {data_id || 'N/A'}
                </div>
              </div>
            </div>
          </div>

          {data && Object.keys(data).length > 0 && (
            <div
              style={{
                marginTop: '15px',
                padding: '10px',
                backgroundColor: '#fafafa',
                borderRadius: '6px',
                border: '1px solid #e8e8e8',
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  color: '#666',
                  marginBottom: '8px',
                  fontWeight: 500,
                }}
              >
                Additional Data Information
              </div>
              <div
                style={{
                  fontSize: '12px',
                  color: '#333',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  maxHeight: '200px',
                  overflowY: 'auto',
                }}
              >
                {JSON.stringify(data, null, 2)}
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  }

  const renderUploadPanel = () => {
    return (
      <UploadFormBox
        form={form}
        status={status}
        onSubmit={handleSubmit}
        uploadProgress={uploadProgress}
        hasDataId={!!dataId}
      />
    );
  };

  return (
    <Card>
      <Layout>
        <Layout.Header style={{ background: '#fff', padding: 0 }}>
          <Menu
            style={{ width: '100%' }}
            selectedKeys={[uploadType]}
            onClick={({ key }) => setUploadType(key)}
            items={items}
          />
        </Layout.Header>
        <Layout.Content>{renderUploadPanel()}</Layout.Content>
      </Layout>
    </Card>
  );
};

export default UploadDatasToolDetails;
