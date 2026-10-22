import {
  CaretDownOutlined,
  CaretRightOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Card, Collapse, Tag, Typography } from 'antd';

const { Panel } = Collapse;
const { Text } = Typography;

const GetAnalysisInfoToolDetails = ({ subTask }: any) => {
  let subTaskDetails = {};
  try {
    subTaskDetails = JSON.parse(subTask.outputs || '{}');
    subTaskDetails['analysis'] = subTaskDetails['analysis-info'];
  } catch (error) {
    subTaskDetails = { analysis: null, nodes: [], edges: [] };
  }
  const analysis = subTaskDetails['analysis'];
  const nodeList = subTaskDetails['nodes'] || [];

  const formatDateTime = (timestamp: string | number) => {
    if (!timestamp) return 'N/A';
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return 'N/A';
    }
  };

  const getStateColor = (state: string) => {
    switch (state?.toLowerCase()) {
      case 'finished':
        return 'success';
      case 'running':
        return 'running';
      case 'failed':
        return 'error';
      case 'pending':
      case 'waiting':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: '20px 0' }}>
      <Card title="Analysis Info" size="small">
        {analysis ? (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>
                  <UserOutlined style={{ marginRight: '4px' }} />
                  ID
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
                  }}
                >
                  {analysis.id || 'N/A'}
                </div>
              </div>
              <div>
                <Text strong style={{ color: '#52c41a', fontSize: '12px' }}>
                  <ClockCircleOutlined style={{ marginRight: '4px' }} />
                  Created Time
                </Text>
                <div
                  style={{
                    marginTop: '4px',
                    padding: '6px 8px',
                    backgroundColor: '#f6ffed',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: '#52c41a',
                  }}
                >
                  {formatDateTime(analysis.created_time)}
                </div>
              </div>
            </div>
            <div style={{ marginTop: '12px' }}>
              <Text strong style={{ color: '#722ed1', fontSize: '12px' }}>
                <FileTextOutlined style={{ marginRight: '4px' }} />
                Name
              </Text>
              <div
                style={{
                  marginTop: '4px',
                  padding: '8px 12px',
                  backgroundColor: '#f9f0ff',
                  borderRadius: '6px',
                  fontSize: '13px',
                  color: '#722ed1',
                  fontWeight: '500',
                  border: '1px solid #d3adf7',
                }}
              >
                {analysis.name || 'Unnamed Analysis'}
              </div>
            </div>
          </div>
        ) : (
          <div
            style={{
              textAlign: 'center',
              color: '#999',
              padding: '20px',
              fontSize: '12px',
            }}
          >
            No analysis information available
          </div>
        )}

        {nodeList.length > 0 && (
          <Collapse
            size="small"
            ghost
            expandIcon={({ isActive }) =>
              isActive ? (
                <CaretDownOutlined style={{ color: '#1890ff' }} />
              ) : (
                <CaretRightOutlined style={{ color: '#1890ff' }} />
              )
            }
            style={{
              backgroundColor: '#fafafa',
              borderRadius: '6px',
              border: '1px solid #e8e8e8',
            }}
          >
            <Panel
              header={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Text strong style={{ color: '#1890ff', fontSize: '13px' }}>
                    Node List
                  </Text>
                  <Tag color="blue" style={{ fontSize: '10px', margin: 0 }}>
                    {nodeList.length} nodes
                  </Tag>
                </div>
              }
              key="nodes"
              style={{ backgroundColor: 'white' }}
            >
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {nodeList.map((node: any, index: number) => (
                  <div
                    key={index}
                    style={{
                      padding: '8px 12px',
                      marginBottom: '8px',
                      backgroundColor: '#f8f9fa',
                      borderRadius: '6px',
                      border: '1px solid #e9ecef',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#e3f2fd';
                      e.currentTarget.style.borderColor = '#90caf9';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#f8f9fa';
                      e.currentTarget.style.borderColor = '#e9ecef';
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        marginBottom: '6px',
                      }}
                    >
                      <Text strong style={{ fontSize: '12px', color: '#1890ff' }}>
                        {node.name || `Node ${index + 1}`}
                      </Text>
                      <Tag
                        color={getStateColor(node.state)}
                        style={{ fontSize: '10px', margin: 0 }}
                      >
                        {node.state || 'unknown'}
                      </Tag>
                    </div>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '8px',
                        fontSize: '11px',
                      }}
                    >
                      <div>
                        <Text type="secondary" style={{ fontSize: '10px' }}>
                          Function Block ID
                        </Text>
                        <div
                          style={{
                            marginTop: '2px',
                            color: '#666',
                            fontFamily: 'monospace',
                            backgroundColor: '#fff',
                            padding: '2px 6px',
                            borderRadius: '3px',
                            border: '1px solid #e0e0e0',
                          }}
                        >
                          {node.functionBlockId || 'N/A'}
                        </div>
                      </div>
                      <div>
                        <Text type="secondary" style={{ fontSize: '10px' }}>
                          Version ID
                        </Text>
                        <div
                          style={{
                            marginTop: '2px',
                            color: '#666',
                            fontFamily: 'monospace',
                            backgroundColor: '#fff',
                            padding: '2px 6px',
                            borderRadius: '3px',
                            border: '1px solid #e0e0e0',
                          }}
                        >
                          {node.functionBlockVersionId || 'N/A'}
                        </div>
                      </div>
                      <div>
                        <Text type="secondary" style={{ fontSize: '10px' }}>
                          Data ID
                        </Text>
                        <div
                          style={{
                            marginTop: '2px',
                            color: '#666',
                            fontFamily: 'monospace',
                            backgroundColor: '#fff',
                            padding: '2px 6px',
                            borderRadius: '3px',
                            border: '1px solid #e0e0e0',
                          }}
                        >
                          {node.dataId || 'N/A'}
                        </div>
                      </div>
                      <div>
                        <Text type="secondary" style={{ fontSize: '10px' }}>
                          State
                        </Text>
                        <div
                          style={{
                            marginTop: '2px',
                            color: '#666',
                            fontFamily: 'monospace',
                            backgroundColor: '#fff',
                            padding: '2px 6px',
                            borderRadius: '3px',
                            border: '1px solid #e0e0e0',
                          }}
                        >
                          {node.state || 'N/A'}
                        </div>
                      </div>
                      <div>
                        <Text type="secondary" style={{ fontSize: '10px' }}>
                          Node Type
                        </Text>
                        <div
                          style={{
                            marginTop: '2px',
                            color: '#666',
                            fontFamily: 'monospace',
                            backgroundColor: '#fff',
                            padding: '2px 6px',
                            borderRadius: '3px',
                            border: '1px solid #e0e0e0',
                          }}
                        >
                          {node.type || 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>
          </Collapse>
        )}
      </Card>
    </div>
  );
};

export default GetAnalysisInfoToolDetails;
