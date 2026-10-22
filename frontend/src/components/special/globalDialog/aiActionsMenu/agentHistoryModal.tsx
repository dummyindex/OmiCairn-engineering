import { useState } from 'react';
import { Modal, Select, Table } from 'antd';
import { useModel } from 'umi';

const AgentHistoryModal = () => {
  const { agentHistoryInspectedNodeId, setAgentHistoryInspectedNodeId } = useModel('analysis');
  const { dictionary } = useModel('localization');
  const [agentCategory, setAgentCategory] = useState('AUTO_GENIE');

  const agentOptions = [
    { label: dictionary.AUTO_GENIE, value: 'AUTO_GENIE' },
    { label: dictionary.BUG_FIXER, value: 'BUG_FIXER' },
    { label: dictionary.AI_PARAMETER, value: 'AI_PARAMETER' },
    { label: dictionary.AI_INTERPRETATION, value: 'AI_INTERPRETATION' },
  ];

  // useEffect(() => {
  //   if (agentHistoryInspectedNodeId) {
  //     fetchAgentHistory();
  //   }
  // }, [agentHistoryInspectedNodeId]);

  const handleCancel = () => {
    setAgentHistoryInspectedNodeId(null);
  };

  const handleAgentCategoryChange = (value) => {
    setAgentCategory(value);
  };

  return (
    <Modal
      title={<div style={{ textAlign: 'center', width: '100%' }}>{dictionary.AGENT_HISTORY}</div>}
      visible={!!agentHistoryInspectedNodeId}
      onCancel={handleCancel}
      footer={null}
      width={900}
      centered
      bodyStyle={{
        maxHeight: 'calc(90vh - 200px)',
        overflowY: 'auto',
      }}
    >
      <div>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <span>{dictionary.AGENT_CATEGORY}:</span>
            <Select
              value={agentCategory}
              onChange={handleAgentCategoryChange}
              style={{ width: 180 }}
            >
              {agentOptions.map((option) => (
                <Select.Option key={option.value} value={option.value}>
                  {option.label}
                </Select.Option>
              ))}
            </Select>
          </div>
        </div>
        <Table
          columns={null}
          dataSource={[]}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `${dictionary.TOTAL}: ${total} ${dictionary.ITEMS}`,
          }}
          scroll={{ x: 'max-content', y: 'calc(65vh - 200px)' }}
        />
      </div>
    </Modal>
  );
};

export default AgentHistoryModal;
