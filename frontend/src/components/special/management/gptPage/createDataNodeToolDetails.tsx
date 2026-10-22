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
} from 'antd';
import {
  DatabaseOutlined,
  NodeIndexOutlined,
  InfoCircleOutlined,
  FileTextOutlined,
  BarChartOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons';

const { Panel } = Collapse;
const { Title, Text, Paragraph } = Typography;

const CreateDataNodeToolDetails = ({ subTask }) => {
  let subTaskDetails: any = {};
  try {
    subTaskDetails = JSON.parse(subTask.outputs || '{}');
  } catch (error) {
    subTaskDetails = { analysis: null, nodes: [], edges: [] };
  }

  // If there is no data, show the original simple card
  if (!subTaskDetails.data_info || !subTaskDetails.new_data_node_info) {
    return (
      <div style={{ height: '100%', overflow: 'auto' }} id={subTask?.id}>
        <Card title="Create Data Node" size="small" style={{ marginBottom: '16px' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            No detailed information available
          </Text>
        </Card>
      </div>
    );
  }

  const { data_info, new_data_node_info } = subTaskDetails;

  // Parse the description
  let parsedDescription: any = {};
  try {
    parsedDescription = JSON.parse(data_info.description || '{}');
  } catch (error) {
    parsedDescription = {};
  }

  // Parse the summary
  let parsedSummary: any = {};
  try {
    parsedSummary = JSON.parse(data_info.summary || '{}');
  } catch (error) {
    parsedSummary = {};
  }

  // Status-to-color mapping
  const getStateColor = (state: string) => {
    switch (state) {
      case 'ok':
        return 'success';
      case 'original':
        return 'processing';
      case 'error':
        return 'error';
      case 'running':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Format the time
  const formatTime = (timestamp: number) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString('en-US', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div style={{ height: '100%', overflow: 'auto' }} id={subTask?.id}>
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {/* Main info card */}
        <Card
          title={
            <Space>
              <DatabaseOutlined style={{ fontSize: '12px' }} />
              <span style={{ fontSize: '12px' }}>Data Node Created</span>
              <Badge status={getStateColor(data_info.state)} text={data_info.state} />
            </Space>
          }
          size="small"
          bodyStyle={{ padding: '10px' }}
        >
          <Row gutter={[8, 8]}>
            <Col span={8}>
              <Statistic
                title={<span style={{ fontSize: '10px' }}>Data ID</span>}
                value={data_info.id}
                prefix={<DatabaseOutlined style={{ fontSize: '10px' }} />}
                valueStyle={{ fontSize: '14px' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title={<span style={{ fontSize: '10px' }}>Node ID</span>}
                value={new_data_node_info.id}
                prefix={<NodeIndexOutlined style={{ fontSize: '10px' }} />}
                valueStyle={{ fontSize: '14px' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title={<span style={{ fontSize: '10px' }}>Analysis ID</span>}
                value={new_data_node_info.analysisId}
                valueStyle={{ fontSize: '14px' }}
              />
            </Col>
          </Row>

          <Divider style={{ margin: '10px 0' }} />

          <Title level={5} style={{ fontSize: '13px', margin: '0 0 6px 0' }}>
            {data_info.name}
          </Title>

          {parsedDescription.data_description && (
            <Paragraph
              ellipsis={{ rows: 2, expandable: true }}
              style={{ fontSize: '11px', margin: '0 0 8px 0' }}
            >
              <Text type="secondary" style={{ fontSize: '11px' }}>
                {parsedDescription.data_description}
              </Text>
            </Paragraph>
          )}

          <Space wrap size="small">
            <Tag
              color="blue"
              icon={<FileTextOutlined />}
              style={{ fontSize: '10px', padding: '2px 6px' }}
            >
              {data_info.uploadType}
            </Tag>
            <Tag
              color="green"
              icon={<CloudUploadOutlined />}
              style={{ fontSize: '10px', padding: '2px 6px' }}
            >
              {data_info.createdFrom}
            </Tag>
            {parsedDescription.conformity_degree && (
              <Tag color="purple" style={{ fontSize: '10px', padding: '2px 6px' }}>
                Conformity: {parsedDescription.conformity_degree}
              </Tag>
            )}
            <Tag
              color={new_data_node_info.locked ? 'red' : 'green'}
              style={{ fontSize: '10px', padding: '2px 6px' }}
            >
              {new_data_node_info.locked ? 'Locked' : 'Unlocked'}
            </Tag>
          </Space>

          {/* Collapsible details panel */}
          <Collapse size="small" style={{ marginTop: '10px' }}>
            {/* Data statistics */}
            {parsedSummary.sparsity && (
              <Panel
                header={
                  <Space>
                    <BarChartOutlined style={{ fontSize: '11px' }} />
                    <span style={{ fontSize: '11px' }}>Data Statistics</span>
                  </Space>
                }
                key="stats"
              >
                <Row gutter={[8, 8]}>
                  <Col span={6}>
                    <Statistic
                      title={<span style={{ fontSize: '10px' }}>Sparsity</span>}
                      value={(parsedSummary.sparsity * 100).toFixed(1)}
                      suffix="%"
                      valueStyle={{ color: '#1890ff', fontSize: '12px' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title={<span style={{ fontSize: '10px' }}>Species</span>}
                      value={data_info.species}
                      valueStyle={{ color: '#1890ff', fontSize: '12px' }}
                    />
                  </Col>
                </Row>
                <Row gutter={[8, 8]} style={{ marginTop: '12px' }}>
                  {parsedSummary.gene_name_sample && (
                    <div style={{ marginBottom: '8px' }}>
                      <Text style={{ fontSize: '10px' }}>Gene samples (First 6):</Text>
                      <div style={{ marginTop: '4px' }}>
                        <Space wrap size="small">
                          {parsedSummary.gene_name_sample
                            .slice(0, 6)
                            .map((gene: string, index: number) => (
                              <Tag
                                key={index}
                                color="blue"
                                style={{ fontSize: '9px', padding: '1px 4px' }}
                              >
                                {gene}
                              </Tag>
                            ))}
                          {parsedSummary.gene_name_sample.length > 6 && (
                            <Tag style={{ fontSize: '9px', padding: '1px 4px' }}>
                              +{parsedSummary.gene_name_sample.length - 6}
                            </Tag>
                          )}
                        </Space>
                      </div>
                    </div>
                  )}

                  {parsedSummary.cell_name_sample && (
                    <div>
                      <Text style={{ fontSize: '10px' }}>Cell samples (First 3):</Text>
                      <div style={{ marginTop: '4px' }}>
                        <Space wrap size="small">
                          {parsedSummary.cell_name_sample
                            .slice(0, 3)
                            .map((cell: string, index: number) => (
                              <Tag
                                key={index}
                                color="green"
                                style={{ fontSize: '9px', padding: '1px 4px' }}
                              >
                                {cell}
                              </Tag>
                            ))}
                          {parsedSummary.cell_name_sample.length > 3 && (
                            <Tag style={{ fontSize: '9px', padding: '1px 4px' }}>
                              +{parsedSummary.cell_name_sample.length - 3}
                            </Tag>
                          )}
                        </Space>
                      </div>
                    </div>
                  )}
                </Row>
              </Panel>
            )}

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
                <Descriptions.Item label="Data Status">
                  <Badge
                    status={getStateColor(data_info.state)}
                    text={<span style={{ fontSize: '10px' }}>{data_info.state}</span>}
                  />
                </Descriptions.Item>
                <Descriptions.Item label="Node Status">
                  <Badge
                    status={getStateColor(new_data_node_info.state)}
                    text={<span style={{ fontSize: '10px' }}>{new_data_node_info.state}</span>}
                  />
                </Descriptions.Item>
                <Descriptions.Item label="Data Creation Time">
                  {formatTime(data_info.createdTime)}
                </Descriptions.Item>
                <Descriptions.Item label="Node Creation Time">
                  {formatTime(new_data_node_info.createdTime)}
                </Descriptions.Item>
                <Descriptions.Item label="Data Description">
                  {data_info.description || 'No description available'}
                </Descriptions.Item>
              </Descriptions>
            </Panel>
          </Collapse>
        </Card>
      </Space>
    </div>
  );
};

export default CreateDataNodeToolDetails;
