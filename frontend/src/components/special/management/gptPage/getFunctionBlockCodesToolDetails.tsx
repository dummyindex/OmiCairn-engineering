import { Card, Collapse, Badge, Space, Typography } from 'antd';
import { FileOutlined, CodeOutlined } from '@ant-design/icons';

const { Panel } = Collapse;
const { Text } = Typography;

const GetFunctionBlockCodesToolDetails = ({ subTask }) => {
  if (subTask?.status === 'running') {
    return (
      <Card title="Get Function Block Codes" size="small" style={{ marginBottom: '16px' }}>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
            Status:
          </label>
          <div
            style={{
              padding: '12px',
              background: '#fffbe6',
              border: '1px solid #ffe58f',
              borderRadius: '6px',
              color: '#d48806',
            }}
          >
            Sub Task is running...
          </div>
        </div>
      </Card>
    );
  }

  let subTaskDetails: any = {};
  try {
    subTaskDetails = JSON.parse(subTask.outputs || '{}');
  } catch (error) {
    subTaskDetails = { success: false, message: 'Failed to parse output', code_files: {} };
  }

  // If code_files is missing or parsing fails
  if (!subTaskDetails.code_files || Object.keys(subTaskDetails.code_files).length === 0) {
    return (
      <Card
        title={
          <Space>
            <CodeOutlined style={{ fontSize: '14px' }} />
            <span style={{ fontSize: '14px' }}>Get Function Block Codes</span>
            <Badge
              status={subTaskDetails.success ? 'success' : 'error'}
              text={subTaskDetails.success ? 'Success' : 'Failed'}
            />
          </Space>
        }
        size="small"
        style={{ marginBottom: '16px' }}
      >
        <Text type="secondary" style={{ fontSize: '12px' }}>
          No code files available
        </Text>
      </Card>
    );
  }

  // Get the language type from the file extension
  const getLanguageByExtension = (filename: string): string => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'py':
        return 'python';
      case 'js':
        return 'javascript';
      case 'ts':
        return 'typescript';
      case 'tsx':
        return 'typescript';
      case 'jsx':
        return 'javascript';
      case 'json':
        return 'json';
      case 'sh':
        return 'bash';
      case 'r':
        return 'r';
      case 'sql':
        return 'sql';
      case 'yaml':
      case 'yml':
        return 'yaml';
      case 'xml':
        return 'xml';
      case 'html':
        return 'html';
      case 'css':
        return 'css';
      case 'txt':
        return 'text';
      default:
        return 'text';
    }
  };

  // Get the icon color from the file extension
  const getFileIconColor = (filename: string): string => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'py':
        return '#3776ab';
      case 'js':
      case 'jsx':
        return '#f7df1e';
      case 'ts':
      case 'tsx':
        return '#3178c6';
      case 'json':
        return '#000000';
      case 'sh':
        return '#89e051';
      case 'r':
        return '#276dc3';
      case 'sql':
        return '#336791';
      case 'txt':
        return '#666666';
      default:
        return '#1890ff';
    }
  };

  // Code display component
  const CodeDisplay = ({ content, language }: { content: string; language: string }) => (
    <div
      style={{
        background: '#f6f8fa',
        border: '1px solid #e1e4e8',
        borderRadius: '6px',
        overflow: 'hidden',
        fontSize: '12px',
        fontFamily: '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace',
      }}
    >
      {/* Code header */}
      <div
        style={{
          background: '#f1f3f4',
          padding: '8px 12px',
          borderBottom: '1px solid #e1e4e8',
          fontSize: '11px',
          color: '#586069',
          fontWeight: 'bold',
        }}
      >
        {language.toUpperCase()}
      </div>
      {/* Code content */}
      <pre
        style={{
          margin: 0,
          padding: '12px',
          overflow: 'auto',
          maxHeight: '400px',
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
          lineHeight: '1.4',
          color: '#24292e',
        }}
      >
        <code>{content}</code>
      </pre>
    </div>
  );

  const codeFiles = subTaskDetails.code_files || {};
  const fileCount = Object.keys(codeFiles).length;

  return (
    <div style={{ height: '100%', overflow: 'auto' }} id={subTask?.id}>
      <Card
        title={
          <Space>
            <CodeOutlined style={{ fontSize: '14px' }} />
            <span style={{ fontSize: '14px' }}>Function Block Codes</span>
            <Badge
              status={subTaskDetails.success ? 'success' : 'error'}
              text={subTaskDetails.success ? 'Success' : 'Failed'}
            />
            <Badge count={fileCount} style={{ backgroundColor: '#1890ff' }} />
          </Space>
        }
        size="small"
        bodyStyle={{ padding: '12px' }}
      >
        {fileCount > 0 ? (
          <Collapse size="small" ghost>
            {Object.entries(codeFiles).map(([filename, content]: [string, any], index: number) => {
              const language = getLanguageByExtension(filename);
              const iconColor = getFileIconColor(filename);

              return (
                <Panel
                  header={
                    <Space>
                      <FileOutlined style={{ color: iconColor, fontSize: '12px' }} />
                      <span style={{ fontSize: '12px', fontWeight: 'bold' }}>{filename}</span>
                      <Text type="secondary" style={{ fontSize: '10px' }}>
                        {language.toUpperCase()}
                      </Text>
                      <Text type="secondary" style={{ fontSize: '10px' }}>
                        {typeof content === 'string' ? `${content.length} chars` : 'N/A'}
                      </Text>
                    </Space>
                  }
                  key={index.toString()}
                >
                  <CodeDisplay
                    content={
                      typeof content === 'string' ? content : JSON.stringify(content, null, 2)
                    }
                    language={language}
                  />
                </Panel>
              );
            })}
          </Collapse>
        ) : (
          <Text type="secondary" style={{ fontSize: '12px' }}>
            No code files found
          </Text>
        )}
      </Card>
    </div>
  );
};

export default GetFunctionBlockCodesToolDetails;
