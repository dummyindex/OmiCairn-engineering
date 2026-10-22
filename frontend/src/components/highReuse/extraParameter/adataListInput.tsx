import { DataListFetchMode } from '@/constants/data';
import { requestUploadToAWS, uploadFileToAWS } from '@/request/awsOperation';
import { requestDataInfo, requestDataSourceList } from '@/request/data';
import {
  requestCreateParamFile,
  requestListParamFilesBySuffixes,
  requestParamFileInfo,
} from '@/request/paramFile';
import {
  DatabaseOutlined,
  DeleteOutlined,
  FileOutlined,
  InboxOutlined,
  PlusOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { Select, message, Button, Modal, Upload } from 'antd';
import { useEffect, useState } from 'react';
const { Dragger } = Upload;

const DELIMITER = '--|--';

interface AdataItem {
  source: string;
  ident: string;
  name: string;
}

interface SelectedFileItem {
  source: string;
  ident: string;
  name: string;
  type: string;
}

const AdataListInput = (props: any) => {
  const { value, onChange } = props;
  const [dataSourceOptions, setDataSourceOptions] = useState<any[]>([]);
  const [paramFileOptions, setParamFileOptions] = useState<any[]>([]);

  const [addFromExistsModalVisible, setAddFromExistsModalVisible] = useState(false);
  const [selectedNewExistsOption, setSelectedNewExistsOption] = useState<AdataItem | null>(null);

  const [uploadNewFileModalVisible, setUploadNewFileModalVisible] = useState(false);
  const [newUploadFileItem, setNewUploadFileItem] = useState<any>(null);

  const [fileList, setFileList] = useState<(SelectedFileItem | null)[]>([]);

  const loadDataSourceOptions = async () => {
    const { data: dataSourceOptions } = await requestDataSourceList(
      DataListFetchMode.UPLOADED,
      null,
      null,
    );
    setDataSourceOptions(dataSourceOptions);
  };

  const loadParamFileOptions = async () => {
    const { data: paramFileOptions } = await requestListParamFilesBySuffixes(['h5ad', 'loom']);
    console.log('paramFileOptions', paramFileOptions);
    setParamFileOptions(paramFileOptions);
  };

  useEffect(() => {
    loadDataSourceOptions();
    loadParamFileOptions();
  }, []);

  const loadFileList = async () => {
    if (!value || value.length === 0) {
      setFileList([]);
      return;
    }
    const res = await Promise.all(
      value.map(async (adataItem: AdataItem) => {
        const { source, ident } = adataItem;
        if (source === 'data-source') {
          const { data: dataSourceInfo } = await requestDataInfo(ident);
          return {
            source: 'data-source',
            ident,
            name: dataSourceInfo.name,
            type: 'adata',
          };
        } else if (source === 'param-file') {
          const { data: paramFileInfo } = await requestParamFileInfo(ident);
          return {
            source: 'param-file',
            ident,
            name: paramFileInfo.name,
            type: 'param-file',
          };
        } else {
          return null;
        }
      }),
    );
    setFileList(res);
  };

  const removeFile = async (fileItem: { source: string; ident: string }) => {
    const { source, ident } = fileItem;
    const newFileList = value.filter((adataItem: AdataItem) => {
      return adataItem.source !== source || adataItem.ident !== ident;
    });
    onChange(newFileList);
  };

  const customUploadParamFile = async (info: any) => {
    const { file, onError, onProgress, onSuccess } = info;

    try {
      const requestCreateResponse = await requestCreateParamFile({
        name: file.name,
        size: file.size,
      });
      const {
        data: { presignedPost: uploadInfo, paramFile },
      } = requestCreateResponse;
      console.log('paramFile', paramFile);
      if (uploadInfo.multipart) {
        await requestUploadToAWS(
          file,
          uploadInfo.partInfoList,
          uploadInfo.part_count,
          uploadInfo.part_size,
          uploadInfo.object_key,
          uploadInfo.uploadId,
          (progress: number) => {
            onProgress({ percent: progress });
          },
        );
      } else {
        // Create a shared AbortController
        const abortController = new AbortController();
        await uploadFileToAWS(
          file,
          uploadInfo.presigned_url,
          abortController,
          (progress: number) => {
            onProgress({ percent: progress });
          },
        );
      }
      setNewUploadFileItem(paramFile);
      onSuccess('ok', file);
    } catch (e) {
      onError(e);
      return;
    }
  };
  useEffect(() => {
    loadFileList();
  }, [value]);

  return (
    <div
      style={{
        width: '100%',
      }}
    >
      {fileList.map((fileItem: SelectedFileItem | null) => {
        if (!fileItem) {
          return null;
        }
        let icon: any = null;
        if (fileItem.source === 'data-source') {
          icon = <DatabaseOutlined />;
        } else if (fileItem.source === 'param-file') {
          icon = <FileOutlined />;
        }
        return (
          <div
            key={`${fileItem.source}-${fileItem.ident}`}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '5px',
            }}
          >
            <div>
              {icon} <span>{fileItem.name}</span>
            </div>
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => removeFile(fileItem)}
            />
          </div>
        );
      })}
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-start',
          alignItems: 'center',
          marginTop: '5px',
          gap: '5px',
        }}
      >
        <Button
          type="primary"
          size="small"
          icon={<PlusOutlined />}
          onClick={() => setAddFromExistsModalVisible(true)}
        >
          Add from existing sources
        </Button>
        <Button
          type="primary"
          size="small"
          icon={<UploadOutlined />}
          onClick={() => setUploadNewFileModalVisible(true)}
        >
          Upload new file
        </Button>
      </div>
      <Modal
        open={addFromExistsModalVisible}
        onCancel={() => {
          setSelectedNewExistsOption(null);
          setAddFromExistsModalVisible(false);
        }}
        onOk={() => {
          if (!selectedNewExistsOption) {
            message.error('Please select a data source or param file');
            return;
          }
          const { source, ident, name } = selectedNewExistsOption;
          const newFileList = value.concat([{ source, ident, name }]);
          onChange(newFileList);
          setAddFromExistsModalVisible(false);
        }}
        okText="Add"
        title="Add From Existing Sources"
        centered
      >
        <Select
          style={{ width: '100%' }}
          placeholder="Please select data source or param file"
          onChange={(value: string) => {
            const fruits = value.split(DELIMITER);
            const [source, ident, name] = fruits;
            setSelectedNewExistsOption({ source, ident, name });
          }}
          options={[
            {
              title: 'Param File',
              label: 'Param File',
              options: paramFileOptions.map((paramFileOption: any) => {
                return {
                  label: paramFileOption.name,
                  value: `param-file${DELIMITER}${paramFileOption.uuid}${DELIMITER}${paramFileOption.name}`,
                };
              }),
            },
            {
              title: 'Data Source',
              label: 'Data Source',
              options: dataSourceOptions.map((dataSourceOption: any) => {
                const alternateName = dataSourceOption.id + '.h5ad';
                return {
                  label: dataSourceOption.name || alternateName,
                  value: `data-source${DELIMITER}${dataSourceOption.id}${DELIMITER}${alternateName}`,
                };
              }),
            },
          ]}
        />
      </Modal>
      <Modal
        open={uploadNewFileModalVisible}
        onOk={() => {
          if (!newUploadFileItem) {
            message.error('Please select a data source or param file');
            return;
          }
          const { uuid, name } = newUploadFileItem;
          const newFileList = value.concat([{ source: 'param-file', ident: uuid, name }]);
          onChange(newFileList);
          setUploadNewFileModalVisible(false);
        }}
        okText="Add"
        okButtonProps={{
          disabled: !newUploadFileItem,
        }}
        onCancel={() => setUploadNewFileModalVisible(false)}
        cancelButtonProps={{ style: { display: 'none' } }}
        title="Upload New File"
        centered
      >
        <Dragger
          accept=".h5ad,.loom"
          name="file"
          multiple={false}
          maxCount={1}
          customRequest={customUploadParamFile}
          onChange={(info) => {
            console.log(info);
            const { status } = info.file;
            if (status !== 'uploading') {
              // console.log(info.file, info.fileList);
            }
            if (status === 'done') {
              message.success(`${info.file.name} file uploaded successfully.`);
            } else if (status === 'error') {
              message.error(`${info.file.name} file upload failed.`);
            }
          }}
          onDrop={(e) => {
            console.log('Dropped files', e.dataTransfer.files);
          }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">Click or drag h5ad or loom file to this area to upload</p>
        </Dragger>
      </Modal>
    </div>
  );
};

export default AdataListInput;
