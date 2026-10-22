import {
  Card,
  Descriptions,
  Badge,
  Collapse,
  Space,
  Tag,
  Typography,
  Statistic,
  Row,
  Col,
  Divider,
  Alert,
} from 'antd';
import {
  CalculatorOutlined,
  InfoCircleOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  SettingOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  LinkOutlined,
} from '@ant-design/icons';

const { Panel } = Collapse;
const { Title, Text, Paragraph } = Typography;

const GetComputationDetailsToolDetails = ({ subTask }) => {
  let subTaskDetails: any = {};
  try {
    subTaskDetails = JSON.parse(subTask.outputs || '{}');
  } catch (error) {
    subTaskDetails = {
      success: false,
      message: 'Failed to parse output',
      computation_details: null,
    };
  }

  // If computation_details is missing or parsing fails
  if (!subTaskDetails.computation_details) {
    return (
      <Card
        title={
          <Space>
            <CalculatorOutlined style={{ fontSize: '14px' }} />
            <span style={{ fontSize: '14px' }}>Computation Details</span>
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
          No computation details available
        </Text>
      </Card>
    );
  }

  const { computation_details } = subTaskDetails;
  const basicInfo = computation_details.computation_basic_info || {};
  const logs = computation_details.computation_logs || [];
  const fbInfo = computation_details.function_block_info || {};
  const fbVersionInfo = computation_details.function_block_version_info || {};

  // Status-to-color mapping
  const getStateColor = (state: string) => {
    switch (state?.toLowerCase()) {
      case 'finished':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
      case 'pending':
        return 'processing';
      case 'waiting':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Format the time
  const formatTime = (timestamp: number) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // Format the duration
  const formatDuration = (seconds: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(2)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(2)}s`;
  };

  // Parse the computation parameters
  let computationParams: any = {};
  try {
    computationParams = JSON.parse(basicInfo.computationParams || '{}');
  } catch (error) {
    computationParams = {};
  }

  // Render the parameter table
  const renderParameters = (args: any[]) => {
    if (!args || args.length === 0) return null;

    return (
      <div style={{ marginTop: '12px' }}>
        <Text strong style={{ fontSize: '11px' }}>
          Parameters:
        </Text>
        <div style={{ marginTop: '8px', display: 'grid', gap: '4px' }}>
          {args.slice(0, 6).map((arg: any, index: number) => (
            <div
              key={index}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '4px 8px',
                background: '#f8f9fa',
                borderRadius: '4px',
                fontSize: '10px',
              }}
            >
              <Text strong style={{ fontSize: '10px' }}>
                {arg.name}:
              </Text>
              <Text style={{ fontSize: '10px' }}>
                {arg.default_value !== null ? String(arg.default_value) : 'null'}
              </Text>
            </div>
          ))}
          {args.length > 6 && (
            <Text type="secondary" style={{ fontSize: '10px', textAlign: 'center' }}>
              ...{args.length - 6} more parameters
            </Text>
          )}
        </div>
      </div>
    );
  };

  return (
    <div style={{ height: '100%', overflow: 'auto' }} id={subTask?.id}>
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {/* Main info card */}
        <Card
          title={
            <Space>
              <CalculatorOutlined style={{ fontSize: '14px' }} />
              <span style={{ fontSize: '14px' }}>Computation Details</span>
              <Badge
                status={getStateColor(basicInfo.computationState)}
                text={basicInfo.computationState}
              />
            </Space>
          }
          size="small"
          bodyStyle={{ padding: '12px' }}
        >
          {/* Basic statistics */}
          <Row gutter={[8, 8]}>
            <Col span={6}>
              <Statistic
                title={<span style={{ fontSize: '10px' }}>Computation ID</span>}
                value={basicInfo.id}
                prefix={<CalculatorOutlined style={{ fontSize: '10px' }} />}
                valueStyle={{ fontSize: '14px' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title={<span style={{ fontSize: '10px' }}>Node ID</span>}
                value={basicInfo.nodeId}
                prefix={<DatabaseOutlined style={{ fontSize: '10px' }} />}
                valueStyle={{ fontSize: '14px' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title={<span style={{ fontSize: '10px' }}>Duration</span>}
                value={formatDuration(basicInfo.duration)}
                prefix={<ClockCircleOutlined style={{ fontSize: '10px' }} />}
                valueStyle={{
                  fontSize: '14px',
                  color: basicInfo.computationState === 'failed' ? '#ff4d4f' : '#52c41a',
                }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title={<span style={{ fontSize: '10px' }}>Task ID</span>}
                value={basicInfo.taskId}
                prefix={<ThunderboltOutlined style={{ fontSize: '10px' }} />}
                valueStyle={{ fontSize: '14px' }}
              />
            </Col>
          </Row>

          <Divider style={{ margin: '12px 0' }} />

          {/* Function Block info */}
          <div style={{ marginBottom: '12px' }}>
            <Title level={5} style={{ fontSize: '13px', margin: '0 0 8px 0' }}>
              Function Block: {fbInfo.name || 'N/A'}
            </Title>
            <Space wrap size="small">
              <Tag color="blue" style={{ fontSize: '10px' }}>
                ID: {fbInfo.id}
              </Tag>
              <Tag color="green" style={{ fontSize: '10px' }}>
                Version: {fbVersionInfo.id}
              </Tag>
              <Tag color="purple" style={{ fontSize: '10px' }}>
                Language: {fbVersionInfo.programLanguage}
              </Tag>
              <Tag color="orange" style={{ fontSize: '10px' }}>
                Env: {fbVersionInfo.presetEnv}
              </Tag>
            </Space>
          </div>

          {/* Compute resource configuration */}
          {basicInfo.computationResourceConfigure && (
            <div style={{ marginBottom: '12px' }}>
              <Text strong style={{ fontSize: '11px' }}>
                Resource Configuration:
              </Text>
              <div style={{ marginTop: '6px' }}>
                <Space wrap size="small">
                  <Tag style={{ fontSize: '10px' }}>
                    CPU: {basicInfo.computationResourceConfigure.vcpu} cores
                  </Tag>
                  <Tag style={{ fontSize: '10px' }}>
                    RAM: {basicInfo.computationResourceConfigure.ram}GB
                  </Tag>
                  <Tag style={{ fontSize: '10px' }}>
                    GPU: {basicInfo.computationResourceConfigure.gpu}
                  </Tag>
                  <Tag style={{ fontSize: '10px' }}>
                    Timeout: {basicInfo.computationResourceConfigure.timeout}s
                  </Tag>
                </Space>
              </div>
            </div>
          )}

          {/* Error info */}
          {basicInfo.computationState === 'failed' && basicInfo.optimizedErrorDescription && (
            <Alert
              message={<span style={{ fontSize: '11px' }}>Error Analysis</span>}
              description={
                <div style={{ fontSize: '10px', maxHeight: '200px', overflow: 'auto' }}>
                  <pre
                    style={{
                      whiteSpace: 'pre-wrap',
                      margin: 0,
                      fontFamily: 'monospace',
                      fontSize: '10px',
                    }}
                  >
                    {basicInfo.optimizedErrorDescription}
                  </pre>
                </div>
              }
              type="error"
              showIcon
              style={{ marginBottom: '12px' }}
            />
          )}

          {/* Collapsible details panel */}
          <Collapse size="small" ghost>
            {/* Computation parameters */}
            <Panel
              header={
                <Space>
                  <SettingOutlined style={{ fontSize: '11px' }} />
                  <span style={{ fontSize: '11px' }}>Computation Parameters</span>
                </Space>
              }
              key="params"
            >
              <div style={{ fontSize: '10px' }}>
                <pre
                  style={{
                    background: '#f6f8fa',
                    padding: '8px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    overflow: 'auto',
                    margin: 0,
                  }}
                >
                  {JSON.stringify(computationParams, null, 2)}
                </pre>
              </div>
              {renderParameters(fbVersionInfo.args)}
            </Panel>

            {/* Computation logs */}
            {logs.length > 0 && (
              <Panel
                header={
                  <Space>
                    <FileTextOutlined style={{ fontSize: '11px' }} />
                    <span style={{ fontSize: '11px' }}>Computation Logs ({logs.length})</span>
                  </Space>
                }
                key="logs"
              >
                <div
                  style={{
                    maxHeight: '300px',
                    overflow: 'auto',
                    background: '#f6f8fa',
                    padding: '8px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    fontFamily: 'monospace',
                  }}
                >
                  {logs.map((log: any, index: number) => (
                    <div
                      key={index}
                      style={{
                        marginBottom: '4px',
                        paddingLeft: '8px',
                        borderLeft:
                          log.message.includes('error') || log.message.includes('failed')
                            ? '3px solid #ff4d4f'
                            : '3px solid #52c41a',
                      }}
                    >
                      {log.message}
                    </div>
                  ))}
                </div>
              </Panel>
            )}

            {/* Function Block details */}
            <Panel
              header={
                <Space>
                  <InfoCircleOutlined style={{ fontSize: '11px' }} />
                  <span style={{ fontSize: '11px' }}>Function Block Details</span>
                </Space>
              }
              key="fbinfo"
            >
              <Descriptions
                column={2}
                size="small"
                labelStyle={{ fontSize: '10px' }}
                contentStyle={{ fontSize: '10px' }}
              >
                <Descriptions.Item label="Name">{fbVersionInfo.name}</Descriptions.Item>
                <Descriptions.Item label="Source">{fbVersionInfo.source}</Descriptions.Item>
                <Descriptions.Item label="Created Time">
                  {fbVersionInfo.createdTime}
                </Descriptions.Item>
                <Descriptions.Item label="State">
                  <Badge status={getStateColor(fbVersionInfo.state)} text={fbVersionInfo.state} />
                </Descriptions.Item>
                <Descriptions.Item label="Plot Only">
                  <Tag
                    color={fbVersionInfo.plotOnly ? 'orange' : 'green'}
                    style={{ fontSize: '9px' }}
                  >
                    {fbVersionInfo.plotOnly ? 'Yes' : 'No'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="System Env">{basicInfo.systemEnv}</Descriptions.Item>
              </Descriptions>

              {fbVersionInfo.description && (
                <div style={{ marginTop: '12px' }}>
                  <Text strong style={{ fontSize: '11px' }}>
                    Description:
                  </Text>
                  <Paragraph
                    style={{ fontSize: '10px', marginTop: '6px' }}
                    ellipsis={{ rows: 3, expandable: true }}
                  >
                    {fbVersionInfo.description}
                  </Paragraph>
                </div>
              )}

              {fbVersionInfo.documentUrl && (
                <div style={{ marginTop: '8px' }}>
                  <Text strong style={{ fontSize: '11px' }}>
                    Documentation:{' '}
                  </Text>
                  <a
                    href={fbVersionInfo.documentUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontSize: '10px' }}
                  >
                    <LinkOutlined style={{ fontSize: '10px', marginRight: '4px' }} />
                    View Docs
                  </a>
                </div>
              )}
            </Panel>

            {/* Basic info */}
            <Panel
              header={
                <Space>
                  <InfoCircleOutlined style={{ fontSize: '11px' }} />
                  <span style={{ fontSize: '11px' }}>Basic Information</span>
                </Space>
              }
              key="basic"
            >
              <Descriptions
                column={2}
                size="small"
                labelStyle={{ fontSize: '10px' }}
                contentStyle={{ fontSize: '10px' }}
              >
                <Descriptions.Item label="Start Time">
                  {formatTime(basicInfo.startTime)}
                </Descriptions.Item>
                <Descriptions.Item label="Created Time">
                  {formatTime(basicInfo.createdTime)}
                </Descriptions.Item>
                <Descriptions.Item label="Source Data IDs">
                  {basicInfo.sourceDataIds?.join(', ') || 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Result Data ID">
                  {basicInfo.resultDataId}
                </Descriptions.Item>
                <Descriptions.Item label="Function Block ID">
                  {basicInfo.functionBlockId}
                </Descriptions.Item>
                <Descriptions.Item label="Version ID">
                  {basicInfo.functionBlockVersionId}
                </Descriptions.Item>
              </Descriptions>
            </Panel>
          </Collapse>
        </Card>
      </Space>
    </div>
  );
};

export default GetComputationDetailsToolDetails;
