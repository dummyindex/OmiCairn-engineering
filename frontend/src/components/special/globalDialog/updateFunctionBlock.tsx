import { ServiceCloud } from '@/constants';
import { AnalysisType } from '@/constants/analysis';
import { ServiceCloudSelection } from '@/constants/serviceCloudSelection';
import { requestUploadToAWS, uploadFileToAWS } from '@/request/awsOperation';
import {
  requestPreprocessFunctionBlockVersion,
  requestUpdateFunctionBlockPrivate,
  requestValidateUpdateForm,
} from '@/request/functionBlock';
import { FileTextTwoTone, InboxOutlined } from '@ant-design/icons';
import { Button, Form, Input, Layout, message, Modal, Progress, Upload } from 'antd';
import { useEffect } from 'react';
import { useModel } from 'umi';
import { FunctionBlockUpdateStep } from '@/constants/functionBlock';

const formItemLayout = {
  labelCol: { span: 8 }, // Label spans a full row
  wrapperCol: { span: 16 }, // Input spans a full row
};

// Modal form for updating a function block
const UpdateFBForm = (props) => {
  const { form, updatedFBId, validateError } = props;
  const handleSetFieldValue = () => {
    form.setFieldsValue({
      functionBlockId: updatedFBId,
      // versionName: '1.1',
    });
  };
  useEffect(() => {
    handleSetFieldValue();
  }, []);
  return (
    <div>
      <Form form={form} {...formItemLayout}>
        <Form.Item
          label="Function Block Id"
          name="functionBlockId"
          style={{ marginBottom: '0' }}
          // rules={[{ required: true, message: 'function_block_id cannot be empty!' }]}
        >
          <Input disabled />
        </Form.Item>
        <div style={{ color: '#ff4d4f', display: 'flex', justifyContent: 'right' }}>
          <div style={{ width: '66.6%' }}>{validateError.function_block_id}</div>
        </div>
        <Form.Item
          label="Version name"
          name="versionName"
          style={{ marginBottom: '0', marginTop: '24px' }}
          // rules={[{ required: true, message: 'version name cannot be empty!' }]}
        >
          <Input placeholder="Please enter a version name" />
        </Form.Item>
        <div style={{ color: '#ff4d4f', display: 'flex', justifyContent: 'right' }}>
          <div style={{ width: '66.6%' }}>{validateError.version_name}</div>
        </div>
      </Form>
    </div>
  );
};

