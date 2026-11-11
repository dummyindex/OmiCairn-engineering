import { AnalysisType } from '@/constants/analysis';
import { UploadFromType, UploadType } from '@/constants/data';
import type { FileMap } from '@/interfaces/file';
import { requestImportDatas } from '@/request/analysis';
import { requestUploadToAWS, uploadFileToAWS } from '@/request/awsOperation';
import {
  requestAssembleDataComponent,
  requestCreateDataFrame,
  requestDataComponentUploadInfo,
} from '@/request/data';
import { flatFileMap } from '@/util/fileTool';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  FileOutlined,
  FolderOpenOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { Button, Form, message, Tag, Tree } from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';
import BasicDataInfoForm from './basicDataInform';

// Convert a FileMap into Tree data
const convertFileMapToTreeData = (
  fileMap: FileMap | null,
  processMap: Record<string, number>,
  fileStatusMap: Record<string, 'pending' | 'uploading' | 'success' | 'failed'>,
  keyPrefix: string = '',
  onRetry?: (fileKey: string) => void,
): any[] => {
  if (!fileMap) return [];

  return Object.keys(fileMap).map((key) => {
    const fileItem = fileMap[key];
    const fullKey = keyPrefix ? `${keyPrefix}/${key}` : key;
    const processKey = `s3-store/${fullKey}`;
    const progress = processMap[processKey];
    const status = fileStatusMap[processKey];

    if (fileItem.type === 'folder') {
      return {
        title: (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              width: '100%',
            }}
          >
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                overflow: 'hidden',
                minWidth: 0,
                flex: 1,
              }}
            >
              <FolderOpenOutlined style={{ marginRight: 8, color: '#1890ff', flexShrink: 0 }} />
              <span
                style={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  fontSize: '12px',
                }}
                title={key}
              >
                {key}
              </span>
            </span>
          </div>
        ),
        key: fullKey,
        children: convertFileMapToTreeData(
          fileItem.children,
          processMap,
          fileStatusMap,
          fullKey,
          onRetry,
        ),
      };
    } else {
      return {
        title: (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              width: '100%',
            }}
          >
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                overflow: 'hidden',
                minWidth: 0,
                flex: 1,
                marginRight: 8,
              }}
            >
              <FileOutlined style={{ marginRight: 8, color: '#666', flexShrink: 0 }} />
              <span
                style={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  fontSize: '12px',
                }}
                title={key}
              >
                {key}
              </span>
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}>
              {progress !== undefined && progress < 100 && status === 'uploading' && (
                <span style={{ fontSize: '12px', color: '#1890ff' }}>{progress}%</span>
              )}
              {status === 'success' && (
                <Tag
                  icon={<CheckCircleOutlined />}
                  color="success"
                  style={{ margin: 0, fontSize: '10px' }}
                >
                  Success
                </Tag>
              )}
              {status === 'failed' && (
                <>
                  <Tag
                    icon={<CloseCircleOutlined />}
                    color="error"
                    style={{ margin: 0, fontSize: '10px' }}
                  >
                    Failed
                  </Tag>
                  <Button
                    type="text"
                    size="small"
                    icon={<ReloadOutlined />}
                    style={{ padding: '0 4px', height: '20px', fontSize: '10px' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onRetry?.(processKey);
                    }}
                    title="Retry upload"
                  />
                </>
              )}
              {(status === 'pending' || !status) && (
                <Tag color="default" style={{ margin: 0, fontSize: '10px' }}>
                  Pending
                </Tag>
              )}
            </div>
          </div>
        ),
        key: fullKey,
        isLeaf: true,
      };
    }
  });
};

