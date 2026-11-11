import { Card } from 'antd';

const ChangeNodeToolDetails = ({ subTask }: any) => {
  let node = {};
  try {
    const subTaskDetails = JSON.parse(subTask.outputs || '{}');
    node = subTaskDetails?.node_info || {};
  } catch (error) {
    node = {};
  }
  return (
    <div style={{ height: '100%', overflow: 'auto' }} id={subTask?.id}>
      <Card title="Focus on Node" size="small" style={{ marginBottom: '16px' }}>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
            Focus on Node : {node['name'] || 'N/A'}
          </label>
          <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.4' }}>
            Node ID: {node['id'] || 'N/A'} <br />
            Function Block ID: {node['functionBlockId'] || 'N/A'} <br />
            Function Block Version ID: {node['functionBlockVersionId'] || 'N/A'} <br />
            State: {node['state'] || 'N/A'} <br />
            Created Time: {node['createdTime'] || 'N/A'} <br />
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ChangeNodeToolDetails;
