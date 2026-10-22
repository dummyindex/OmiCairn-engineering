import { LoadingOutlined } from '@ant-design/icons';
import { Card, Spin } from 'antd';
import { useModel } from 'umi';

const PlanAutoGenieToolDetails = ({ subTask }: any) => {
  const { dictionary } = useModel('localization');
  if (subTask.status === 'running') {
    return (
      <div style={{ height: '100%', overflow: 'auto' }}>
        <Card title="Plan Auto Genie" size="small" style={{ marginBottom: '16px' }}>
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin
              indicator={
                <LoadingOutlined
                  style={{
                    fontSize: 24,
                  }}
                  spin
                />
              }
            />
            <div style={{ marginTop: '12px', color: '#666', fontSize: '12px' }}>
              Planning in progress...
            </div>
          </div>
        </Card>
      </div>
    );
  }
  let subTaskDetails = {};
  try {
    subTaskDetails = JSON.parse(subTask.outputs || '{}');
  } catch (error) {
    subTaskDetails = {
      success: false,
      message: 'Error parsing subtask details',
      system_task_id: 'N/A',
      plan: 'N/A',
    };
  }
  const { success, message, plan } = subTaskDetails;
  if (!success) {
    return (
      <div style={{ height: '100%', overflow: 'auto' }}>
        <Card title="Plan Auto Genie" size="small" style={{ marginBottom: '16px' }}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
              {dictionary.TASK_STATUS}
            </label>
            <div
              style={{
                padding: '12px',
                background: '#fff1f0',
                border: '1px solid #ffa39e',
                borderRadius: '6px',
                color: '#cf1322',
              }}
            >
              {message || 'Task creation failed'}
            </div>
          </div>
        </Card>
      </div>
    );
  }
  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <Card title="Plan Auto Genie" size="small" style={{ marginBottom: '16px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
            Plan Name:
          </label>
          <div
            style={{
              padding: '12px',
              background: '#fffbe6',
              border: '1px solid #ffe58f',
              borderRadius: '6px',
              fontSize: '12px',
              lineHeight: '1.6',
              whiteSpace: 'pre-wrap',
            }}
          >
            {plan.name || 'No plan generated'}
          </div>
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
            Plan Steps:
          </label>
          <div
            style={{
              padding: '12px',
              background: '#fffbe6',
              border: '1px solid #ffe58f',
              borderRadius: '6px',
              fontSize: '12px',
              lineHeight: '1.6',
              whiteSpace: 'pre-wrap',
            }}
          >
            {plan.steps || 'No plan generated'}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default PlanAutoGenieToolDetails;