const GeneralUpload = () => {
  const { analysisAccessType } = useModel('analysis');
  const { targetAnalysisId, closeUploadDataUI } = useModel('uploadDataUI');
  const { isGuest } = useModel('user');

  const [form] = Form.useForm();
  const [fileMap, setFileMap] = useState<FileMap | null>(null);
  const [treeData, setTreeData] = useState<any[]>([]);
  const [processMap, setProcessMap] = useState<Record<string, number>>({});
  const [fileStatusMap, setFileStatusMap] = useState<
    Record<string, 'pending' | 'uploading' | 'success' | 'failed'>
  >({});
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState('');
  const [uploadComplete, setUploadComplete] = useState(false);
  const [currentDataFrameId, setCurrentDataFrameId] = useState<string | null>(null);

  const isGuestUser = isGuest();

  // Upload a single file
  const startUpload = async (componentKey: string, file: File, dataFrameIdParam: string) => {
    try {
      setFileStatusMap((prev) => ({ ...prev, [componentKey]: 'uploading' }));

      const controller = new AbortController();
      const { data: uploadInfo } = await requestDataComponentUploadInfo(
        dataFrameIdParam,
        componentKey,
        '',
        UploadType.GENERAL,
        file.size,
      );

      if (uploadInfo.multipart) {
        await requestUploadToAWS(
          file,
          uploadInfo.partInfoList,
          uploadInfo.part_count,
          uploadInfo.part_size,
          uploadInfo.object_key,
          uploadInfo.uploadId,
          (progress: number) => {
            setProcessMap((prev) => ({
              ...prev,
              [componentKey]: Math.round(progress),
            }));
          },
        );
      } else {
        await uploadFileToAWS(file, uploadInfo.presigned_url, controller, (progress: number) => {
          setProcessMap((prev) => ({
            ...prev,
            [componentKey]: Math.round(progress),
          }));
        });
      }

      setFileStatusMap((prev) => ({ ...prev, [componentKey]: 'success' }));
      setProcessMap((prev) => ({ ...prev, [componentKey]: 100 }));
    } catch (error) {
      console.error(`Upload failed for ${componentKey}:`, error);
      setFileStatusMap((prev) => ({ ...prev, [componentKey]: 'failed' }));
      throw error;
    }
  };

  // Retry uploading a single file
  const handleRetryFile = async (componentKey: string) => {
    if (!fileMap || !currentDataFrameId) {
      message.error('Cannot retry: No active upload session. Please restart the upload process.');
      return;
    }

    const flattenFm = flatFileMap(fileMap);
    const fileKey = componentKey.replace('s3-store/', '');
    const fileItem = flattenFm[fileKey];

    if (!fileItem || fileItem.type !== 'file') {
      message.error('File not found for retry');
      return;
    }

    message.info(`Retrying upload for ${fileItem.file?.name}...`);

    try {
      // Reset the file status
      setFileStatusMap((prev) => ({ ...prev, [componentKey]: 'uploading' }));
      setProcessMap((prev) => ({ ...prev, [componentKey]: 0 }));

      // Retry the upload using the current dataFrameId
      await startUpload(componentKey, fileItem.file as File, currentDataFrameId);
      message.success(`Successfully retried upload for ${fileItem.file?.name}`);
    } catch (error) {
      console.error('Retry failed:', error);
      setFileStatusMap((prev) => ({ ...prev, [componentKey]: 'failed' }));
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      message.error(`Retry failed for ${fileItem.file?.name}: ${errorMessage}`);
    }
  };

  // Update the tree structure
  useEffect(() => {
    const newTreeData = convertFileMapToTreeData(
      fileMap,
      processMap,
      fileStatusMap,
      '',
      handleRetryFile,
    );
    setTreeData(newTreeData);
  }, [fileMap, processMap, fileStatusMap]);

  // Helper to clear all state
  const clearAllState = () => {
    setFileMap(null);
    setTreeData([]);
    setProcessMap({});
    setFileStatusMap({});
    setCurrentStep('');
    setUploadComplete(false);
    setCurrentDataFrameId(null);
  };

  // Handle folder upload
  const handleFolderUpload = (fileList: any[]) => {
    if (!fileList || fileList.length === 0) {
      clearAllState();
      setCurrentStep('No files selected');
      return;
    }

    // Clear previous state but keep the in-progress state
    setProcessMap({});
    setFileStatusMap({});
    setUploadComplete(false);
    setCurrentStep('Processing files...');

    // Build the file map
    const newFileMap: FileMap = {};
    let countedFiles = 0;
    let skippedFiles = 0;

    fileList.forEach((file, index) => {
      if (!file) {
        console.warn(`File at index ${index} is null or undefined`);
        skippedFiles++;
        return;
      }

      // Safely get the file path (compatible across browsers and platforms)
      let filePath = '';
      if ((file as any).webkitRelativePath) {
        filePath = (file as any).webkitRelativePath as string;
      } else if (file.name) {
        // If there is no webkitRelativePath, use the file name (single-file case)
        filePath = file.name;
      } else {
        console.warn(`File at index ${index} has no path or name`);
        skippedFiles++;
        return;
      }

      const pathParts = filePath.split(/[\\/]/).filter((part) => part.length > 0);

      // If there is no valid path, skip it
      if (pathParts.length === 0) {
        console.warn(`File ${filePath} has no valid path parts`);
        skippedFiles++;
        return;
      }

      let currentLevel = newFileMap;

      // Build the folder structure
      for (let i = 0; i < pathParts.length - 1; i++) {
        const folderName = pathParts[i];
        if (!currentLevel[folderName]) {
          currentLevel[folderName] = {
            type: 'folder',
            file: null,
            children: {},
          };
        }
        currentLevel = currentLevel[folderName].children!;
      }

      // Add the file
      const fileName = pathParts[pathParts.length - 1];
      currentLevel[fileName] = {
        type: 'file',
        file: file,
        children: null,
      };
      countedFiles += 1;
    });

    setFileMap(newFileMap);
    setCurrentStep(`Selected ${countedFiles} files`);

    if (countedFiles === 0) {
      if (skippedFiles > 0) {
        message.warning(
          `No valid files recognized (skipped ${skippedFiles} files). Please ensure the selected folder contains valid files.`,
        );
      } else {
        message.warning('No valid files recognized. Please select a different folder.');
      }
    } else {
      message.success(`Successfully recognized ${countedFiles} files`);
    }
  };

  // Upload all files
  const uploadAllFiles = async (dataFrameIdParam: string) => {
    if (!fileMap) return;

    setCurrentStep('Preparing file upload...');
    const flattenFm = flatFileMap(fileMap);
    const fileKeys = Object.keys(flattenFm).filter((key) => flattenFm[key].type === 'file');

    if (fileKeys.length === 0) {
      console.warn('No files to upload');
      return;
    }

    // Initialize all file statuses to pending
    const initialStatusMap: Record<string, 'pending' | 'uploading' | 'success' | 'failed'> = {};
    fileKeys.forEach((key) => {
      const componentKey = `s3-store/${key}`;
      initialStatusMap[componentKey] = 'pending';
    });
    setFileStatusMap(initialStatusMap);

    setCurrentStep(`Uploading files (0/${fileKeys.length})`);

    // Upload files concurrently (with a concurrency limit)
    const concurrentLimit = 3;
    let completedCount = 0;
    const failedFiles: string[] = [];

    const uploadPromises = fileKeys.map(async (key) => {
      const fileItem = flattenFm[key];
      const componentKey = `s3-store/${key}`;

      try {
        await startUpload(componentKey, fileItem.file as File, dataFrameIdParam);
        completedCount++;
        setCurrentStep(`Uploading files (${completedCount}/${fileKeys.length})`);
      } catch (error) {
        failedFiles.push(key);
        console.error(`File ${key} upload failed:`, error);
      }
    });

    // Run uploads in batches
    for (let i = 0; i < uploadPromises.length; i += concurrentLimit) {
      const batch = uploadPromises.slice(i, i + concurrentLimit);
      await Promise.all(batch);
    }

    // Check for any failed files
    if (failedFiles.length > 0) {
      throw new Error(
        `${failedFiles.length} file(s) failed to upload. Check individual file status and retry if needed.`,
      );
    }
  };

  // Handle submit
  const handleSubmit = async () => {
    try {
      setLoading(true);
      setCurrentStep('Validating form...');

      // Validate the form
      const values = await form.validateFields();

      if (!fileMap || Object.keys(fileMap).length === 0) {
        message.error('Please upload a folder first');
        return;
      }

      // Create the data frame
      setCurrentStep('Creating data frame...');
      const { data: dataFrame } = await requestCreateDataFrame(
        UploadFromType.FROMUPLOADEDDIRECTLY,
        values.name,
        UploadType.GENERAL,
        values.species,
        values.description,
      );

      setCurrentDataFrameId(dataFrame.id);

      // Upload files
      await uploadAllFiles(dataFrame.id);

      setCurrentStep('Assembling data...');
      await requestAssembleDataComponent(dataFrame.id);

      // Import into the analysis
      if (targetAnalysisId !== null) {
        setCurrentStep('Importing to analysis...');
        await requestImportDatas(targetAnalysisId, [dataFrame.id]);
      }

      setCurrentStep('Upload completed!');
      setUploadComplete(true);
      message.success('Data uploaded and assembled successfully!');
    } catch (error) {
      console.error('Submit failed:', error);
      const errorMessage =
        error instanceof Error ? error.message : 'Upload failed, please try again';
      message.error(errorMessage);
      setCurrentStep('Upload failed');
    } finally {
      setLoading(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    clearAllState();
    form.resetFields();
    closeUploadDataUI();
  };

  return (
    <div
      style={{
        padding: '16px 24px 24px 24px',
        minHeight: '60vh',
        maxHeight: '85vh',
        display: 'flex',
        overflow: 'hidden',
        flexDirection: 'column',
      }}
    >
      <h3
        style={{
          marginBottom: '20px',
          fontSize: '18px',
          fontWeight: 600,
        }}
      >
        General Data Upload
      </h3>

      <div
        style={{
          flex: 1,
          display: 'flex',
          gap: '20px',
          flexDirection: 'row',
          minHeight: 0,
        }}
        className="upload-container"
      >
        {/* Left form area */}
        <div
          style={{
            flex: '1 1 auto',
            minWidth: '500px',
            maxWidth: '65%',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'auto',
            paddingRight: '8px',
          }}
          className="form-section"
        >
          {/* Basic info form */}
          <div style={{ flexShrink: 0 }}>
            <BasicDataInfoForm form={form} showName />
          </div>

          {/* File upload area */}
          <Form.Item
            label="Upload Folder"
            style={{
              marginTop: '16px',
              marginBottom: '16px',
              flexShrink: 0,
            }}
          >
            <div
              style={{
                minHeight: '120px',
                maxHeight: '200px',
                border: '2px dashed #d9d9d9',
                borderRadius: '6px',
                padding: '16px',
                textAlign: 'center',
                cursor:
                  isGuestUser || analysisAccessType === AnalysisType.PUBLIC || loading
                    ? 'not-allowed'
                    : 'pointer',
                backgroundColor:
                  isGuestUser || analysisAccessType === AnalysisType.PUBLIC || loading
                    ? '#f5f5f5'
                    : '#fafafa',
                transition: 'border-color 0.3s',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
              }}
              onClick={() => {
                if (!isGuestUser && analysisAccessType !== AnalysisType.PUBLIC && !loading) {
                  const input = document.createElement('input');
                  input.type = 'file';
                  input.webkitdirectory = true;
                  input.multiple = true;
                  input.onchange = (e: any) => {
                    const files = Array.from(e.target.files || []);
                    if (files.length > 0) {
                      clearAllState();
                      handleFolderUpload(files);
                    }
                  };
                  input.click();
                }
              }}
            >
              <FolderOpenOutlined
                style={{
                  fontSize: '40px',
                  color: '#1890ff',
                  marginBottom: '8px',
                }}
              />
              <p
                style={{
                  margin: '8px 0 4px 0',
                  fontSize: '15px',
                  color: '#000',
                  fontWeight: 500,
                }}
              >
                Click to select folder
              </p>
              <p
                style={{
                  margin: '0 0 8px 0',
                  fontSize: '13px',
                  color: '#666',
                  lineHeight: 1.4,
                }}
              >
                Select a folder to upload all files
              </p>
              {currentStep && (
                <p
                  style={{
                    color: '#1890ff',
                    fontSize: '12px',
                    margin: '4px 0 0 0',
                    fontWeight: 500,
                  }}
                >
                  {currentStep}
                </p>
              )}
            </div>
          </Form.Item>

          {/* Bottom button area */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              alignItems: 'center',
              paddingTop: '16px',
              gap: '12px',
              flexShrink: 0,
              borderTop: '1px solid #f0f0f0',
              marginTop: '16px',
            }}
          >
            <Button onClick={handleCancel} disabled={loading}>
              Cancel
            </Button>
            <Button
              type="primary"
              onClick={handleSubmit}
              loading={loading}
              disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC || uploadComplete}
            >
              {uploadComplete ? 'Upload Complete' : 'Submit'}
            </Button>
          </div>
        </div>

        {/* Right tree-structure area */}
        <div
          style={{
            flex: '0 0 auto',
            minWidth: '300px',
            width: '35%',
            maxWidth: '450px',
            border: '1px solid #d9d9d9',
            borderRadius: '6px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            backgroundColor: '#fafafa',
          }}
          className="tree-section"
        >
          <h4
            style={{
              marginBottom: '12px',
              fontSize: '14px',
              fontWeight: 600,
              margin: '0 0 12px 0',
              color: '#262626',
            }}
          >
            File Structure
            {fileMap &&
              (() => {
                const flattenFm = flatFileMap(fileMap);
                const fileKeys = Object.keys(flattenFm).filter(
                  (key) => flattenFm[key].type === 'file',
                );
                const totalFiles = fileKeys.length;
                const successCount = fileKeys.filter(
                  (key) => fileStatusMap[`s3-store/${key}`] === 'success',
                ).length;
                const failedCount = fileKeys.filter(
                  (key) => fileStatusMap[`s3-store/${key}`] === 'failed',
                ).length;
                const uploadingCount = fileKeys.filter(
                  (key) => fileStatusMap[`s3-store/${key}`] === 'uploading',
                ).length;

                if (totalFiles > 0) {
                  return (
                    <div
                      style={{
                        fontSize: '12px',
                        fontWeight: 'normal',
                        color: '#666',
                        marginTop: '4px',
                      }}
                    >
                      <div style={{ marginBottom: '4px' }}>Total: {totalFiles} files</div>
                      {(successCount > 0 || failedCount > 0 || uploadingCount > 0) && (
                        <div
                          style={{
                            display: 'flex',
                            gap: '8px',
                            flexWrap: 'wrap',
                            alignItems: 'center',
                          }}
                        >
                          {successCount > 0 && (
                            <span style={{ color: '#52c41a', fontSize: '11px' }}>
                              ✓ {successCount} success
                            </span>
                          )}
                          {failedCount > 0 && (
                            <span style={{ color: '#ff4d4f', fontSize: '11px' }}>
                              ✗ {failedCount} failed
                            </span>
                          )}
                          {uploadingCount > 0 && (
                            <span style={{ color: '#1890ff', fontSize: '11px' }}>
                              ↑ {uploadingCount} uploading
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              })()}
          </h4>
          <div
            style={{
              flex: 1,
              overflow: 'auto',
              minHeight: 0,
              backgroundColor: '#fff',
              borderRadius: '4px',
              padding: '8px',
            }}
          >
            {treeData.length > 0 ? (
              <Tree
                showLine
                defaultExpandAll
                treeData={treeData}
                style={{ fontSize: '12px' }}
                height={300}
              />
            ) : (
              <div
                style={{
                  textAlign: 'center',
                  color: '#999',
                  paddingTop: '40px',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                }}
              >
                <FolderOpenOutlined
                  style={{
                    fontSize: '28px',
                    marginBottom: '12px',
                    opacity: 0.6,
                  }}
                />
                <div style={{ fontSize: '12px' }}>No files selected</div>
              </div>
            )}
          </div>
          {/* Status info */}
          {currentStep && (
            <div
              style={{
                marginTop: '12px',
                padding: '8px 12px',
                backgroundColor: '#e6f7ff',
                borderRadius: '4px',
                fontSize: '12px',
                color: '#1890ff',
                borderLeft: '3px solid #1890ff',
                flexShrink: 0,
              }}
            >
              <strong>Status:</strong> {currentStep}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GeneralUpload;
