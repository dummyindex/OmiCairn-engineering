import DynamicGenerationTaskCard from '@/components/common/dynamicGenerationTaskCard';
import { requestGetDynamicGeneration } from '@/request/node';
import { Card } from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';

const RunAutoGenieToolDetails = ({ subTask }: any) => {
  const { systemTaskId } = subTask;
  const { dictionary } = useModel('localization');

  const [dynamicGeneration, setDynamicGeneration] = useState<any>(null);

  useEffect(() => {
    const loadDynamicGeneration = async () => {
      if (systemTaskId) {
        const { data: dynamicGeneration } = await requestGetDynamicGeneration(systemTaskId);
        console.log('Fetched Dynamic Generation:', dynamicGeneration);
        setDynamicGeneration(dynamicGeneration);
      }
    };
    loadDynamicGeneration();
  }, [systemTaskId]);

  if (!systemTaskId) {
    return (
      <div style={{ height: '100%', overflow: 'auto' }}>
        <Card title="Run Auto Genie" size="small" style={{ marginBottom: '16px' }}>
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
              Task creation failed, missing system task ID
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', overflow: 'auto' }} id={subTask?.id}>
      {!dynamicGeneration ? (
        <div>Loading...</div>
      ) : (
        <DynamicGenerationTaskCard task={dynamicGeneration} />
      )}
    </div>
  );
};

export default RunAutoGenieToolDetails;
