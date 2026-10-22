import { useEffect, useState } from 'react';
import { Modal, Form, Table, Button, Tooltip } from 'antd';
import { requestLatestComputation, requestComputationGetSummary } from '@/request/computation';
import { useModel } from 'umi';

const JobInfoModal = () => {
  const { jobInfoInspectedNodeId, setJobInfoInspectedNodeId } = useModel('analysis');
  const { dictionary } = useModel('localization');

  const [datasource, setDatasource] = useState<any>({});
  const [tableSource, setTableSource] = useState<any>([]);
  const [loading, setLoading] = useState(false);

  const columns = [
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

  const refreshJoinInfo = async () => {
    if (!jobInfoInspectedNodeId) {
      setDatasource({});
      return;
    }

    setLoading(true);

    try {
      const { data: latestComputation } = await requestLatestComputation(
        jobInfoInspectedNodeId + '',
      );
      if (latestComputation) {
        const result = await requestComputationGetSummary(latestComputation.id);
        setDatasource(result.data);
        const tableSource =
          result.data.timepiece_reports &&
          result.data.timepiece_reports.map((item, index) => {
            return {
              ...item,
              key: index,
            };
          });
        setTableSource(tableSource);
      }
    } catch (error) {
      console.error('Failed to fetch data', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshJoinInfo();
  }, [jobInfoInspectedNodeId]);

  const handleCancelMethod = () => {
    setJobInfoInspectedNodeId(null);
  };

  return (
    <Modal
      open={!!jobInfoInspectedNodeId}
      title={dictionary.JOB_INFO}
      onCancel={handleCancelMethod}
      centered
      width="50vw"
      style={{ minWidth: '840px' }}
      footer={[
        <Button key="close" onClick={handleCancelMethod}>
          {dictionary.CLOSE}
        </Button>,
      ]}
    >
      <Form
        name="jobInfo"
        labelCol={{
          span: 4,
        }}
        wrapperCol={{
          span: 20,
        }}
      >
        <Form.Item label="duration">
          {datasource && Number(datasource.duration).toFixed(2) + ' s'}
        </Form.Item>
        <Form.Item label="successful">
          {datasource && datasource.successful ? 'true' : 'false'}
        </Form.Item>
        <Form.Item label="error_description">
          {datasource && datasource.error_description ? datasource.error_description : 'null'}
        </Form.Item>
        <Form.Item label="timepiece_reports">
          <Table
            columns={columns}
            loading={loading}
            dataSource={tableSource}
            pagination={false}
            size="small"
            scroll={{
              y: 240,
            }}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default JobInfoModal;