const UpdatePage = () => {
  const {
    currentUploadIdRef,
    updatedStep,
    setUpdatedStep,
    updatedFBId,
    setUpdatedFBId,
    uploadProgress,
    setUploadProgress,
    isUploading,
    setIsUploading,
    fileList,
    setFileList,
    validateError,
    setValidateError,
    updateInfo,
    setUpdateInfo,
  } = useModel('functionBlockUpdate');
  const { analysisAccessType } = useModel('analysis');
  const [form] = Form.useForm();

  const pushFile = (file: any) => {
    setFileList([...fileList, file]);
  };
  const uploadFile = async (file: File) => {
    setIsUploading(true);
    if (ServiceCloud == ServiceCloudSelection.AWS) {
      try {
        const {
          data: { version, s3Info: uploadInformation },
        } = await requestUpdateFunctionBlockPrivate(
          updateInfo.functionBlockId,
          updateInfo.versionName,
          file.size,
        );

        currentUploadIdRef.current = uploadInformation.uploadId;

        if (uploadInformation.multipart) {
          await requestUploadToAWS(
            file,
            uploadInformation.partInfoList,
            uploadInformation.part_count,
            uploadInformation.part_size,
            uploadInformation.object_key,
            uploadInformation.uploadId,
            (progress: number) => {
              if (currentUploadIdRef.current !== uploadInformation.uploadId) {
                return;
              }
              console.log(Math.ceil(progress));
              setUploadProgress(Math.ceil(progress));
            },
          );
        } else {
          await uploadFileToAWS(file, uploadInformation.presigned_url, null, (progress: number) => {
            setUploadProgress(Math.ceil(progress));
          });
        }
        await requestPreprocessFunctionBlockVersion(version.id);
        pushFile(file);
        message.success('Upload successfully.');
      } catch (e) {
        console.error(e);
        message.error('Upload failed.');
      }
    }
    setIsUploading(false);
    setUploadProgress(0);
  };

  const onChange = async (info: any) => {
    const file = info.file;
    await uploadFile(file);
  };

  const itemRender = (_: any, file: File) => {
    return (
      <div
        style={{
          paddingTop: '0.5rem',
          paddingLeft: '0.5rem',
        }}
      >
        <FileTextTwoTone />
        <span style={{ paddingLeft: '0.5rem' }}>{file.name}</span>
      </div>
    );
  };

  return (
    <Layout>
      {updatedStep === FunctionBlockUpdateStep.INPUT && (
        <Layout.Content
          style={{
            padding: '2rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'stretch',
            maxHeight: '55vh',
            overflow: 'auto',
          }}
        >
          <UpdateFBForm form={form} updatedFBId={updatedFBId} validateError={validateError} />
        </Layout.Content>
      )}
      {updatedStep === FunctionBlockUpdateStep.UPLOAD && (
        <Layout.Content
          style={{
            padding: '2rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'stretch',
            maxHeight: '55vh',
            overflow: 'auto',
          }}
        >
          <div style={{ fontSize: '14px', marginBottom: '15px' }}>
            <span style={{ color: 'red' }}>*</span> Files
          </div>
          <Upload.Dragger
            disabled={isUploading || analysisAccessType === AnalysisType.PUBLIC}
            // disabled={!species || isUploading}
            name="file"
            multiple={false}
            maxCount={1}
            onChange={onChange}
            // onDrop={onDrop}
            beforeUpload={() => false}
            fileList={fileList}
            itemRender={itemRender}
            accept=".zip"
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to this area to upload</p>
            <p className="ant-upload-hint">Support for a zip upload.</p>

            {isUploading && (
              <Progress
                style={{
                  width: '90%',
                }}
                percent={uploadProgress}
              />
            )}
          </Upload.Dragger>
        </Layout.Content>
      )}
      <Layout.Footer
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        <div
          style={{
            width: '1rem',
          }}
        />
        {updatedStep === FunctionBlockUpdateStep.UPLOAD && (
          <Button
            // type="primary"
            style={{ color: '#2949B0', border: '1px solid #5B74C3', marginRight: '1rem' }}
            onClick={() => {
              setUpdatedStep(FunctionBlockUpdateStep.INPUT);
            }}
            size="large"
          >
            Previous
          </Button>
        )}
        {updatedStep === FunctionBlockUpdateStep.UPLOAD && (
          <Button
            type="primary"
            disabled={analysisAccessType === AnalysisType.PUBLIC}
            onClick={() => {
              setUpdatedFBId(null);
            }}
            size="large"
          >
            finish
          </Button>
        )}
        {updatedStep === FunctionBlockUpdateStep.INPUT && (
          <Button
            type="primary"
            onClick={async () => {
              const { functionBlockId, versionName } = await form.validateFields();
              const { data } = await requestValidateUpdateForm(functionBlockId, versionName);
              const ValidateError = {};
              console.log(data);
              data.map((item) => {
                if (ValidateError[item.field] === undefined) {
                  ValidateError[item.field] = item.reason;
                  setValidateError(ValidateError);
                  console.log('ValidateError: ', ValidateError);
                }
              });

              if (data.length === 0) {
                setUpdateInfo({ functionBlockId: functionBlockId, versionName: versionName });
                setUpdatedStep(FunctionBlockUpdateStep.UPLOAD);
              }
            }}
            size="large"
          >
            Next
          </Button>
        )}
      </Layout.Footer>
    </Layout>
  );
};

const UpdateFunctionBlock = () => {
  const { updatedFBId, setUpdatedFBId } = useModel('functionBlockUpdate');
  return (
    <Modal
      centered
      destroyOnClose
      open={!!updatedFBId || updatedFBId === 0}
      onCancel={() => {
        setUpdatedFBId(null);
      }}
      cancelText="close"
      title="Update Function Block"
      okButtonProps={{ hidden: true }}
      cancelButtonProps={{ hidden: true }}
      width="35vw"
    >
      <UpdatePage />
    </Modal>
  );
};

export default UpdateFunctionBlock;
