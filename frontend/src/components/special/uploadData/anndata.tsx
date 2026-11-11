import { ServiceCloud } from '@/constants';
import { UploadFromType, UploadType } from '@/constants/data';
import { ServiceCloudSelection } from '@/constants/serviceCloudSelection';
import {
  requestAnndataUploadInfo,
  requestCheckAnndataUpload,
  requestCreateDataFrame,
  requestValidateUpdate,
} from '@/request/data';
import { AnalysisType } from '@/constants/analysis';
import {
  CheckCircleTwoTone,
  CloseOutlined,
  DeleteOutlined,
  EditOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { Form, message, Progress, Table, Select, Input, Popconfirm, Button } from 'antd';
import React from 'react';
import { requestCancelUpload, requestUploadToAWS, uploadFileToAWS } from '@/request/awsOperation';
import { requestImportDatas } from '@/request/analysis';
import { getLocationParams } from '@/util/getUrl';
import styles from './anndata.less';

const speciesOptions = [
  { value: 'Mus musculus (Mouse)' },
  { value: 'Homo sapiens (Human)' },
  { value: 'Other species' },
];

interface AnndataUploadProps {
  // From uploadDataUI model
  closeUploadDataUI: () => void;
  anndataUploadProgress: Record<string, number>;
  setAnndataUploadProgress: React.Dispatch<React.SetStateAction<Record<string, number>>>;
  currentAnndataUploadIdRef: Record<string, string>;
  setCurrentAnndataUploadIdRef: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  isAnndataUploading: Record<string, boolean>;
  setIsAnndataUploading: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  setFileList: React.Dispatch<React.SetStateAction<Record<string, File>>>;
  targetAnalysisId: string | null;
  isAnndataUploadSuccess: Record<string, boolean>;
  setIsAnndataUploadSuccess: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  persistentDataSource: {
    key: string;
    filename: string;
    species: string;
    description: string;
    progress: number;
  }[];
  setPersistentDataSource: React.Dispatch<
    React.SetStateAction<
      { key: string; filename: string; species: string; description: string; progress: number }[]
    >
  >;
  persistentSelectedFiles: { file: File; key: string }[];
  setPersistentSelectedFiles: React.Dispatch<React.SetStateAction<{ file: File; key: string }[]>>;

  // From analysis model
  analysisAccessType: string | null;

  // From user model
  isGuest: () => boolean;
}

const AnndataUpload: React.FC<AnndataUploadProps> = ({
  closeUploadDataUI,
  anndataUploadProgress,
  setAnndataUploadProgress,
  currentAnndataUploadIdRef,
  setCurrentAnndataUploadIdRef,
  isAnndataUploading,
  setIsAnndataUploading,
  setFileList,
  targetAnalysisId,
  isAnndataUploadSuccess,
  setIsAnndataUploadSuccess,
  persistentDataSource,
  setPersistentDataSource,
  persistentSelectedFiles,
  setPersistentSelectedFiles,
  analysisAccessType,
  isGuest,
}) => {
  const [form] = Form.useForm();
  const [objectKey, setObjectKey] = React.useState<Record<string, string>>({});
  const [isMultipart, setIsMultipart] = React.useState<Record<string, boolean>>({});
  const [editingKey, setEditingKey] = React.useState(null);
  const [uploadingControllers, setUploadingControllers] = React.useState<
    Record<string, AbortController>
  >({});
  const [isDragging, setIsDragging] = React.useState(false);
  const [analysisId, setAnalysisId] = React.useState<string | null>(null);
  const isGuestUser = isGuest();

  React.useEffect(() => {
    if (persistentDataSource.length > 0) {
      setPersistentDataSource(persistentDataSource);
    }
  }, [persistentDataSource]);

  const getAnalysisId = async () => {
    const [currentanalysisId] = getLocationParams(['analysis-id']);
    setAnalysisId(currentanalysisId);
  };

  React.useEffect(() => {
    getAnalysisId();
  }, []);

  const handleEdit = (record) => {
    setEditingKey(record.key);
  };

  const handleSave = () => {
    setEditingKey(null);
  };

  const pushFile = (file: any) => {
    setFileList((prev) => ({ ...prev, [file.name]: file }));
  };

  const addFilesToDataSource = (files) => {
    const validFiles = files.filter((file) => file.name.endsWith('.h5ad'));
    if (validFiles.length === 0) {
      message.error('Please upload .h5ad files only.');
      return;
    }

    const filesWithKeys = validFiles.map((file) => ({
      file,
      key: `${file.name}-${Date.now()}`,
    }));
    setPersistentSelectedFiles((prevFiles) => [...prevFiles, ...filesWithKeys]);

    const newData = filesWithKeys.map(({ file, key }) => ({
      key,
      filename: file.name,
      species: '',
      description: '',
      progress: 0,
    }));

    setPersistentDataSource((prevData) => [...prevData, ...newData]);
  };

  const handleAddFile = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = '.h5ad';
    input.onchange = (e: any) => {
      const files = Array.from(e.target.files);
      addFilesToDataSource(files);
    };
    input.click();
  };

  const uploadFile = async (
    file: File,
    species: string,
    description: string,
    recordKey: string,
  ) => {
    setIsAnndataUploading((prev) => ({ ...prev, [recordKey]: true }));
    if (ServiceCloud == ServiceCloudSelection.AWS) {
      const { data: dataFrame } = await requestCreateDataFrame(
        UploadFromType.FROMUPLOADEDDIRECTLY,
        file.name,
        UploadType.ANNDATA,
        species,
        description,
      );
      const { data: uploadInfo }: any = await requestAnndataUploadInfo(dataFrame.id, file.size);

      setCurrentAnndataUploadIdRef((prev) => ({ ...prev, [recordKey]: uploadInfo.uploadId }));
      setObjectKey((prev) => ({ ...prev, [recordKey]: uploadInfo.object_key }));
      setIsMultipart((prev) => ({ ...prev, [recordKey]: uploadInfo.multipart }));
      try {
        if (uploadInfo.multipart) {
          await requestUploadToAWS(
            file,
            uploadInfo.partInfoList,
            uploadInfo.part_count,
            uploadInfo.part_size,
            uploadInfo.object_key,
            uploadInfo.uploadId,
            (progress: number) => {
              setAnndataUploadProgress((prev) => {
                return {
                  ...prev,
                  [recordKey]: Math.ceil(progress),
                };
              });
            },
          );
        } else {
          const abortController = new AbortController();
          setUploadingControllers((prev) => ({ ...prev, [recordKey]: abortController }));
          await uploadFileToAWS(
            file,
            uploadInfo.presigned_url,
            abortController,
            (progress: number) => {
              setAnndataUploadProgress((prev) => ({ ...prev, [recordKey]: Math.ceil(progress) }));
            },
          );
        }
        await requestCheckAnndataUpload(dataFrame.id);
        if (!!targetAnalysisId || targetAnalysisId + '' === '0') {
          await requestImportDatas(targetAnalysisId + '', [dataFrame.id]);
        }
        pushFile(file);
        message.success('Upload successfully.');
        setIsAnndataUploading((prev) => ({ ...prev, [recordKey]: false }));
        setIsAnndataUploadSuccess((prev) => ({ ...prev, [recordKey]: true }));
        setAnndataUploadProgress((prev) => ({ ...prev, [recordKey]: 0 }));
      } catch (err) {
        setAnndataUploadProgress((prev) => ({ ...prev, [recordKey]: 0 }));
        setIsAnndataUploading((prev) => ({ ...prev, [recordKey]: false }));
        return;
      }
    }
  };

  const handleUpload = async (record) => {
    try {
      await form.validateFields([`species-${record.key}`, `description-${record.key}`]);

      if (!record.species || !record.description) {
        message.error('Please fill in the species and description before uploading.');
        return;
      }

      await requestValidateUpdate(record.species, record.description);

      const fileObj = persistentSelectedFiles.find((f) => f.key === record.key);
      if (fileObj) {
        setAnndataUploadProgress((prev) => ({
          ...prev,
          [record.key]: 0,
        }));

        await uploadFile(fileObj.file, record.species, record.description, record.key);

        setPersistentDataSource((prevData) =>
          prevData.map((item) => {
            if (item.key === record.key) {
              return { ...item, progress: 100 };
            }
            return item;
          }),
        );
      } else {
        message.error('File not found. Please try adding the file again.');
      }
    } catch (error) {
      message.error('Validation failed. Please check the species and description fields.');
    }
  };

  const cancelUpload = async (recordKey) => {
    try {
      if (isMultipart[recordKey]) {
        try {
          await requestCancelUpload(currentAnndataUploadIdRef[recordKey], objectKey[recordKey]);
        } catch (err) {
          console.error('Failed to cancel multipart upload:', err);
        }
      } else {
        const abortController = uploadingControllers[recordKey];
        if (abortController) {
          abortController.abort();
        }
      }

      setAnndataUploadProgress((prev) => ({ ...prev, [recordKey]: 0 }));
      setIsAnndataUploading((prev) => ({ ...prev, [recordKey]: false }));
      setCurrentAnndataUploadIdRef((prev) => {
        const updatedUploadId = { ...prev };
        delete updatedUploadId[recordKey];
        return updatedUploadId;
      });
      setObjectKey((prev) => {
        const updatedObjectKey = { ...prev };
        delete updatedObjectKey[recordKey];
        return updatedObjectKey;
      });

      message.info(`Upload for ${recordKey} has been canceled.`);
    } catch (error) {
      console.error('Error while canceling upload:', error);
      message.error('An error occurred while canceling the upload.');
    }
  };

  const handleDelete = (record) => {
    setPersistentSelectedFiles((prevFiles) =>
      prevFiles.filter((fileObj) => fileObj.key !== record.key),
    );
    setPersistentDataSource((prevData) => prevData.filter((item) => item.key !== record.key));

    setAnndataUploadProgress((prev) => {
      const updatedProgress = { ...prev };
      delete updatedProgress[record.key];
      return updatedProgress;
    });
    setIsAnndataUploading((prev) => {
      const updatedUploading = { ...prev };
      delete updatedUploading[record.key];
      return updatedUploading;
    });
    setCurrentAnndataUploadIdRef((prev) => {
      const updatedUploadId = { ...prev };
      delete updatedUploadId[record.key];
      return updatedUploadId;
    });
    setObjectKey((prev) => {
      const updatedObjectKey = { ...prev };
      delete updatedObjectKey[record.key];
      return updatedObjectKey;
    });
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    addFilesToDataSource(files);
  };

  const handleSpeciesChange = (value, record) => {
    setPersistentDataSource((prevData) =>
      prevData.map((item) => {
        if (item.key === record.key) {
          return { ...item, species: value };
        }
        return item;
      }),
    );
  };

  const handleDescriptionChange = (value, record) => {
    setPersistentDataSource((prevData) =>
      prevData.map((item) => {
        if (item.key === record.key) {
          return { ...item, description: value };
        }
        return item;
      }),
    );
  };

  const handleFinish = () => {
    closeUploadDataUI();
  };

  const columns = [
    {
      title: 'Data File',
      dataIndex: 'filename',
      key: 'filename',
      width: '15%',
    },
    {
      title: (
        <span style={{ whiteSpace: 'nowrap' }}>
          <span className={styles.labelRequired}>*</span> Species
        </span>
      ),
      dataIndex: 'species',
      key: 'species',
      width: '30%',
      render: (_, record) => (
        <Select
          placeholder="Please select the species"
          value={record.species}
          style={{ width: 200 }}
          options={speciesOptions}
          onChange={(value) => handleSpeciesChange(value, record)}
        />
      ),
    },
    {
      title: (
        <span style={{ whiteSpace: 'nowrap' }}>
          <span className={styles.labelRequired}>*</span> Description
        </span>
      ),
      dataIndex: 'description',
      key: 'description',
      render: (_, record) =>
        editingKey === record.key ? (
          <Input
            placeholder="Enter description"
            value={record.description}
            onChange={(e) => handleDescriptionChange(e.target.value, record)}
            onBlur={() => handleSave()}
          />
        ) : (
          <div>
            {record.description}
            <EditOutlined
              onClick={() => handleEdit(record)}
              style={{ cursor: 'pointer', marginLeft: '8px' }}
            />
          </div>
        ),
    },
    {
      title: 'State',
      dataIndex: 'progress',
      key: 'progress',
      width: '20%',
      render: (_, record) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {isAnndataUploading[record.key] ? (
            <>
              <Progress
                percent={anndataUploadProgress[record.key] || 0}
                size="small"
                style={{ marginRight: '8px', width: '70%' }}
                status={anndataUploadProgress[record.key] === 100 ? 'success' : 'active'}
              />
              {anndataUploadProgress[record.key] !== 100 ? (
                <CloseOutlined onClick={() => cancelUpload(record.key)} />
              ) : null}
            </>
          ) : (
            <Popconfirm
              title="Are you sure you want to upload this file?"
              onConfirm={() => handleUpload(record)}
              okText="Yes"
              cancelText="No"
            >
              {isAnndataUploadSuccess[record.key] ? (
                <span style={{ color: '#2f54eb' }}>
                  Uploaded <CheckCircleTwoTone twoToneColor="#2f54eb" />
                </span>
              ) : (
                <button className={styles.uploadButton} disabled={isAnndataUploading[record.key]}>
                  Upload <UploadOutlined />
                </button>
              )}
            </Popconfirm>
          )}
        </div>
      ),
    },
    {
      title: (
        <button
          className={styles.addFilesButton}
          onClick={handleAddFile}
          disabled={analysisId ? analysisAccessType === AnalysisType.PUBLIC : isGuestUser}
          title={
            analysisId
              ? analysisAccessType === AnalysisType.PUBLIC
                ? 'Cannot upload data to public analysis'
                : ''
              : isGuestUser
              ? 'Guest users cannot upload data'
              : ''
          }
        >
          + Add
        </button>
      ),
      dataIndex: 'add',
      key: 'add',
      width: '10%',
      render: (_, record) => (
        <DeleteOutlined
          className={styles.deleteButton}
          onClick={() => handleDelete(record)}
          style={{ cursor: 'pointer', color: 'red' }}
          disabled={isAnndataUploading[record.key]}
        />
      ),
    },
  ];

  return (
    <div
      style={{
        height: 'calc(70vh - 32px)',
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div
          onDragOver={(e) => {
            if (!(analysisId ? analysisAccessType === AnalysisType.PUBLIC : isGuestUser)) {
              handleDragOver(e);
            } else {
              e.preventDefault();
            }
          }}
          onDragLeave={(e) => {
            if (!(analysisId ? analysisAccessType === AnalysisType.PUBLIC : isGuestUser)) {
              handleDragLeave(e);
            }
          }}
          onDrop={(e) => {
            if (!(analysisId ? analysisAccessType === AnalysisType.PUBLIC : isGuestUser)) {
              handleDrop(e);
            } else {
              e.preventDefault();
            }
          }}
          className={`${styles.tableContainer} ${isDragging ? styles.dragging : ''} ${
            (analysisId ? analysisAccessType === AnalysisType.PUBLIC : isGuestUser)
              ? styles.noDragging
              : ''
          }`}
        >
          <Table
            dataSource={persistentDataSource}
            columns={columns}
            className={styles.tableContainer}
            locale={{
              emptyText: (
                <>
                  Drag and drop files here or click the + Add button to upload files.
                  <br />
                  Support for .h5ad files.
                </>
              ),
            }}
          />
        </div>
        <div className={styles.moreInfoContainer}>
          <p className={styles.moreInfoText}>
            <span className={styles.labelRequired}>*</span> Accurate descriptions could enhance the
            precision of AI applications.
          </p>
        </div>
        <div className={styles.finishButtonContainer}>
          <div>
            <Button
              onClick={() => {
                handleFinish();
              }}
            >
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnndataUpload;
