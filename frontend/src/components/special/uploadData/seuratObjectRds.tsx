import { ServiceCloud } from '@/constants';
import { UploadFromType, UploadType } from '@/constants/data';
import { ServiceCloudSelection } from '@/constants/serviceCloudSelection';
import { requestImportDatas } from '@/request/analysis';
import {
  requestAssembleDataComponent,
  requestCreateDataFrame,
  requestDataComponentUploadInfo,
  requestValidateUpdate,
} from '@/request/data';
import { CloudUploadOutlined } from '@ant-design/icons';
import { Button, Form, Layout, message, Progress, Upload } from 'antd';
import React from 'react';
import { useModel } from 'umi';
import BasicDataInfoForm from './basicDataInform';
import { uploadFileToAWS, requestUploadToAWS } from '@/request/awsOperation';
import { AnalysisType } from '@/constants/analysis';

interface ComponentBlockProps {
  disabled?: boolean;
  dataId?: string | null;
  species?: string | null;
  description?: string | null;
  name?: string | null;
  setDataId: (dataId: string) => void;
  setGlobalDisabled: (disabled: boolean) => void;
  setIsSeuratObjectRdsUploaded: (uploaded: boolean) => void;
}

const ComponentBlock = (props: ComponentBlockProps) => {
  const {
    disabled,
    dataId,
    setDataId,
    setGlobalDisabled,
    species,
    description,
    name,
    setIsSeuratObjectRdsUploaded,
  } = props;
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadProgress, setUploadProgress] = React.useState(0);
  const [fileList, setFileList] = React.useState<File[]>([]);

  const uploadComponent = async (file: File) => {
    if (!species) {
      throw Error('species is null');
    }
    let _dataId = dataId;
    if (_dataId === null || _dataId === undefined) {
      setGlobalDisabled(true);
      const tempName = name || `${species}__${new Date().getTime()}`;
      try {
        const { data: dataFrame } = await requestCreateDataFrame(
          UploadFromType.FROMASSEMBLED,
          tempName,
          UploadType.SEURAT_OBJECT_RDS,
          species,
          description,
        );
        _dataId = dataFrame.id;
        setDataId(dataFrame.id);
      } catch (e) {
        console.error(e);
        return;
      }
      setGlobalDisabled(false);
    }
    setIsUploading(true);
    if (ServiceCloud == ServiceCloudSelection.AWS) {
      const fileSuffix = file.name.substring(file.name.lastIndexOf('.') + 1);
      const { data: uploadInfo } = await requestDataComponentUploadInfo(
        _dataId as string,
        'raw',
        fileSuffix,
        UploadType.SEURAT_OBJECT_RDS,
        file.size,
      );
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
              setUploadProgress(Math.ceil(progress));
            },
          );
        } else {
          await uploadFileToAWS(file, uploadInfo.presigned_url, null, (progress: number) => {
            setUploadProgress(Math.ceil(progress));
          });
        }
        setIsUploading(false);
        setIsSeuratObjectRdsUploaded(true);
      } catch (err) {
        console.log('err', err);
      }
    }
  };

  const onChange = async (info: any) => {
    const { file } = info;
    await uploadComponent(file);
    setFileList([file]);
  };

  return (
    <Upload.Dragger
      disabled={disabled}
      name="file"
      multiple={false}
      maxCount={1}
      onChange={onChange}
      beforeUpload={() => false}
      fileList={fileList}
      style={{
        backgroundColor: '#fff',
      }}
      accept={'.rds'}
    >
      <div
        style={{
          fontSize: 40,
        }}
      >
        <CloudUploadOutlined />
      </div>
      <div>
        <p style={{ marginTop: 8 }}>Click or drag file to this area to upload</p>
      </div>
      {/* <p className="ant-upload-text">
        {isSeuratObjectRdsUploaded && (
          <CheckCircleFilled
            style={{
              color: '#52c41a',
              marginLeft: 5,
            }}
          />
        )}
      </p> */}
      {isUploading && (
        <Progress
          style={{
            width: '90%',
          }}
          percent={uploadProgress}
        />
      )}
    </Upload.Dragger>
  );
};

