import { ServiceCloud } from '@/constants';
import { ComponentType, UploadFromType, UploadType } from '@/constants/data';
import { ServiceCloudSelection } from '@/constants/serviceCloudSelection';
import { requestImportDatas } from '@/request/analysis';
import {
  requestAssembleDataComponent,
  requestCreateDataFrame,
  requestDataComponentUploadInfo,
  requestValidateUpdate,
} from '@/request/data';
import { CheckCircleFilled, CloudUploadOutlined } from '@ant-design/icons';
import { Button, Col, Form, Layout, message, Progress, Row, Segmented, Upload } from 'antd';
import React from 'react';
import { useModel } from 'umi';
import BasicDataInfoForm from './basicDataInform';
import { uploadFileToAWS, requestUploadToAWS } from '@/request/awsOperation';
import { AnalysisType } from '@/constants/analysis';

const Component2Accept: Record<string, string[]> = {
  [ComponentType.LAYER_SPLICED]: ['.csv', '.tsv', '.mtx'],
  [ComponentType.LAYER_UNSPLICED]: ['.csv', '.tsv', '.mtx'],
  [ComponentType.OBS]: ['.csv', '.tsv'],
  [ComponentType.VAR]: ['.csv', '.tsv'],
  [ComponentType.OBSM]: ['.csv', '.tsv', '.mtx'],
  [ComponentType.VARM]: ['.csv', '.tsv', '.mtx'],
  [ComponentType.VARP]: ['.csv', '.tsv', '.mtx'],
  [ComponentType.OBSP]: ['.csv', '.tsv', '.mtx'],
  [ComponentType.X]: ['.csv', '.tsv', '.mtx'],
};

interface ComponentBlockProps {
  componentType: string;
  disabled?: boolean;
  dataId?: string | null;
  species?: string | null;
  description?: string | null;
  setAssembleDataId: (dataId: string) => void;
  setGlobalDisabled: (disabled: boolean) => void;
  uploadStateChange: (componentType: string, state: boolean) => void;
  componentUploadedStateDict: any;
}

const ComponentBlock = (props: ComponentBlockProps) => {
  const {
    componentType,
    disabled,
    dataId,
    setAssembleDataId,
    setGlobalDisabled,
    species,
    description,
    uploadStateChange,
    componentUploadedStateDict,
  } = props;
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadProgress, setUploadProgress] = React.useState(0);

  const isComponentUploaded = componentUploadedStateDict[componentType];

  const uploadComponent = async (file: File) => {
    if (!species) {
      throw Error('species is null');
    }
    let _dataId = dataId;
    if (_dataId === null || _dataId === undefined) {
      setGlobalDisabled(true);
      const tempName = `${species}__${new Date().getTime()}`;
      try {
        const { data: dataFrame } = await requestCreateDataFrame(
          UploadFromType.FROMASSEMBLED,
          tempName,
          UploadType.ASSEMBLE,
          species,
          description,
        );
        _dataId = dataFrame.id;
        setAssembleDataId(dataFrame.id);
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
        componentType,
        fileSuffix,
        UploadType.ASSEMBLE,
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
        uploadStateChange(componentType, true);
      } catch (err) {
        console.log('err', err);
      }
    }
  };

  const onChange = (info: any) => {
    const { file } = info;
    uploadComponent(file);
  };

  return (
    <Upload.Dragger
      disabled={disabled}
      name="file"
      multiple={false}
      maxCount={1}
      onChange={onChange}
      beforeUpload={() => false}
      fileList={[]}
      style={{
        backgroundColor: '#fff',
      }}
      accept={Component2Accept[componentType].join(',')}
    >
      <div>
        <CloudUploadOutlined />
      </div>
      <p className="ant-upload-text">
        {componentType}
        {isComponentUploaded && (
          <CheckCircleFilled
            style={{
              color: '#52c41a',
              marginLeft: 5,
            }}
          />
        )}
      </p>
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

interface LayersBlockProps {
  disabled?: boolean;
  dataId?: string | null;
  species?: string | null;
  description?: string | null;
  setAssembleDataId: (dataId: string) => void;
  setGlobalDisabled: (disabled: boolean) => void;
  uploadStateChange: (componentType: string, state: boolean) => void;
  componentUploadedStateDict: any;
}

const LayersBlock = (props: LayersBlockProps) => {
  const {
    disabled,
    dataId,
    setAssembleDataId,
    setGlobalDisabled,
    species,
    description,
    uploadStateChange,
    componentUploadedStateDict,
  } = props;

  const layerList = [ComponentType.LAYER_UNSPLICED, ComponentType.LAYER_SPLICED, ComponentType.X];

  const [currentLayer, setCurrentLayer] = React.useState(ComponentType.LAYER_UNSPLICED);

  const currentIndex = layerList.indexOf(currentLayer);
  const renderLayerList = () => {
    return layerList.map((layer: string, index: number) => {
      const z = -Math.abs(index - currentIndex) * 20;
      const x = index * 15;
      return (
        <div
          key={layer}
          style={{
            width: `calc(100% - ${(layerList.length - 1) * 15}px)`,
            height: '100%',
            transform: `translate3d(${x}px, 0px, ${z}px)`,
            position: 'absolute',
            transition: 'transform 0.3s',
          }}
        >
          <ComponentBlock
            dataId={dataId}
            componentType={layer}
            disabled={disabled}
            setAssembleDataId={setAssembleDataId}
            setGlobalDisabled={setGlobalDisabled}
            species={species}
            description={description}
            uploadStateChange={uploadStateChange}
            componentUploadedStateDict={componentUploadedStateDict}
          />
        </div>
      );
    });
  };

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        perspective: '1000px',
        transformStyle: 'preserve-3d',
      }}
    >
      {renderLayerList()}
      <div
        style={{
          position: 'absolute',
          transform: 'translate(-50%, -50%)',
          top: '85%',
          left: '50%',
        }}
      >
        <Segmented options={layerList} onChange={setCurrentLayer} size="small" />
      </div>
    </div>
  );
};

