import { useEffect, useState } from 'react';
import { Modal, Form, Table, Button, Tooltip, Tabs } from 'antd';
import { ExportOutlined } from '@ant-design/icons';
import { CSVLink } from 'react-csv';
import {
  requestLatestComputation,
  requestComputationGetSummary,
  requestComputationGetLogs,
} from '@/request/computation';
import { formatTimeTool } from '@/util/formatTimeTool';
import { useModel } from 'umi';

const JobDetailsModal = () => {
  const { jobDetailsInspectedNodeId, setJobDetailsInspectedNodeId } = useModel('analysis');
  const { dictionary } = useModel('localization');

  const [jobInfoData, setJobInfoData] = useState<any>({});
  const [jobInfoTableSource, setJobInfoTableSource] = useState<any>([]);
  const [calcLogTableSource, setCalcLogTableSource] = useState<any>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('jobInfo');

  const jobInfoColumns = [
    {
      title: 'name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <Tooltip title={text}>
          <div
            style={{
              maxWidth: '200px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {text}
          </div>
        </Tooltip>
      ),
      width: '30%',
    },
    {
      title: 'duration(seconds)',
      dataIndex: 'length',
      key: 'length',
      width: '20%',
    },
    {
      title: 'start',
      dataIndex: 'start',
      key: 'start',
      width: '25%',
    },
    {
      title: 'end',
      dataIndex: 'end',
      key: 'end',
      width: '25%',
    },
  ];

  const logColumns = [
    {
      title: 'timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 80,
    },
    {
      title: 'message',
      dataIndex: 'message',
      key: 'message',
      width: 300,
      textWrap: 'word-break',
      onCell: () => {
        return {
          style: {
            maxWidth: 300,
            whiteSpace: 'nowrap',
            textOverflow: 'ellipsis',
            overflow: 'hidden',
          },
        };
      },
    },
  ];

  const refreshData = async () => {
    if (!jobDetailsInspectedNodeId) {
      setJobInfoData({});
      setCalcLogTableSource([]);
      return;
    }

    setLoading(true);

    try {
      const { data: latestComputation } = await requestLatestComputation(
        jobDetailsInspectedNodeId + '',
      );

      if (latestComputation) {
        const jobInfoResult = await requestComputationGetSummary(latestComputation.id);
        setJobInfoData(jobInfoResult.data);
        const tableSource =
          jobInfoResult.data.timepiece_reports &&
          jobInfoResult.data.timepiece_reports.map((item, index) => ({
            ...item,
            key: index,
          }));
        setJobInfoTableSource(tableSource);

        const calcLogResult = await requestComputationGetLogs(latestComputation.id);
        if (calcLogResult.data && calcLogResult.data.length !== 0) {
          const calcLogData = calcLogResult.data.map((item, index) => ({
            key: index,
            timestamp: formatTimeTool(item.timestamp),
            message: item.message,
          }));
          setCalcLogTableSource(calcLogData);
        }
      }
    } catch (error) {
      console.error('Failed to fetch data', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, [jobDetailsInspectedNodeId]);

  const handleClose = () => {
    setJobDetailsInspectedNodeId(null);
  };

  const handleExportCsvFile = () => {
    const data: any = [];
    const header = logColumns.map((item) => item.title);
    data.push(header);
    calcLogTableSource.forEach((log) => {
      data.push([log.timestamp, log.message]);
    });
    return data;
  };

  const items = [
    {
      key: 'jobInfo',
      label: dictionary.JOB_INFO,
      children: (
        <Form name="jobInfo" labelCol={{ span: 4 }} wrapperCol={{ span: 20 }}>
          <Form.Item label="duration">
            {jobInfoData && Number(jobInfoData.duration).toFixed(2) + ' s'}
          </Form.Item>
          <Form.Item label="successful">
            {jobInfoData && jobInfoData.successful ? 'true' : 'false'}
          </Form.Item>
          <Form.Item label="error_description">
            {jobInfoData && jobInfoData.error_description ? jobInfoData.error_description : 'null'}
          </Form.Item>
          <Form.Item label="timepiece_reports">
            <Table
              dataSource={jobInfoTableSource}
              columns={jobInfoColumns}
              loading={loading}
              pagination={false}
              size="small"
              scroll={{ y: 240 }}
            />
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'calculationLog',
      label: dictionary.CALCULATION_LOG,
      children: (
        <Table
          dataSource={calcLogTableSource}
          columns={logColumns}
          loading={loading}
          pagination={false}
          size="small"
          expandable={{
            expandedRowRender: (record) => (
              <p style={{ margin: 0, maxWidth: '915px' }}>{record.message}</p>
            ),
            rowExpandable: () => true,
          }}
          scroll={{ y: 380 }}
        />
      ),
    },
  ];

  const getFooterButtons = () => {
    const closeButton = (
      <Button key="close" onClick={handleClose}>
        {dictionary.CLOSE}
      </Button>
    );

    if (activeTab === 'calculationLog') {
      return [
        <Button key="export" type="primary" disabled={calcLogTableSource.length === 0}>
          <CSVLink
            data={handleExportCsvFile()}
            filename={'calculationLog.csv'}
            style={
              calcLogTableSource.length === 0
                ? { color: 'rgba(0, 0, 0, 0.25)', cursor: 'not-allowed' }
                : { color: 'white' }
            }
          >
            <ExportOutlined style={{ marginRight: '3px' }} />
            {dictionary.EXPORT}
          </CSVLink>
        </Button>,
        closeButton,
      ];
    }

    return [closeButton];
  };

  return (
    <Modal
      open={!!jobDetailsInspectedNodeId}
      title={dictionary.JOB_DETAILS}
      onCancel={handleClose}
      centered
      width="1000px"
      footer={getFooterButtons()}
    >
      <Tabs items={items} onChange={(activeKey) => setActiveTab(activeKey)} />
    </Modal>
  );
};

export default JobDetailsModal;