const SeuratObjectRdsUpload = () => {
  const [form] = Form.useForm();

  const {
    targetAnalysisId,
    closeUploadDataUI,
    seuratObjectRdsShowPage,
    setSeuratObjectRdsShowPage,
    setIsSeuratObjectRdsUploaded,
    dataId,
    setDataId,
  } = useModel('uploadDataUI');

  const { dictionary } = useModel('localization');
  const { isGuest } = useModel('user');
  const { analysisAccessType } = useModel('analysis');
  const isGuestUser = isGuest();

  const [species, setSpecies] = React.useState<string>('');
  const [description, setDescription] = React.useState<string>('');
  const [name, setName] = React.useState<string>('');

  const [disabled, setDisabled] = React.useState(false);

  const [preprocessing, setPreprocessing] = React.useState(false);

  const assembleData = async () => {
    if (dataId === null) {
      message.error('Please upload rds');
      return;
    }
    setPreprocessing(true);
    try {
      await requestAssembleDataComponent(dataId);
      if (targetAnalysisId !== null) {
        await requestImportDatas(targetAnalysisId, [dataId]);
      }
      message.success('Dispatch Data Preprocessing successfully');
    } catch (e: any) {
      message.error(e.message);
    }
    setPreprocessing(false);
    closeUploadDataUI();
  };

  return (
    <Layout>
      {!seuratObjectRdsShowPage && (
        <Layout.Content
          style={{
            padding: '2rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'stretch',
            maxHeight: '60vh',
            overflow: 'auto',
          }}
        >
          {' '}
          <h3>Seurat Object RDS</h3>
          <BasicDataInfoForm form={form} showName={true} />
        </Layout.Content>
      )}
      {seuratObjectRdsShowPage && (
        <Layout.Content
          style={{
            padding: '2rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'stretch',
            maxHeight: '60vh',
            overflow: 'auto',
          }}
        >
          <h3>Seurat Object RDS</h3>
          <ComponentBlock
            dataId={dataId}
            description={description}
            disabled={disabled || !species}
            species={species}
            name={name}
            setDataId={setDataId}
            setGlobalDisabled={setDisabled}
            setIsSeuratObjectRdsUploaded={setIsSeuratObjectRdsUploaded}
          />

          <div
            hidden={!!species}
            style={{
              color: '#ff4d4f',
              textAlign: 'center',
              paddingTop: '2rem',
            }}
          >
            Please select a species first.
          </div>
        </Layout.Content>
      )}

      <Layout.Footer
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        {seuratObjectRdsShowPage && (
          <Button
            // type="primary"
            style={{ color: '#2949B0', border: '1px solid #5B74C3', marginRight: '1rem' }}
            onClick={() => {
              setSeuratObjectRdsShowPage(false);
            }}
            size="large"
          >
            {dictionary.PREVIOUS}
          </Button>
        )}
        {seuratObjectRdsShowPage && (
          <Button
            type="primary"
            size="large"
            onClick={assembleData}
            disabled={disabled || !species || dataId === null}
            loading={preprocessing}
          >
            {dictionary.ASSEMBLE}
          </Button>
        )}
        <div
          style={{
            width: '1rem',
          }}
        />
        {seuratObjectRdsShowPage && (
          <Button
            // type="primary"
            onClick={closeUploadDataUI}
            size="large"
          >
            {dictionary.FINISH}
          </Button>
        )}
        {!seuratObjectRdsShowPage && (
          <Button
            type="primary"
            onClick={async () => {
              const values = await form.validateFields();
              try {
                await requestValidateUpdate(values.species, values.description);
                setSpecies(values.species);
                setDescription(values.description);
                setName(values.name);
                setSeuratObjectRdsShowPage(true);
              } catch {
                message.error('failed');
              }
            }}
            size="large"
            disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC}
          >
            {dictionary.NEXT}
          </Button>
        )}
      </Layout.Footer>
    </Layout>
  );
};

export default SeuratObjectRdsUpload;
