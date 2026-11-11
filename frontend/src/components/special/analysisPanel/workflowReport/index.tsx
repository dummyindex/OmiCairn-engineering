import { useState, useEffect, useRef } from 'react';
import { useModel, useLocation } from 'umi';

import { Spin, Modal, Form, Input, message } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';

import {
  requestDeleteWorkflowReport,
  requestUpdateWorkflowReportContent,
  requestUpdateWorkflowReportMetadata,
  requestWorkflowReportContent,
  requestWorkflowReportInfo,
  requestWorkflowReportList,
} from '@/request/workflowReport';

import './index.css';
import type { WorkflowReport } from '@/interfaces/workflowReport';
import ReportList from '@/components/special/analysisPanel/workflowReport/reportList';
import CustomQuillToolbar from '@/components/special/analysisPanel/workflowReport/customQuillToolbar';
import RightSider from '@/components/special/analysisPanel/workflowReport/rightSider';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
const WorkflowReportPage = () => {
  const location = useLocation();

  const { analysisId } = useModel('analysis');

  const { dictionary } = useModel('localization');

  const [metaDataForm] = Form.useForm();

  const [listLoading, setListLoading] = useState<boolean>(false);

  const [contentLoading, setContentLoading] = useState<boolean>(false);

  const [reportList, setReportList] = useState<WorkflowReport[]>([]);

  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const editorRef = useRef<ReactQuill>(null);

  const [content, setContent] = useState<string>('');

  const [metadataEditedReportUuid, setMetadataEditedReportUuid] = useState<string | null>(null);

  const [metadataEditing, setMetadataEditing] = useState<boolean>(false);

  const [deletedReportUuid, setDeletedReportUuid] = useState<string | null>(null);

  const [deleting, setDeleting] = useState<boolean>(false);

  const refreshTimer = useRef<NodeJS.Timeout | null>(null);

  const contentSaveTimer = useRef<NodeJS.Timeout | null>(null);

  const fetchReportInfo = async (uuid: string) => {
    const { data: report } = await requestWorkflowReportInfo(uuid);
    return report;
  };

  const initWithReport = async (uuid: string) => {
    const report = await fetchReportInfo(uuid);
    if (report) {
      setSelectedKey(`${report.uuid}/${report.reportName}.txt`);
    }
  };

  const initReports = async () => {
    if (!analysisId) {
      setReportList([]);
      return;
    }
    setListLoading(true);
    try {
      const { data: reports } = await requestWorkflowReportList(analysisId);
      setReportList(reports);
    } catch (e) {
      console.error(e);
      setReportList([]);
    } finally {
      setListLoading(false);
    }
  };

  const loadReports = async () => {
    if (!analysisId) {
      setReportList([]);
      return;
    }
    try {
      const { data: reports } = await requestWorkflowReportList(analysisId);
      setReportList(reports);
    } catch (e) {
      console.error(e);
      setReportList([]);
    }
  };

  const loadReportContent = async () => {
    if (!selectedKey) {
      setContent('');
      return;
    }
    setContentLoading(true);
    try {
      const [uuid, fileName] = selectedKey.split('/');
      if (!uuid || !fileName) {
        setContent('');
        return;
      }
      const content = await requestWorkflowReportContent(uuid, fileName);
      setContent(content);
    } catch (e) {
      console.error(e);
    } finally {
      setContentLoading(false);
    }
  };

  const saveReportContent = async (newContent: string, resultPrompt: boolean = false) => {
    if (!selectedKey) {
      return;
    }
    try {
      const [uuid, fileName] = selectedKey.split('/');
      if (!uuid || !fileName) {
        return;
      }
      await requestUpdateWorkflowReportContent(uuid, fileName, newContent);
      if (resultPrompt) {
        message.success('Content saved');
      }
    } catch (e) {
      console.error(e);
      if (resultPrompt) {
        message.error('Failed to save content');
      }
    }
  };

  const updateReportMetadata = async () => {
    if (!metadataEditedReportUuid) {
      return;
    }
    setMetadataEditing(true);
    try {
      const updatedObj = metaDataForm.getFieldsValue();
      delete updatedObj.uuid;
      delete updatedObj.id;

      await requestUpdateWorkflowReportMetadata(metadataEditedReportUuid, updatedObj);
      message.success('Metadata updated');
      metaDataForm.resetFields();
      setMetadataEditedReportUuid(null);
    } catch (e) {
      console.error(e);
      message.error('Failed to update metadata');
    }
    setMetadataEditing(false);
  };

  const deleteReport = async (uuid: string | null) => {
    if (!uuid) {
      return;
    }
    setDeleting(true);
    try {
      await requestDeleteWorkflowReport(uuid);
      message.success('Report deleted');
      setReportList(reportList.filter((report) => report.uuid !== uuid));
      setSelectedKey(selectedKey?.startsWith(uuid) ? null : selectedKey);
      setDeletedReportUuid(null);
      setContent(selectedKey?.startsWith(uuid) ? '' : content);
    } catch (e) {
      console.error(e);
      message.error('Failed to delete report');
    }
    setDeleting(false);
  };

  const onDownloadAsPdf = () => {
    const doc = new jsPDF('p', 'mm', 'a4'); // New jsPDF instance: orientation, unit, page size

    const width = doc.internal.pageSize.getWidth();
    const height = doc.internal.pageSize.getHeight();

    html2canvas(document.querySelector('.ql-editor')).then((canvas) => {
      const imgData = canvas.toDataURL('image/png');
      doc.addImage(imgData, 'PNG', 0, 0, width, height);
      doc.save('report.pdf');
    });
  };

  useEffect(() => {
    initReports();
    refreshTimer.current = setInterval(() => {
      loadReports();
    }, 5000);
    return () => {
      if (refreshTimer.current) {
        clearInterval(refreshTimer.current);
      }
    };
  }, [analysisId]);

  useEffect(() => {
    loadReportContent();
  }, [selectedKey]);

  useEffect(() => {
    const reportUuid = new URLSearchParams(location.search).get('report-uuid');
    if (reportUuid) {
      initWithReport(reportUuid);
    }
  }, [location]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'stretch',
        height: '100%',
        justifyContent: 'flex-start',
      }}
    >
      <div
        style={{
          backgroundColor: 'white',
          width: '25%',
        }}
      >
        <ReportList
          loading={listLoading}
          reportList={reportList}
          selectedKey={selectedKey}
          setSelectedKey={setSelectedKey}
          onItemEdit={(reportItem: WorkflowReport) => {
            setMetadataEditedReportUuid(reportItem.uuid);
            metaDataForm.setFieldsValue(reportItem);
          }}
          onItemDelete={(uuid: string) => {
            setDeletedReportUuid(uuid);
          }}
        />
      </div>
      <div
        style={{
          flex: 1,
          height: '100%',
          padding: '2em 1em 0 1em',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-start',
        }}
      >
        <div
          style={{
            paddingBottom: '1px',
          }}
        >
          <CustomQuillToolbar
            onDownloadAsPdf={onDownloadAsPdf}
            onSaveContent={() => {
              saveReportContent(content, true);
            }}
          />
        </div>
        <div
          style={{
            flex: 1,
            width: '100%',
            backgroundColor: 'white',
            position: 'relative',
          }}
          id="editor-container"
        >
          <ReactQuill
            theme="snow"
            ref={editorRef}
            value={content}
            onChange={(value: string) => {
              setContent(value);
              if (contentSaveTimer.current) {
                clearTimeout(contentSaveTimer.current);
              }
              contentSaveTimer.current = setTimeout(() => {
                saveReportContent(value, false);
              }, 4000);
            }}
            bounds={'#editor-container'}
            modules={{
              toolbar: {
                container: '#toolbar',
              },
            }}
          />
          <div
            hidden={!contentLoading}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              display: 'flex',
              paddingTop: '10vh',
              justifyContent: 'center',
              backgroundColor: 'rgba(255,255,255,0.5)',
            }}
          >
            <Spin indicator={<LoadingOutlined spin />} size="large" />
          </div>
        </div>
      </div>
      <div
        style={{
          backgroundColor: 'transparent',
          width: '25%',
        }}
      >
        <RightSider />
      </div>
      <Modal
        centered
        title="Edit Report"
        open={!!metadataEditedReportUuid}
        onCancel={() => {
          metaDataForm.resetFields();
          setMetadataEditedReportUuid(null);
        }}
        okButtonProps={{
          loading: metadataEditing,
        }}
        okText={dictionary.SUBMIT}
        onOk={() => {
          metaDataForm.submit();
        }}
      >
        <Form
          form={metaDataForm}
          labelCol={{ span: 6 }}
          wrapperCol={{ span: 18 }}
          onFinish={updateReportMetadata}
        >
          <Form.Item label="ID" name="report_id">
            <Input disabled />
          </Form.Item>
          <Form.Item label="UUID" name="uuid">
            <Input disabled />
          </Form.Item>
          <Form.Item label="Name" name="report_name">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        centered
        title="Delete Report"
        open={!!deletedReportUuid}
        onCancel={() => {
          setDeletedReportUuid(null);
        }}
        okButtonProps={{
          loading: deleting,
          danger: true,
        }}
        okText={dictionary.DELETE}
        onOk={() => {
          deleteReport(deletedReportUuid);
        }}
      >
        <p>Are you sure to delete this report?</p>
      </Modal>
    </div>
  );
};

export default WorkflowReportPage;
