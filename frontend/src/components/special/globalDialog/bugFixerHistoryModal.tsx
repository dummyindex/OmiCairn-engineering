import {
  Modal,
  Table,
  Empty,
  Typography,
  Card,
  message,
  Tooltip,
  Switch,
  Spin,
  Button,
} from 'antd';
import { useModel } from 'umi';
import {
  requestBugFixerNodeListByNode,
  requestBugFixerHistory,
  requestBugFixerComputationContext,
} from '@/request/computation';
import { useState, useEffect } from 'react';
import { CodeOutlined, CopyOutlined, DashOutlined, InfoCircleOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import Editor from '@monaco-editor/react';
import { writeToClipboard } from '@/util/operationTools';

const { Text } = Typography;

interface ErrorDetails {
  errorDescription: string;
  optimizedErrorDescription: string;
  parsedErrorMessage?: string;
  parsedSolution?: string;
}

interface ContextDetails {
  input_prompt: string;
  raw_response: string;
}

const BugFixerHistoryModal = () => {
  const { dictionary } = useModel('localization');
  const { bugFixerHistoryInspectedNodeId, setBugFixerHistoryInspectedNodeId } =
    useModel('analysis');
  const { setFbVersionId } = useModel('visualPanelControl');
  const [nodeList, setNodeList] = useState([]);
  const [history, setHistory] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedError, setSelectedError] = useState<ErrorDetails | null>(null);
  const [selectedContext, setSelectedContext] = useState<ContextDetails | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [markdownMode, setMarkdownMode] = useState(true);
  const [isContextModalOpen, setIsContextModalOpen] = useState(false);

  const parseOptimizedErrorDescription = (optimizedErrorDescription) => {
    let errorMessage = '';
    let solution = '';

    if (!optimizedErrorDescription) {
      return { errorMessage, solution };
    }

    if (optimizedErrorDescription.startsWith('```')) {
      // Handle markdown format
      const parts = optimizedErrorDescription.split('error_message:');
      if (parts.length > 1) {
        const solutionParts = parts[1].split('solution:');
        if (solutionParts.length > 1) {
          errorMessage = solutionParts[0].trim();
          solution = solutionParts[1].trim();
        } else {
          // No solution part found
          errorMessage = optimizedErrorDescription;
        }
      } else {
        // No error_message part found
        errorMessage = optimizedErrorDescription;
      }
    } else {
      // Handle non-markdown format with backticks
      const parts = optimizedErrorDescription.split('`error_message:`');
      if (parts.length > 1) {
        const solutionParts = parts[1].split('`solution:`');
        if (solutionParts.length > 1) {
          errorMessage = solutionParts[0].trim();
          solution = solutionParts[1].trim();
        } else {
          // No solution part found
          errorMessage = optimizedErrorDescription;
        }
      } else {
        // No error_message part found
        errorMessage = optimizedErrorDescription;
      }
    }

    return { errorMessage, solution };
  };

  useEffect(() => {
    const fetchData = async () => {
      if (!bugFixerHistoryInspectedNodeId) return;

      setLoading(true);
      try {
        const [historyResponse, nodeListResponse] = await Promise.all([
          requestBugFixerHistory(bugFixerHistoryInspectedNodeId),
          requestBugFixerNodeListByNode(bugFixerHistoryInspectedNodeId),
        ]);

        if (historyResponse.code === 200) {
          setHistory(historyResponse.data.history);
        }

        if (nodeListResponse.code === 200) {
          setNodeList(nodeListResponse.data);
        }
      } catch (error) {
        message.error('Failed to fetch bug fixer data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [bugFixerHistoryInspectedNodeId]);

  const handleClose = () => {
    setBugFixerHistoryInspectedNodeId(null);
    setNodeList([]);
    setHistory('');
  };

  const handleErrorClick = (record: any) => {
    if (record.errorDescription && record.optimizedErrorDescription) {
      const { errorMessage, solution } = parseOptimizedErrorDescription(
        record.optimizedErrorDescription,
      );
      setSelectedError({
        errorDescription: record.errorDescription,
        optimizedErrorDescription: record.optimizedErrorDescription,
        parsedErrorMessage: errorMessage,
        parsedSolution: solution,
      });
    }
  };

  const handleContextClick = async (record: any) => {
    setIsContextModalOpen(true);
    setContextLoading(true);
    try {
      const response = await requestBugFixerComputationContext(record.id);

      if (response && response.code === 200) {
        const s3Response = await fetch(response.data, {
          method: 'GET',
          mode: 'cors',
          headers: {
            Accept: 'application/json',
          },
        });

        if (!s3Response.ok) {
          if (s3Response.status === 404) {
            const errorText = await s3Response.text();
            if (errorText.includes('NoSuchKey')) {
              message.warning(
                'Context data is not available yet. The computation might still be in progress.',
              );
              setSelectedContext(null);
              return;
            }
          }
          throw new Error(`S3 fetch failed: ${s3Response.status}`);
        }

        const contextData = await s3Response.json();
        setSelectedContext(contextData);
      } else {
        setSelectedContext(null);
      }
    } catch (error) {
      message.error('Failed to fetch context data');
      setSelectedContext(null);
    } finally {
      setContextLoading(false);
    }
  };

  const handleCopyCode = (content: string) => {
    try {
      writeToClipboard(content);
      message.success('Code copied to clipboard!');
    } catch (error) {
      message.error('Failed to copy code.');
      console.error('Copy failed:', error);
    }
  };

  const computationColumns = [
    {
      title: `${dictionary.CREATED_TIME}`,
      dataIndex: 'createdTime',
      key: 'createdTime',
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: `${dictionary.COMPUTATION_STATUS}`,
      dataIndex: 'computationState',
      key: 'computationState',
    },
    {
      title: `${dictionary.DURATION}`,
      dataIndex: 'duration',
      key: 'duration',
      render: (text) => `${text.toFixed(2)}s`,
    },
    {
      title: `${dictionary.CODE}`,
      dataIndex: 'code',
      key: 'code',
      render: (text, record) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {record.functionBlockVersionId ? (
            <Tooltip title="View Code">
              <CodeOutlined
                onClick={() => {
                  setFbVersionId(record.functionBlockVersionId);
                }}
              />
            </Tooltip>
          ) : null}
        </div>
      ),
    },
    {
      title: `${dictionary.ERROR_DESCRIPTION}`,
      dataIndex: 'errorDescription',
      key: 'errorDescription',
      render: (text, record) =>
        record.errorDescription && record.errorDescription.length > 0 ? (
          <Tooltip title="View Error Details">
            <InfoCircleOutlined onClick={() => handleErrorClick(record)} />
          </Tooltip>
        ) : (
          <DashOutlined />
        ),
    },
    {
      title: 'Context',
      dataIndex: 'context',
      key: 'context',
      render: (text, record) => (
        <Tooltip title="View Context">
          <InfoCircleOutlined onClick={() => handleContextClick(record)} />
        </Tooltip>
      ),
    },
  ];

  const columns = [
    {
      title: `${dictionary.CREATED_TIME}`,
      dataIndex: 'createdTime',
      key: 'createdTime',
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: `${dictionary.COMPLETED_TIME}`,
      dataIndex: 'completedTime',
      key: 'completedTime',
      render: (text) => (text ? new Date(text).toLocaleString() : '-'),
    },
    {
      title: `${dictionary.STATUS}`,
      dataIndex: 'state',
      key: 'state',
    },
    {
      title: `${dictionary.MAX_RETRIES}`,
      dataIndex: 'maxRetry',
      key: 'maxRetry',
    },
    {
      title: `${dictionary.REMAINING_RETRIES}`,
      dataIndex: 'restRetry',
      key: 'restRetry',
    },
  ];

  return (
    <div>
      <Modal
        width="80vw"
        centered
        title={dictionary.BUG_FIXER_HISTORY}
        open={!!bugFixerHistoryInspectedNodeId}
        onCancel={handleClose}
        cancelText={dictionary.CLOSE}
        okButtonProps={{ style: { display: 'none' } }}
        footer={null}
      >
        <div>
          <Card title={dictionary.COMPUTATION_RETRY_LIST} loading={loading}>
            {nodeList && nodeList.length > 0 ? (
              <Table
                dataSource={nodeList}
                columns={columns}
                rowKey="id"
                pagination={false}
                scroll={{ y: 240 }}
                expandable={{
                  expandedRowRender: (record) => (
                    <Table
                      dataSource={record.computations}
                      columns={computationColumns}
                      pagination={false}
                      rowKey="id"
                      size="small"
                    />
                  ),
                }}
              />
            ) : (
              <Empty description="No node list data available" />
            )}
          </Card>

          <Card title={dictionary.RUN_HISTORY} loading={loading}>
            {history && history !== '""' ? (
              <Text>{history}</Text>
            ) : (
              <Empty description="No history data available" />
            )}
          </Card>
        </div>
      </Modal>
      <Modal
        width={window.innerWidth * 0.5}
        centered
        title={dictionary.ERROR_DETAILS}
        open={!!selectedError}
        onCancel={() => setSelectedError(null)}
        cancelText={dictionary.CLOSE}
        okButtonProps={{ style: { display: 'none' } }}
        footer={null}
        bodyStyle={{
          height: window.innerHeight * 0.8,
          overflowY: 'auto',
          position: 'relative',
        }}
        style={{
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <div style={{ height: '100%', position: 'relative' }}>
          <div>
            <div>
              <Text strong>{dictionary.ERROR_DESCRIPTION + ':'}</Text>
              <Button
                icon={<CopyOutlined />}
                onClick={() => handleCopyCode(selectedError?.errorDescription || '')}
                type="text"
                size="large"
                style={{
                  marginRight: 10,
                  color: 'white',
                  position: 'absolute',
                  top: 30,
                  right: 10,
                  zIndex: 1,
                }}
              />
              <Editor
                height={`${Math.floor((window.innerHeight * 0.8 - 120) * 0.35)}px`}
                language="python"
                theme="vs-dark"
                value={selectedError?.errorDescription}
                options={{
                  fontSize: 14,
                  readOnly: true,
                  minimap: { enabled: false },
                  automaticLayout: true,
                  padding: { top: 20 },
                }}
              />
            </div>
            {selectedError?.parsedErrorMessage && (
              <div style={{ marginTop: '15px' }}>
                <Text strong>{dictionary.ERROR_MESSAGE + ':'}</Text>
                <div
                  style={{
                    maxHeight: `${Math.floor((window.innerHeight * 0.8 - 120) * 0.27)}px`,
                    overflowY: 'auto',
                    padding: '20px',
                    backgroundColor: '#f5f5f5',
                    borderRadius: '4px',
                    marginTop: '5px',
                  }}
                >
                  <ReactMarkdown>{selectedError.parsedErrorMessage}</ReactMarkdown>
                </div>
              </div>
            )}
            {selectedError?.parsedSolution && (
              <div style={{ marginTop: '15px' }}>
                <Text strong>{dictionary.SUGGESTED_SOLUTION + ':'}</Text>
                <div
                  style={{
                    maxHeight: `${Math.floor((window.innerHeight * 0.8 - 120) * 0.33)}px`,
                    overflowY: 'auto',
                    padding: '15px',
                    backgroundColor: '#f5f5f5',
                    borderRadius: '4px',
                    marginTop: '5px',
                  }}
                >
                  <ReactMarkdown>{selectedError.parsedSolution}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        </div>
      </Modal>
      <Modal
        width={window.innerWidth * 0.9}
        centered
        title="Bug Fixer Context"
        open={isContextModalOpen}
        onCancel={() => {
          setIsContextModalOpen(false);
          setSelectedContext(null);
        }}
        cancelText={dictionary.CLOSE}
        okButtonProps={{ style: { display: 'none' } }}
        footer={null}
        bodyStyle={{
          height: window.innerHeight * 0.8,
          overflowY: 'auto',
          position: 'relative',
        }}
        style={{
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {contextLoading ? (
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
              minHeight: '200px',
            }}
          >
            <Spin size="large" tip="Loading context data..." />
          </div>
        ) : selectedContext ? (
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '16px',
                paddingBottom: '8px',
                borderBottom: '1px solid #f0f0f0',
              }}
            >
              <Text>Plain Text</Text>
              <Switch checked={markdownMode} onChange={setMarkdownMode} size="small" />
              <Text>Markdown</Text>
            </div>

            <div
              style={{
                flex: 1,
                display: 'flex',
                gap: '16px',
                minHeight: 0,
              }}
            >
              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  minWidth: 0,
                }}
              >
                <Text strong style={{ marginBottom: '8px' }}>
                  Input Prompt:
                </Text>
                <div
                  style={{
                    flex: 1,
                    padding: '12px',
                    backgroundColor: '#f8f9fa',
                    border: '1px solid #e9ecef',
                    borderRadius: '6px',
                    overflowX: 'auto',
                    overflowY: 'auto',
                    fontSize: '13px',
                    fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                    lineHeight: '1.5',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {markdownMode ? (
                    <ReactMarkdown>
                      {selectedContext.input_prompt || 'No input data available'}
                    </ReactMarkdown>
                  ) : (
                    <pre
                      style={{
                        margin: 0,
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        fontFamily: 'inherit',
                      }}
                    >
                      {selectedContext.input_prompt || 'No input data available'}
                    </pre>
                  )}
                </div>
              </div>
              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  minWidth: 0,
                }}
              >
                <Text strong style={{ marginBottom: '8px' }}>
                  Response:
                </Text>
                <div
                  style={{
                    flex: 1,
                    padding: '12px',
                    backgroundColor: '#f8f9fa',
                    border: '1px solid #e9ecef',
                    borderRadius: '6px',
                    overflowX: 'auto',
                    overflowY: 'auto',
                    fontSize: '13px',
                    fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                    lineHeight: '1.5',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {markdownMode ? (
                    <ReactMarkdown>
                      {selectedContext.raw_response || 'No output data available'}
                    </ReactMarkdown>
                  ) : (
                    <pre
                      style={{
                        margin: 0,
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        fontFamily: 'inherit',
                      }}
                    >
                      {selectedContext.raw_response || 'No output data available'}
                    </pre>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <Empty description="No context data available" />
        )}
      </Modal>
    </div>
  );
};

export default BugFixerHistoryModal;
