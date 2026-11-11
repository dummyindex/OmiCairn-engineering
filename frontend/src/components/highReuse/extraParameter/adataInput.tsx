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

const AdataInput = (props: any) => {
  const { value, onChange } = props;
  const [dataSourceOptions, setDataSourceOptions] = useState<any[]>([]);
  const [paramFileOptions, setParamFileOptions] = useState<any[]>([]);

  const [addFromExistsModalVisible, setSelectFromExistsModalVisible] = useState(false);
  const [selectedNewExistsOption, setSelectedNewExistsOption] = useState<AdataItem | null>(null);

  const [uploadNewFileModalVisible, setUploadNewFileModalVisible] = useState(false);
  const [newUploadFileItem, setNewUploadFileItem] = useState<any>(null);

  const [file, setFile] = useState<SelectedFileItem | null>(null);

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

  const loadFile = async () => {
    if (!value) {
      setFile(null);
      return;
    }
    const { source, ident } = value;
    let fileInfo: SelectedFileItem | null = null;
    if (source === 'data-source') {
      const { data: dataSourceInfo } = await requestDataInfo(ident);
      fileInfo = {
        source: 'data-source',
        ident,
        name: dataSourceInfo.name,
        type: 'adata',
      };
    } else if (source === 'param-file') {
      const { data: paramFileInfo } = await requestParamFileInfo(ident);
      fileInfo = {
        source: 'param-file',
        ident,
        name: paramFileInfo.name,
        type: 'param-file',
      };
    } else {
      return null;
    }
    setFile(fileInfo);
  };

  const removeFile = async () => {
    onChange(null);
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
    loadFile();
  }, [value]);

  const icon = file?.source === 'data-source' ? <DatabaseOutlined /> : <FileOutlined />;

  return (
    <div
      style={{
        width: '100%',
      }}
    >
      {!!file && (
        <div
          key={`${file.source}-${file.ident}`}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '5px',
          }}
        >
          <div>
            {icon} <span>{file.name}</span>
          </div>
          <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={removeFile} />
        </div>
      )}
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
          onClick={() => setSelectFromExistsModalVisible(true)}
        >
          Select From Exists Options
        </Button>
        <Button
          type="primary"
          size="small"
          icon={<UploadOutlined />}
          onClick={() => setUploadNewFileModalVisible(true)}
        >
          Upload New File
        </Button>
      </div>
      <Modal
        open={addFromExistsModalVisible}
        onCancel={() => {
          setSelectedNewExistsOption(null);
          setSelectFromExistsModalVisible(false);
        }}
        onOk={() => {
          if (!selectedNewExistsOption) {
            message.error('Please select a data source or param file');
            return;
          }
          const { source, ident, name } = selectedNewExistsOption;
          onChange({ source, ident, name });
          setSelectFromExistsModalVisible(false);
        }}
        okText="Confirm"
        title="Select From Exists Options"
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
          onChange({ source: 'param-file', ident: uuid, name });
          setUploadNewFileModalVisible(false);
        }}
        okText="Use it"
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

export default AdataInput;
