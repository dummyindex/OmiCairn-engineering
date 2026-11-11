import { Card } from 'antd';

const OtherToolDetails = ({ subTask }: any) => {
  return (
    <div style={{ height: '100%', overflow: 'auto' }} id={subTask?.id}>
      <Card title="Tool Calling" size="small" style={{ marginBottom: '16px' }}>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
            Tool Name: {subTask['toolName'] || 'N/A'}
          </label>
          <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.4' }}>
            Parameters: {JSON.stringify(subTask['toolParams']) || 'N/A'} <br />
            Results: {JSON.stringify(subTask['outputs']) || 'N/A'} <br />
          </div>
        </div>
        <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.4' }}>
          Start Time: {subTask?.startTime || 'N/A'} <br />
          End Time: {subTask?.endTime || 'N/A'} <br />
          Status: {subTask?.status || 'N/A'} <br />
        </div>
      </Card>
    </div>
  );
};

export default OtherToolDetails;
