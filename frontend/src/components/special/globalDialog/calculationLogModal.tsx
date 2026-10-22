import { useEffect, useState } from 'react';
import { Modal, Table, Button } from 'antd';
import { ExportOutlined } from '@ant-design/icons';
import { CSVLink } from 'react-csv';
import { requestLatestComputation, requestComputationGetLogs } from '@/request/computation';
import { formatTimeTool } from '@/util/formatTimeTool';
import { useModel } from 'umi';

const CalculationLogModal = () => {
  const { calcuLogInspectedNodeId, setCalcuLogInspectedNodeId } = useModel('analysis');
  const { dictionary } = useModel('localization');

  const [datasource, setDatasource] = useState<any>([]);
  const [loading, setLoading] = useState(false);

  const column = [
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
    // {
    //   title: 'ptr',
    //   dataIndex: 'ptr',
    //   key: 'ptr',
    //   width: 200,
    //   onCell: () => {
    //     return {
    //       style: {
    //         // whiteSpace: 'nowrap',
    //         maxWidth: 200,
    //         // textOverflow: 'ellipsis',
    //         // overflow: 'hidden',
    //       },
    //     };
    //   },
    // },
  ];

  const refreshLog = async () => {
    if (!calcuLogInspectedNodeId) {
      setDatasource([]);
      return;
    }
    console.log('refresh log:', calcuLogInspectedNodeId);
    setLoading(true);
    const { data: latestComputation } = await requestLatestComputation(
      calcuLogInspectedNodeId + '',
    );
    if (latestComputation) {
      const result = await requestComputationGetLogs(latestComputation.id);
      if (result.data !== null && result.data.length !== 0) {
        const datasource = result.data.map((item, index) => {
          return {
            key: index,
            timestamp: formatTimeTool(item.timestamp),
            message: item.message,
          };
        });
        setDatasource(datasource);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    refreshLog();
  }, [calcuLogInspectedNodeId]);

  const handleCancelMethod = () => {
    setCalcuLogInspectedNodeId(null);
  };
  const handleExportCsvFile = () => {
    const data: any = [];
    const header = column.map((item) => {
      return item.title;
    });
    data.push(header);
    for (let i = 0; i < datasource.length; i++) {
      const dataItem = [datasource[i].timestamp, datasource[i].message];
      data.push(dataItem);
    }
    return data;
  };
  return (
    <Modal
      title={dictionary.CALCULATION_LOG}
      open={calcuLogInspectedNodeId !== null}
      onCancel={handleCancelMethod}
      centered
      width="1000px"
      footer={[
        <Button key="export" type="primary" disabled={datasource.length === 0}>
          <CSVLink
            data={handleExportCsvFile()}
            filename={'calculationLog.csv'}
            style={
              datasource.length === 0
                ? { color: 'rgba(0, 0, 0, 0.25)', cursor: 'not-allowed' }
                : { color: 'white' }
            }
          >
            <ExportOutlined style={{ marginRight: '3px' }} />
            {dictionary.EXPORT}
          </CSVLink>
        </Button>,
        <Button key="success" onClick={handleCancelMethod}>
          {dictionary.CLOSE}
        </Button>,
      ]}
    >
      <Table
        dataSource={datasource}
        columns={column}
        loading={loading}
        pagination={false}
        size="small"
        expandable={{
          expandedRowRender: (record) => (
            <p
              style={{
                margin: 0,
                maxWidth: '915px',
              }}
            >
              {record.message}
            </p>
          ),
          rowExpandable: () => true,
        }}
        scroll={{
          y: 380,
        }}
        // style={{ maxHeight: '380px', overflow: 'auto' }}
      />
    </Modal>
  );
};

export default CalculationLogModal;
