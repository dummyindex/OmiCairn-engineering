import FileInput from '@/components/common/fileInput';
import type { FileMap } from '@/interfaces/file';
import { uploadFileToS3 } from '@/request/awsOperation';
import { requestDownloadParamFile, requestUploadParamFile } from '@/request/node';
import { CloudDownloadOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { useState, useEffect } from 'react';
import { Progress, Button } from 'antd';

// After upload, pass onChange(filename) to the parent

const ParamFileInput = (props: any) => {
  const { value, onChange, filename, nodeId } = props;
  const [presignedUrl, setPresignedUrl] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);

  const loadPresignedUrl = async () => {
    if (!filename || !nodeId) return;
    const { data: url } = await requestDownloadParamFile(nodeId, filename);
    setPresignedUrl(url);
  };

  useEffect(() => {
    loadPresignedUrl();
  }, [filename, nodeId, value]);

  const startUpload = async (file: File) => {
    const { data: uploadInfo } = await requestUploadParamFile(nodeId, filename, file.size);
    await uploadFileToS3(file, uploadInfo, (progress: number) => {
      setUploadProgress(Math.ceil(progress));
    });
    setUploadProgress(null);
    onChange(filename);
  };

  const onFileInput = (fm: FileMap) => {
    const firstLevelKeys = Object.keys(fm);
    const fileKeys = firstLevelKeys.filter((key) => fm[key].type === 'file');
    if (fileKeys.length === 0) return;
    const fileKey = fileKeys[0];
    const file = fm[fileKey].file;
    startUpload(file);
  };

  const removeFile = async () => {
    // await requestDeleteParamFile(nodeId, filename);
    onChange(null);
  };

  return (
    <div>
      {!value && (
        <div>
          <FileInput
            triggers={['click', 'drop']}
            onChange={(fm: FileMap) => {
              onFileInput(fm);
            }}
            innerRender={() => {
              return (
                <div
                  style={{
                    width: '100%',
                    height: '5vh',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    backgroundColor: 'white',
                    fontSize: '0.8em',
                  }}
                >
                  {uploadProgress !== null && (
                    <Progress
                      style={{
                        width: '90%',
                      }}
                      percent={uploadProgress}
                      size="small"
                    />
                  )}
                  {uploadProgress === null && (
                    <span>
                      <PlusOutlined
                        style={{
                          fontSize: '1em',
                          color: '#1890ff',
                        }}
                      />
                      <span
                        style={{
                          paddingLeft: '1em',
                          color: '#999',
                        }}
                      >
                        Drop file here or click to upload
                      </span>
                    </span>
                  )}
                </div>
              );
            }}
          />
        </div>
      )}
      {value && (
        <div
          style={{
            width: '100%',
            height: '5vh',
            display: 'flex',
            justifyContent: 'flex-start',
            alignItems: 'center',
            backgroundColor: 'white',
            border: '1px dashed #1890ff',
            // gap: '0.5em',
            padding: '0 1em 0 1em',
          }}
        >
          <Button type="link" href={presignedUrl}>
            {value}
          </Button>
          <div
            style={{
              flex: 1,
            }}
          />
          <Button type="text" icon={<CloudDownloadOutlined />} href={presignedUrl} />
          <Button type="text" danger icon={<DeleteOutlined />} onClick={removeFile} />
        </div>
      )}
    </div>
  );
};

export default ParamFileInput;
