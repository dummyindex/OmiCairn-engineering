import { DemoFunctionBlockUrl, ServiceCloud } from '@/constants';
import { AnalysisType } from '@/constants/analysis';
import { ServiceCloudSelection } from '@/constants/serviceCloudSelection';
import { requestUploadToAWS, uploadFileToAWS } from '@/request/awsOperation';
import {
  requestCreateFBGroup,
  requestPreprocessFunctionBlockVersion,
  requestPrivateFBGroupList,
  requestUploadFunctionBlockPrivate,
} from '@/request/functionBlock';
import {
  DownloadOutlined,
  FileTextTwoTone,
  InboxOutlined,
  PlusOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import {
  Button,
  Form,
  Input,
  Layout,
  message,
  Modal,
  Progress,
  Radio,
  Select,
  Upload,
  Tooltip,
  Divider,
  Space,
} from 'antd';
import JSZip from 'jszip';
import { useEffect, useState, useRef } from 'react';
import type { InputRef } from 'antd';
import { useModel, useLocation } from 'umi';
import './index.less';

const formItemLayout = {
  labelCol: { span: 8 }, // Label spans a full row
  wrapperCol: { span: 16 }, // Input spans a full row
};

const UploadPage = ({ onUploadSuccess }) => {
  const { analysisAccessType } = useModel('analysis');
  const [isValidFile, setIsValidFile] = useState(true);
  const [isDragging, setIsDragging] = useState(false);

  const {
    uploadProgress,
    setUploadProgress,
    isUploading,
    setIsUploading,
    createInfo,
    setCreateInfo,
    setFile,
  } = useModel('functionBlockCreate');

  const uploadFile = async (file: File) => {
    setIsUploading(true);

    try {
      const zip = new JSZip();
      const zipContent = await zip.loadAsync(file);

      try {
        const jsonFile = zipContent.files['static-config.json'];
        const jsonData = JSON.parse(await jsonFile.async('text'));

        const { name, group, version } = jsonData;

        const type = 'computation';
        createInfo.name = name;
        createInfo.type = type;
        createInfo.groupName = group;
        createInfo.groupId = '';
        createInfo.versionName = version;
        onUploadSuccess();
      } catch (e) {
        message.error('Zip file must contain static-config.json.');
        setIsValidFile(false);
        setIsUploading(false);
        return;
      }
    } catch (e) {
      console.error(e);
      message.error('Upload failed.');
      setIsValidFile(false);
      setIsUploading(false);
      return;
    }
    setIsValidFile(true);
    setIsUploading(false);
    setUploadProgress(0);
    setCreateInfo(createInfo);
    setFile(file);
  };

  const handleFileChange = async (info: any) => {
    const file = info.file;
    await uploadFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (analysisAccessType !== AnalysisType.PUBLIC) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (analysisAccessType === AnalysisType.PUBLIC) {
      return;
    }

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      if (file.name.endsWith('.zip')) {
        await uploadFile(file);
      } else {
        message.error('Please upload .zip files only.');
      }
    }
  };

  const itemRender = (_: any, file: File) => {
    return isValidFile ? (
      <div
        style={{
          paddingTop: '0.5rem',
          paddingLeft: '0.5rem',
        }}
      >
        <FileTextTwoTone />
        <span style={{ paddingLeft: '0.5rem' }}>{file.name}</span>
      </div>
    ) : null;
  };

  return (
    <Layout>
      <Layout.Content className="uploadDraggerContainer">
        <div
          style={{
            fontSize: '15px',
            marginTop: '-8px',
            marginBottom: '8px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>
            <span className="labelRequired">*</span> Files
          </span>
          {DemoFunctionBlockUrl && (
            <Button
              type="link"
              icon={<DownloadOutlined />}
              size="small"
              onClick={() => {
                window.open(DemoFunctionBlockUrl);
              }}
            >
              Download Demo
            </Button>
          )}
        </div>

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`uploadContainer ${isDragging ? 'dragging' : ''} ${
            analysisAccessType === AnalysisType.PUBLIC ? 'noDragging' : ''
          }`}
        >
          <Upload.Dragger
            disabled={isUploading || analysisAccessType === AnalysisType.PUBLIC}
            name="file"
            multiple={false}
            maxCount={1}
            onChange={handleFileChange}
            beforeUpload={() => false}
            itemRender={itemRender}
            accept=".zip"
            className={`${isDragging ? 'dragging' : ''} ${
              analysisAccessType === AnalysisType.PUBLIC ? 'noDragging' : ''
            }`}
          >
            <p className="ant-upload-drag-icon" style={{ marginBottom: '10px' }}>
              <InboxOutlined />
            </p>
            <p className="ant-upload-text" style={{ fontSize: '15px', marginBottom: '2px' }}>
              Upload to autofill information form
            </p>
            <p className="ant-upload-text" style={{ fontSize: '15px', marginBottom: '2px' }}>
              Click or drag file to this area to upload
            </p>
            <p className="ant-upload-hint" style={{ fontSize: '13px' }}>
              Support for a zip upload.
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
        </div>
      </Layout.Content>
    </Layout>
  );
};

const ModifyUploadInfo = () => {
  const { closeUploadFbModal } = useModel('functionBlockCreate');
  const { dictionary } = useModel('localization');
  const [fblist, setFblist] = useState<any[]>([]);
  const [form] = Form.useForm();
  const [name, setName] = useState('');
  const inputRef = useRef<InputRef>(null);
  const [tempFblist, setTempFblist] = useState<any[]>([]);

  const {
    file: uploadedFile,
    createInfo,
    setCreateInfo,
    setUploadProgress,
    setIsUploading,
    currentUploadIdRef,
  } = useModel('functionBlockCreate');

  const getfblist = async () => {
    try {
      const { data: fblist } = await requestPrivateFBGroupList();
      setFblist(fblist);
    } catch (e) {
      message.error('Failed to request function block list.');
    }
  };

  useEffect(() => {
    getfblist();
  }, []);

  useEffect(() => {
    setTempFblist(fblist);
  }, [fblist]);

  const handleNameChange = (e) => {
    try {
      const name = e.target.value;
      setCreateInfo((prevUploadInfo) => ({ ...prevUploadInfo, name: name }));
    } catch (e) {
      message.error('Failed to autofill the name field. Please enter the name manually.');
    }
  };

  const handleTypeChange = (e) => {
    try {
      const type = e.target.value;
      setCreateInfo((prevUploadInfo) => ({ ...prevUploadInfo, type: type }));
    } catch (e) {
      message.error('Failed to autofill the type field. Please choose the type manually.');
    }
  };

  const handleGroupChange = (value, label) => {
    try {
      setCreateInfo((prevUploadInfo) => ({
        ...prevUploadInfo,
        groupName: label.label,
        groupId: value,
      }));
    } catch (e) {
      message.error(
        'Failed to autofill the group field. Please choose the function block manually.',
      );
    }
  };

  const handleVersionNameChange = (e) => {
    try {
      const versionName = e.target.value;
      setCreateInfo((prevUploadInfo) => ({ ...prevUploadInfo, versionName: versionName }));
    } catch (e) {
      message.error(
        'Failed to autofill the version name field. Please enter the version name manually.',
      );
    }
  };

  const validateUploadInfo = () => {
    if (createInfo.name === '' || createInfo.name === undefined || createInfo.name === null) {
      message.error('Name cannot be empty!');
      return false;
    }
    if (createInfo.type === '' || createInfo.type === undefined || createInfo.type === null) {
      message.error('Type cannot be empty!');
      return false;
    }
    if (
      createInfo.groupName === '' ||
      createInfo.groupName === undefined ||
      createInfo.groupName === null
    ) {
      message.error('Group cannot be empty!');
      return false;
    }
    if (
      createInfo.versionName === '' ||
      createInfo.versionName === undefined ||
      createInfo.versionName === null
    ) {
      message.error('Version name cannot be empty!');
      return false;
    }
    return true;
  };

  const getGroupIdAndCreateIfNotExists = async () => {
    // The uploaded group already exists in the dropdown, or the uploaded group is empty but the user selected a group from the dropdown
    for (let i = 0; i < fblist.length; i++) {
      if (fblist[i].name === createInfo.groupName) {
        createInfo.groupId = fblist[i].id;
        return createInfo.groupId;
      }
    }

    // The uploaded group does not exist; create a new group
    try {
      const result = await requestCreateFBGroup(createInfo.groupName);
      createInfo.groupId = result.data.id;
      message.success('Successfully created a new function block: ' + createInfo.groupName);
      return createInfo.groupId;
    } catch (e) {
      message.error('Failed to create a new function block.');
    }
  };

  const onNameChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setName(event.target.value);
  };

  const addItem = (e: React.MouseEvent<HTMLButtonElement | HTMLAnchorElement>) => {
    e.preventDefault();
    if (tempFblist.some((fb) => fb.name === name)) {
      return;
    }
    setTempFblist((prevFblist) => [
      ...prevFblist,
      {
        id: name,
        name: name,
      },
    ]);
    setCreateInfo((prevUploadInfo) => ({
      ...prevUploadInfo,
      groupName: name,
    }));
    setName('');
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
  };

  return (
    <Layout>
      <Layout.Content
        style={{
          padding: '1.2rem',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'stretch',
          maxHeight: '55vh',
          overflow: 'auto',
        }}
      >
        <div style={{ fontSize: '15px', marginTop: '-5px', marginBottom: '15px' }}>
          <span style={{ color: 'red' }}>*</span> Upload Information Form (Autofilled)
        </div>

        <Form form={form} {...formItemLayout} autoComplete="off">
          <Form.Item
            label={
              <span>
                {dictionary.NAME}&nbsp;
                <Tooltip title="Enter a unique name for this item. For example, sc-pl-scatter.">
                  <QuestionCircleOutlined />
                </Tooltip>
              </span>
            }
            name="name"
          >
            <span className="prompt-sentence">*e.g. sc-pl-scatter</span>
            <Input
              placeholder="Please enter a name"
              value={createInfo.name}
              onChange={handleNameChange}
            />
          </Form.Item>
          <Form.Item
            label={
              <span>
                {dictionary.TYPE}&nbsp;
                <Tooltip title="Select the type of item. Default is 'Computation'.">
                  <QuestionCircleOutlined />
                </Tooltip>
              </span>
            }
            name="type"
            initialValue="computation"
          >
            <Radio.Group onChange={handleTypeChange} value={createInfo.type}>
              <Radio value="computation">Computation</Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item
            label={
              <span>
                Group&nbsp;
                <Tooltip title="Choose from existing blocks or create a new one.">
                  <QuestionCircleOutlined />
                </Tooltip>
              </span>
            }
            name="group"
          >
            <span className="prompt-sentence">
              *choose from existing blocks or create a new one
            </span>
            <Select
              value={createInfo.groupName}
              onChange={handleGroupChange}
              dropdownRender={(menu) => (
                <>
                  {menu}
                  <Divider style={{ margin: '8px 0' }} />
                  <Space style={{ padding: '0 8px 4px' }}>
                    <Input
                      placeholder="Please enter a new group"
                      ref={inputRef}
                      value={name}
                      onChange={onNameChange}
                      onKeyDown={(e) => e.stopPropagation()}
                    />
                    <Button type="text" icon={<PlusOutlined />} onClick={addItem}>
                      Add group
                    </Button>
                  </Space>
                </>
              )}
            >
              {tempFblist.map((fb) => (
                <Select.Option key={fb.id} value={fb.id} label={fb.name}>
                  {fb.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label={
              <span>
                Version name&nbsp;
                <Tooltip title="Enter the version name for this item. For example, 0.0.1.">
                  <QuestionCircleOutlined />
                </Tooltip>
              </span>
            }
            name="versionName"
          >
            <span className="prompt-sentence">*e.g. 0.0.1</span>
            <Input
              placeholder="Please enter a version name"
              value={createInfo.versionName}
              onChange={handleVersionNameChange}
            />
          </Form.Item>
        </Form>
      </Layout.Content>
      <Layout.Footer>
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            marginRight: '-30px',
            marginTop: '-28px',
          }}
        >
          <Button
            style={{ marginRight: '10px' }}
            onClick={async () => {
              try {
                form.resetFields();
                setCreateInfo({
                  name: '',
                  type: 'computation',
                  groupName: '',
                  groupId: '',
                  versionName: '',
                });
              } catch {
                message.error('Failed to clear the form.');
              }
            }}
            size="primary"
          >
            Clear all
          </Button>

          <Button
            type="primary"
            onClick={async () => {
              if (!validateUploadInfo()) {
                return;
              }
              setIsUploading(true);
              if (ServiceCloud == ServiceCloudSelection.AWS) {
                try {
                  const file: File = uploadedFile;
                  await getGroupIdAndCreateIfNotExists();
                  const {
                    data: { version, s3Info: uploadInformation },
                  } = await requestUploadFunctionBlockPrivate(
                    createInfo.name,
                    createInfo.type,
                    createInfo.groupId,
                    createInfo.versionName,
                    file?.size,
                  );
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
                        setUploadProgress(Math.ceil(progress));
                      },
                    );
                  } else {
                    await uploadFileToAWS(
                      file,
                      uploadInformation.presigned_url,
                      new AbortController(),
                      (progress: number) => {
                        setUploadProgress(Math.ceil(progress));
                      },
                    );
                  }
                  await requestPreprocessFunctionBlockVersion(version.id);
                  message.success('Upload successfully.');
                  setIsUploading(false);
                  setUploadProgress(0);
                  form.resetFields();
                  setCreateInfo({
                    name: '',
                    type: 'computation',
                    groupName: '',
                    groupId: '',
                    versionName: '',
                  });
                  closeUploadFbModal();
                } catch (e) {
                  console.error(e);
                  setIsUploading(false);
                  setUploadProgress(0);
                  message.error('Upload failed.');
                }
              }
              setIsUploading(false);
              setUploadProgress(0);
            }}
            size="primary"
          >
            Finish and Upload
          </Button>
        </div>
      </Layout.Footer>
    </Layout>
  );
};

const CreateFunctionBlock = () => {
  const { closeUploadFbModal, showUploadFbModal } = useModel('functionBlockCreate');
  const { dictionary } = useModel('localization');
  const [isUploadSuccessful, setIsUploadSuccessful] = useState(false);
  const location = useLocation();

  useEffect(() => {
    if (showUploadFbModal) {
      closeUploadFbModal();
    }
  }, [location.pathname]);

  return (
    <Modal
      centered
      destroyOnClose
      open={showUploadFbModal}
      onCancel={() => closeUploadFbModal()}
      title={dictionary.UPLOAD}
      okButtonProps={{ hidden: true }}
      cancelButtonProps={{ hidden: true }}
      width="38vw"
    >
      <UploadPage onUploadSuccess={() => setIsUploadSuccessful(true)} />
      {isUploadSuccessful && <ModifyUploadInfo />}
    </Modal>
  );
};

export default CreateFunctionBlock;
