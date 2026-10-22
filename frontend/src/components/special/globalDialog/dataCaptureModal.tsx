import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, Button, Card, message } from 'antd';
import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { useModel } from 'umi';
import { FileTextOutlined } from '@ant-design/icons';
import './index.less';
import { requestDataCapture } from '@/request/functionBlock';
import { UploadFromType, UploadType } from '@/constants/data';
import {
  requestAssembleDataComponent,
  requestCreateDataFrame,
  requestDataComponentUploadInfo,
} from '@/request/data';
import { uploadFileToAWS } from '@/request/awsOperation';
import { getLocationParams } from '@/util/getUrl';
import { requestImportDatas } from '@/request/analysis';

const DataCaptureModal: React.FC = () => {
  const { dataCaptureModalVisible, setDataCaptureModalVisible } = useModel('thirdPartyDataSource');
  const [form] = Form.useForm();
  const [userRequest, setUserRequest] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [sampleData, setSampleData] = useState<any[]>([]);
  const { dictionary } = useModel('localization');
  const { isGuest } = useModel('user');
  const isGuestUser = isGuest();
  const [analysisId] = getLocationParams(['analysis-id']);

  useEffect(() => {
    const handleOpenDataCapture = () => {
      setDataCaptureModalVisible(true);
    };

    window.addEventListener('openDataCaptureModal', handleOpenDataCapture);

    return () => {
      window.removeEventListener('openDataCaptureModal', handleOpenDataCapture);
    };
  }, [setDataCaptureModalVisible]);

  const handleClose = () => {
    setDataCaptureModalVisible(false);
    form.resetFields();
    setSampleData([]);
    setUserRequest('');
  };

  const handleReset = () => {
    form.resetFields();
    setUserRequest('');
  };

  const handleCapture = () => {
    form
      .validateFields()
      .then(async () => {
        try {
          setLoading(true);
          const response = await requestDataCapture(userRequest);
          if (response?.data?.data?.selected_data_list) {
            const sortedData = response.data.data.selected_data_list
              .sort((a, b) => b.conformity_degree - a.conformity_degree)
              .map((item) => ({
                id: item.id,
                title: item.name,
                description: item.data_description,
                reason: item.reason,
                status: 'import',
              }));
            setSampleData(sortedData);
          }
        } catch (error) {
          console.error('Failed to fetch data:', error);
        } finally {
          setLoading(false);
        }
      })
      .catch((errorInfo) => {
        console.error('Validation failed:', errorInfo);
      });
  };

  const updateDatasetStatus = (id: string, status: 'importing' | 'import' | 'imported') => {
    setSampleData((prevData) =>
      prevData.map((item) =>
        item.id === id
          ? {
              ...item,
              status,
              disabled: status === 'importing',
            }
          : item,
      ),
    );
  };

  const importDataSource = async (
    id,
    name,
    description,
    analysisId?: string | null,
    uploadType: string,
  ) => {
    updateDatasetStatus(id, 'importing');

    try {
      const { data: createDataFrameResult } = await requestCreateDataFrame(
        UploadFromType.THIRD_PARTY_DATA,
        name,
        UploadType.THIRD_PARTY_DATA,
        'Unknown',
        description,
      );
      const { id: dataFrameId } = createDataFrameResult;

      const { data: uploadInfo } = await requestDataComponentUploadInfo(
        dataFrameId as string,
        'ident.txt',
        '',
        UploadType.THIRD_PARTY_DATA,
        id.length,
      );
      const info = {
        third_party_data_id: id,
        upload_type: uploadType,
      };
      const infoStr = JSON.stringify(info);
      const file = new File([new Blob([infoStr])], 'ident.txt');
      await uploadFileToAWS(file, uploadInfo.presigned_url, new AbortController());
      await requestAssembleDataComponent(dataFrameId);
      if (!!analysisId) {
        await requestImportDatas(analysisId, [dataFrameId]);
      }

      updateDatasetStatus(id, 'imported');
      message.success('The target data was successfully obtained, please wait for prehandling...');
    } catch (e) {
      updateDatasetStatus(id, 'import');
      message.error('Failed to get data source');
      console.error(e);
    }
  };

  return (
    <Modal
      centered
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CustomImage name={customIconNames.AIICONSTAR} style={{ height: '16px' }} />
          <span className="gradient-text">{dictionary.DATA_CAPTURE}</span>
        </div>
      }
      open={dataCaptureModalVisible}
      onCancel={handleClose}
      footer={null}
      width={sampleData.length === 0 ? 900 : 1200}
    >
      <div style={{ display: 'flex', gap: '24px' }}>
        {/* Left Section */}
        <div style={{ flex: 1 }}>
          <Form layout="vertical" form={form}>
            <Form.Item
              label={
                <span style={{ fontWeight: 600, color: 'black' }}>
                  {dictionary.DESCRIBE_DATASET}
                </span>
              }
              name="analysis"
              rules={[{ required: true, message: dictionary.FIELD_REQUIRED }]}
            >
              <Input.TextArea
                placeholder={dictionary.DATASET_PLACEHOLDER}
                rows={5}
                onChange={(e) => setUserRequest(e.target.value)}
              />
            </Form.Item>

            {/* <Collapse>
              <Panel
                header="Adding following tag selections can make capture be more accurate."
                key="1"
              >
                {[
                  { label: 'Data format', name: 'dataFormat' },
                  { label: 'Species', name: 'species' },
                  { label: 'Organism', name: 'organism' },
                  { label: 'Disease', name: 'disease' },
                  { label: 'Cell Count', name: 'cellCount' },
                ].map(({ label, name }) => (
                  <Form.Item key={name} label={label} name={name}>
                    <Select placeholder={`Selected ${label.toLowerCase()}`}>
                      <Option value="option1">Option 1</Option>
                      <Option value="option2">Option 2</Option>
                    </Select>
                  </Form.Item>
                ))}
              </Panel>
            </Collapse> */}

            <div
              style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '16px' }}
            >
              <Button onClick={handleReset}>{dictionary.RESET}</Button>
              <Button
                type="primary"
                loading={loading}
                onClick={handleCapture}
                disabled={isGuestUser}
              >
                {!loading && (
                  <CustomImage
                    name={customIconNames.AIICONSTARWHITE}
                    style={{ height: '16px', marginRight: '8px' }}
                  />
                )}
                {dictionary.CAPTURE}
              </Button>
            </div>
          </Form>
        </div>

        {/* Right Section */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: sampleData.length === 0 ? 'center' : 'flex-start',
            justifyContent: sampleData.length === 0 ? 'center' : 'flex-start',
            textAlign: sampleData.length === 0 ? 'center' : 'left',
            paddingRight: '10px',
            maxHeight: '400px',
            overflowY: 'auto',
          }}
        >
          {sampleData.length === 0 ? (
            <>
              <h3 style={{ fontWeight: 600, fontSize: '16px' }}>
                {dictionary.FILL_FORM_INSTRUCTION}
              </h3>
              <ul
                style={{
                  listStyle: 'none',
                  padding: 0,
                  marginTop: '12px',
                  color: '#666',
                  lineHeight: '1.8',
                }}
              >
                <li> {dictionary.DATA_SOURCE_DESCRIPTION} </li>
              </ul>
            </>
          ) : (
            sampleData.map((item) => (
              <Card key={item.id} style={{ marginBottom: '12px', width: '100%' }}>
                <h4
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-start',
                    gap: '5px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <FileTextOutlined style={{ height: '16px', marginRight: '8px' }} />
                    {item.title}
                  </div>
                  <div style={{ flex: 1 }} />
                  <Button
                    size="small"
                    type="default"
                    onClick={() =>
                      importDataSource(
                        item.id,
                        item.title,
                        item.description,
                        analysisId,
                        UploadType.GENERAL,
                      )
                    }
                    loading={item.status === 'importing'}
                    disabled={item.status === 'importing' || item.status === 'imported'}
                  >
                    {item.status === 'imported'
                      ? dictionary.IMPORTED
                      : item.status === 'importing'
                      ? dictionary.IMPORTING
                      : dictionary.IMPORT}{' '}
                    as General
                  </Button>
                  <Button
                    size="small"
                    type="primary"
                    onClick={() =>
                      importDataSource(
                        item.id,
                        item.title,
                        item.description,
                        analysisId,
                        UploadType.THIRD_PARTY_DATA,
                      )
                    }
                    loading={item.status === 'importing'}
                    disabled={item.status === 'importing' || item.status === 'imported'}
                  >
                    {item.status === 'imported'
                      ? dictionary.IMPORTED
                      : item.status === 'importing'
                      ? dictionary.IMPORTING
                      : dictionary.IMPORT}{' '}
                    as Anndata
                  </Button>
                </h4>
                <p style={{ color: '#666', fontSize: '12px' }}>{item.description}</p>
                <p style={{ color: '#666', fontSize: '12px' }}>
                  {dictionary.REASON}: {item.reason}
                </p>
              </Card>
            ))
          )}
        </div>
      </div>
    </Modal>
  );
};

export default DataCaptureModal;
