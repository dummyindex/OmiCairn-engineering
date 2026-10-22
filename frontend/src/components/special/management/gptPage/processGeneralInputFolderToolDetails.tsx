import { InfoCircleOutlined } from '@ant-design/icons';
import { Card, Typography } from 'antd';

const { Text } = Typography;

const ProcessGeneralInputFolderToolDetails = ({ subTask }: any) => {
  const toolParams = subTask?.toolParams || '';
  const outputs = subTask?.outputs || {};

  const extractFolderName = (toolParams: any) => {
    try {
      const params =
        typeof toolParams === 'string' && toolParams.trim() ? JSON.parse(toolParams) : toolParams;
      const fileKey = params && (params.file_key || params.fileKey || '');

      if (fileKey && typeof fileKey === 'string') {
        const parts = fileKey.split('/');
        return parts.length ? parts[parts.length - 1] : null;
      }
      return null;
    } catch (error) {
      console.error('extractFolderName parse error:', error);
      return null;
    }
  };

  const extractProcessInfo = (outputsString: string) => {
    try {
      const outputs = typeof outputsString === 'string' ? JSON.parse(outputsString) : outputsString;

      return {
        status: outputs.status,
        message: outputs.message,
        data_frame_id: outputs.data_frame_id,
      };
    } catch (error) {
      return null;
    }
  };

  const folderName = extractFolderName(toolParams);
  const processInfo = extractProcessInfo(outputs);

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: '20px 0' }}>
      <Card title="General Input Folder Processing" size="small">
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>
                Folder Name
              </Text>
              <div
                style={{
                  marginTop: '4px',
                  padding: '6px 8px',
                  backgroundColor: '#f0f7ff',
                  borderRadius: '4px',
                  fontSize: '12px',
                  color: '#1890ff',
                  fontFamily: 'monospace',
                  border: '1px solid #d6e4ff',
                }}
              >
                {folderName || 'N/A'}
              </div>
            </div>

            {processInfo?.status && (
              <div>
                <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>
                  Status
                </Text>
                <div
                  style={{
                    marginTop: '4px',
                    padding: '6px 8px',
                    backgroundColor: processInfo.status === 'success' ? '#f6ffed' : '#fff2f0',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: processInfo.status === 'success' ? '#52c41a' : '#ff4d4f',
                    fontFamily: 'monospace',
                    border: `1px solid ${processInfo.status === 'success' ? '#b7eb8f' : '#ffccc7'}`,
                  }}
                >
                  {processInfo.status}
                </div>
              </div>
            )}
          </div>
        </div>

        {processInfo?.data_frame_id && (
          <div style={{ marginBottom: '16px' }}>
            <div>
              <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>
                Data Frame ID
              </Text>
              <div
                style={{
                  marginTop: '4px',
                  padding: '6px 8px',
                  backgroundColor: '#f0f7ff',
                  borderRadius: '4px',
                  fontSize: '12px',
                  color: '#1890ff',
                  fontFamily: 'monospace',
                  border: '1px solid #d6e4ff',
                }}
              >
                {processInfo.data_frame_id}
              </div>
            </div>
          </div>
        )}

        {processInfo?.message && (
          <div style={{ marginBottom: '16px' }}>
            <div>
              <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>
                Message
              </Text>
              <div
                style={{
                  marginTop: '4px',
                  padding: '8px',
                  backgroundColor: '#f9f9f9',
                  borderRadius: '4px',
                  fontSize: '12px',
                  color: '#666',
                  border: '1px solid #e8e8e8',
                  lineHeight: '1.4',
                }}
              >
                {processInfo.message}
              </div>
            </div>
          </div>
        )}

        {!processInfo && (
          <div style={{ textAlign: 'center', padding: '20px 0', color: '#999' }}>
            <InfoCircleOutlined style={{ fontSize: '24px', marginBottom: '12px' }} />
            <div>No processing information available yet.</div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default ProcessGeneralInputFolderToolDetails;
