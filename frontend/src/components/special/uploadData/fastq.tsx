import { FileTextTwoTone, InboxOutlined } from '@ant-design/icons';
import { Button, Form, Layout, message, Progress, Upload } from 'antd';
import React, { useEffect } from 'react';
import { useModel } from 'umi';
import BasicDataInfoForm from './basicDataInform';
import { AnalysisType } from '@/constants/analysis';

// interface Props {
//   speciesList: string[];
// }
const FastqUpload = () => {
  //   const { speciesList } = props;
  const [form] = Form.useForm();
  const [showPage, setShowPage] = React.useState(false);
  const {
    // targetAnalysisId,
    closeUploadDataUI,
  } = useModel('uploadDataUI');

  const { dictionary } = useModel('localization');

  const [species, setSpecies] = React.useState(null as null | string);

  const [uploadProgress, setUploadProgress] = React.useState(0);

  const [fileList, setFileList] = React.useState([] as any[]);

  const [isUploading, setIsUploading] = React.useState(false);

  const { isGuest } = useModel('user');
  const { analysisAccessType } = useModel('analysis');
  const isGuestUser = isGuest();

  useEffect(() => {
    setUploadProgress(0);
    setFileList([]);
    setIsUploading(false);
  }, []);

  const onChange = (info: any) => {
    console.log(info);
    message.warning('Please wait for the upload to complete.');
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
      {!showPage && (
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
          <h3>Fastq</h3>
          <BasicDataInfoForm form={form} />
        </Layout.Content>
      )}
      {showPage && (
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
          {/* <Select placeholder="Select a species" onChange={setSpecies} disabled>
            {speciesList.map((species) => {
              return (
                <Select.Option key={species} value={species}>
                  {species}
                </Select.Option>
              );
            })}
          </Select> */}
          <h3>Fastq</h3>
          {/* <div
            style={{
              height: '2rem',
            }}
          /> */}
          <div style={{ fontSize: '14px', marginBottom: '15px' }}>
            <span style={{ color: 'red' }}>*</span> Files
          </div>
          <Upload.Dragger
            disabled={!species}
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
            <p
              hidden={!!species}
              style={{
                color: '#ff4d4f',
              }}
            >
              {/* Please select a species first. */}
              Please wait for the upload to complete.
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
        </Layout.Content>
      )}
      <Layout.Footer
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        {/* <Button
                    danger
                >
                    abandon
                </Button> */}
        {showPage && (
          <Button
            // type="primary"
            style={{ color: '#2949B0', border: '1px solid #5B74C3', marginRight: '1rem' }}
            onClick={() => {
              setShowPage(false);
            }}
            size="large"
          >
            {dictionary.PREVIOUS}
          </Button>
        )}
        <div
          style={{
            width: '1rem',
          }}
        />
        {showPage && (
          <Button type="primary" onClick={closeUploadDataUI} size="large">
            {dictionary.FINISH}
          </Button>
        )}
        {!showPage && (
          <Button
            type="primary"
            onClick={async () => {
              const values = await form.validateFields();
              if (values.species) {
                setSpecies(values.species);
                setShowPage(true);
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

export default FastqUpload;
