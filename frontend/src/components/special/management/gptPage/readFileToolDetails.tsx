import { InfoCircleOutlined } from '@ant-design/icons';
import { Card, Typography } from 'antd';

const { Text } = Typography;

const ReadFileToolDetails = ({ subTask }: any) => {
  const toolParams = subTask?.toolParams || '';
  const outputs = subTask?.outputs || {};

  const extractFileName = (toolParams: any) => {
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
      console.error('extractFileName parse error:', error);
      return null;
    }
  };

  const extractFileInfo = (outputsString: string) => {
    try {
      const outputs = typeof outputsString === 'string' ? JSON.parse(outputsString) : outputsString;

      if (outputs.success && outputs.content) {
        return {
          file_type: outputs.file_type,
        };
      }
      return null;
    } catch (error) {
      return null;
    }
  };

  const fileName = extractFileName(toolParams);
  const fileInfo = extractFileInfo(outputs);

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: '20px 0' }}>
      <Card title="Read File" size="small">
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>
                File ID
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
                {fileName || 'N/A'}
              </div>
            </div>
          </div>
        </div>

        {fileInfo && (
          <div style={{ marginBottom: '16px' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
              }}
            >
              <div>
                <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>
                  File Type
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
                  {fileInfo.file_type || 'N/A'}
                </div>
              </div>
            </div>
          </div>
        )}

        {!fileInfo && (
          <div style={{ textAlign: 'center', padding: '20px 0', color: '#999' }}>
            <InfoCircleOutlined style={{ fontSize: '24px', marginBottom: '12px' }} />
            <div>No file information available yet.</div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default ReadFileToolDetails;