const AssembleUpload = () => {
  const [form] = Form.useForm();

  const {
    targetAnalysisId,
    closeUploadDataUI,
    assembleShowPage,
    setAssembleShowPage,
    componentUploadedStateDict,
    setComponentUploadedStateDict,
    dataId,
    setDataId,
  } = useModel('uploadDataUI');

  const { dictionary } = useModel('localization');
  const { isGuest } = useModel('user');
  const { analysisAccessType } = useModel('analysis');
  const isGuestUser = isGuest();

  const updateComponentUploadedStateDict = (componentType: string, uploaded: boolean) => {
    setComponentUploadedStateDict({
      ...componentUploadedStateDict,
      [componentType]: uploaded,
    });
  };

  const [species, setSpecies] = React.useState<string>('');
  const [description, setDescription] = React.useState<string>('');

  const [disabled, setDisabled] = React.useState(false);

  const [assembling, setAssembling] = React.useState(false);

  const assembleData = async () => {
    if (dataId === null) {
      message.error('Please upload component first');
      return;
    }
    setAssembling(true);
    try {
      await requestAssembleDataComponent(dataId);
      if (targetAnalysisId !== null) {
        await requestImportDatas(targetAnalysisId, [dataId]);
      }
      message.success('Assemble data successfully');
    } catch (e: any) {
      message.error(e.message);
    }
    setAssembling(false);
    closeUploadDataUI();
  };

  const renderComponent = (componentType: string) => {
    return (
      <ComponentBlock
        dataId={dataId}
        componentType={componentType}
        disabled={disabled || !species}
        species={species}
        setAssembleDataId={setDataId}
        setGlobalDisabled={setDisabled}
        componentUploadedStateDict={componentUploadedStateDict}
        uploadStateChange={updateComponentUploadedStateDict}
      />
    );
  };

  return (
    <Layout>
      {!assembleShowPage && (
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
          <h3>Assemble</h3>
          <BasicDataInfoForm form={form} showName={false} />
        </Layout.Content>
      )}
      {assembleShowPage && (
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
          {/* <Select placeholder="Select a species" onChange={setSpecies}>
            {speciesList.map((species) => {
              return (
                <Select.Option key={species} value={species}>
                  {species}
                </Select.Option>
              );
            })}
          </Select> */}
          <h3>Assemble</h3>
          <Row
            gutter={[16, 16]}
            style={{
              paddingTop: '1rem',
              height: '10vh',
            }}
          >
            <Col span={5} />
            <Col span={5} />
            <Col span={10}>{renderComponent(ComponentType.VAR)}</Col>
            <Col span={4} />
          </Row>
          <Row
            gutter={16}
            style={{
              paddingTop: '1rem',
              height: '15vh',
            }}
          >
            <Col span={5}>{renderComponent(ComponentType.OBSP)}</Col>
            <Col span={5}>{renderComponent(ComponentType.OBSM)}</Col>
            <Col span={10}>
              <LayersBlock
                dataId={dataId}
                disabled={disabled || !species}
                setAssembleDataId={setDataId}
                setGlobalDisabled={setDisabled}
                species={species}
                description={description}
                uploadStateChange={updateComponentUploadedStateDict}
                componentUploadedStateDict={componentUploadedStateDict}
              />
            </Col>
            <Col span={4}>{renderComponent(ComponentType.OBS)}</Col>
          </Row>
          <Row
            gutter={[16, 16]}
            style={{
              paddingTop: '1rem',
              height: '10vh',
            }}
          >
            <Col span={5} />
            <Col span={5} />
            <Col span={10}>{renderComponent(ComponentType.VARM)}</Col>
            <Col span={4} />
          </Row>
          <Row
            gutter={[16, 16]}
            style={{
              paddingTop: '1rem',
              height: '10vh',
            }}
          >
            <Col span={5} />
            <Col span={5} />
            <Col span={10}>{renderComponent(ComponentType.VARP)}</Col>
            <Col span={4} />
          </Row>
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
        {assembleShowPage && (
          <Button
            // type="primary"
            style={{ color: '#2949B0', border: '1px solid #5B74C3', marginRight: '1rem' }}
            onClick={() => {
              setAssembleShowPage(false);
            }}
            size="large"
          >
            {dictionary.PREVIOUS}
          </Button>
        )}
        {assembleShowPage && (
          <Button
            type="primary"
            size="large"
            onClick={assembleData}
            disabled={disabled || !species || dataId === null}
            loading={assembling}
          >
            {dictionary.ASSEMBLE}
          </Button>
        )}
        <div
          style={{
            width: '1rem',
          }}
        />
        {assembleShowPage && (
          <Button
            // type="primary"
            onClick={closeUploadDataUI}
            size="large"
          >
            {dictionary.FINISH}
          </Button>
        )}
        {!assembleShowPage && (
          <Button
            type="primary"
            onClick={async () => {
              const values = await form.validateFields();
              try {
                await requestValidateUpdate(values.species, values.description);
                setSpecies(values.species);
                setDescription(values.description);
                setAssembleShowPage(true);
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

export default AssembleUpload;
