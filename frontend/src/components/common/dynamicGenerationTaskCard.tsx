import {
  requestDynamicGenerationInteractions,
  requestInteractionDetails,
} from '@/request/dynamicGenerationLlmMonitor';
import { calculateInteractionDuration, formatDuration } from '@/util/common';
import {
  BranchesOutlined,
  ClockCircleOutlined,
  DownOutlined,
  LoadingOutlined,
  RightOutlined,
  ThunderboltOutlined,
  ToolOutlined,
} from '@ant-design/icons';
import { Badge, Card, Space, Tag, Typography } from 'antd';
import React, { useEffect, useCallback } from 'react';
import { useModel } from 'umi';

const createThrottledRequest = () => {
  const activeRequests = new Set<string>();
  const requestQueue: (() => Promise<any>)[] = [];
  const MAX_CONCURRENT = 3;
  let processing = false;

  const processQueue = async () => {
    if (processing || requestQueue.length === 0) return;
    processing = true;

    const requests: (() => Promise<any>)[] = [];
    while (requestQueue.length > 0 && activeRequests.size < MAX_CONCURRENT) {
      const request = requestQueue.shift();
      if (request) {
        requests.push(request);
      }
    }

    requests.forEach((request) => {
      request().finally(() => {
        processing = false;
        setTimeout(processQueue, 100); // Small delay between requests
      });
    });

    if (requests.length === 0) {
      processing = false;
    }
  };

  return {
    addRequest: (key: string, requestFn: () => Promise<any>) => {
      if (activeRequests.has(key)) return Promise.resolve(null);

      return new Promise((resolve, reject) => {
        const wrappedRequest = async () => {
          activeRequests.add(key);
          try {
            const result = await requestFn();
            resolve(result);
          } catch (error) {
            reject(error);
          } finally {
            activeRequests.delete(key);
          }
        };

        requestQueue.push(wrappedRequest);
        processQueue();
      });
    },
  };
};

const requestThrottler = createThrottledRequest();

const { Text } = Typography;

const getSourceIcon = (source: string) => {
  switch (source) {
    case 'next_fb_generation':
      return <ThunderboltOutlined style={{ color: '#52c41a' }} />;
    case 'computation_retry_bug_fixer':
      return <ToolOutlined style={{ color: '#fa8c16' }} />;
    default:
      return <ClockCircleOutlined style={{ color: '#1890ff' }} />;
  }
};

const InteractionDescription = (props: any) => {
  const { dictionary } = useModel('localization');
  const { source } = props;

  const getDescription = () => {
    switch (source) {
      case 'next_fb_generation':
        return dictionary.GENERATING_NEXT_FUNCTION_BLOCKS;
      case 'computation_retry_bug_fixer':
        return dictionary.RETRYING_COMPUTATION_WITH_BUG_FIXER;
      default:
        return dictionary.RUNNING;
    }
  };
  return <Text style={{ fontSize: '13px' }}>{getDescription()}</Text>;
};

const TruncatedText = ({ content, color = '#52c41a' }) => {
  const [expanded, setExpanded] = React.useState(false);
  const shouldTruncate = content.length > 100;
  const displayContent = shouldTruncate && !expanded ? content.slice(0, 100) : content;

  return (
    <div
      style={{
        fontSize: '12px',
        lineHeight: '1.4',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}
    >
      {displayContent}
      {shouldTruncate && !expanded && (
        <span
          style={{
            color,
            cursor: 'pointer',
            textDecoration: 'underline',
            marginLeft: '4px',
          }}
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(true);
          }}
        >
          ...more
        </span>
      )}
      {shouldTruncate && expanded && (
        <span
          style={{
            color,
            cursor: 'pointer',
            textDecoration: 'underline',
            marginLeft: '4px',
            display: 'block',
            marginTop: '4px',
          }}
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(false);
          }}
        >
          Show less
        </span>
      )}
    </div>
  );
};

const DynamicGenerationInteraction = ({ interaction }) => {
  const [expanded, setExpanded] = React.useState(true);

  const [details, setDetails] = React.useState<any>(null);

  const [isLoading, setIsLoading] = React.useState<boolean>(false);
  const [hasLoaded, setHasLoaded] = React.useState<boolean>(false);

  const duration = calculateInteractionDuration(interaction);
  const durationText = formatDuration(duration);

  const loadInteractionDetails = useCallback(
    async (showLoading: boolean) => {
      if (hasLoaded) return;

      const requestKey = `interaction_${interaction.session_id}_${interaction.node_id}`;

      if (showLoading) {
        setIsLoading(true);
      }

      try {
        const response = await requestThrottler.addRequest(requestKey, () =>
          requestInteractionDetails(
            interaction.type,
            interaction.session_id,
            interaction.dynamic_generation_id,
            interaction.retry_process_id,
            interaction.node_id,
          ),
        );

        if (response && response.data) {
          const { data } = response;
          setDetails(data);
          setHasLoaded(true);
        }
      } catch (error: any) {
        console.error('Failed to load interaction details:', error);
        // Handle insufficient resources error
        if (
          error?.message?.includes('ERR_INSUFFICIENT_RESOURCES') ||
          error?.code === 'ERR_INSUFFICIENT_RESOURCES'
        ) {
          // Retry after a longer delay
          setTimeout(() => {
            if (!hasLoaded) {
              loadInteractionDetails(false);
            }
          }, 2000 + Math.random() * 1000);
        }
      } finally {
        if (showLoading) {
          setIsLoading(false);
        }
      }
    },
    [hasLoaded, interaction],
  );

  useEffect(() => {
    if (expanded && !hasLoaded) {
      loadInteractionDetails(true);
    }
  }, [expanded, hasLoaded]);

  return (
    <div
      key={interaction.id}
      style={{
        borderLeft: '2px solid #f0f0f0',
        marginBottom: '8px',
      }}
    >
      <div
        style={{
          padding: '8px 12px',
          backgroundColor: '#fafafa',
          borderRadius: '6px',
          border: '1px solid #f0f0f0',
          cursor: 'pointer',
        }}
        onClick={(e) => {
          e.stopPropagation();
          const newExpanded = !expanded;
          setExpanded(newExpanded);
          if (newExpanded && !hasLoaded) {
            loadInteractionDetails(true);
          }
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: 0 }}>
            {expanded ? (
              <DownOutlined style={{ fontSize: '12px' }} />
            ) : (
              <RightOutlined style={{ fontSize: '12px' }} />
            )}
            {getSourceIcon(interaction.interaction_source)}
            <Text
              style={{
                fontSize: '13px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              <InteractionDescription source={interaction.interaction_source} />
            </Text>
            {!interaction.is_valid && (
              <Tag
                color="red"
                style={{
                  fontSize: '11px',
                  padding: '0 6px',
                  height: '20px',
                  lineHeight: '18px',
                  flexShrink: 0,
                }}
              >
                ERROR
              </Tag>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
            <Text type="secondary" style={{ fontSize: '12px', whiteSpace: 'nowrap' }}>
              Duration: {durationText}
            </Text>
            <Text type="secondary" style={{ fontSize: '11px', whiteSpace: 'nowrap' }}>
              ID: {interaction.session_id}
            </Text>
          </div>
        </div>

        {/* Expanded interaction details */}
        {expanded && (
          <div
            style={{
              marginTop: '12px',
              paddingTop: '12px',
              borderTop: '1px solid #e8e8e8',
            }}
          >
            {/* Timing info */}
            <div style={{ marginBottom: '12px' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Time Information:
              </Text>
              <div style={{ marginTop: '4px', fontSize: '12px' }}>
                {interaction.start_time && (
                  <div>Start Time: {new Date(interaction.start_time).toLocaleString()}</div>
                )}
                {interaction.end_time && (
                  <div>End Time: {new Date(interaction.end_time).toLocaleString()}</div>
                )}
              </div>
            </div>

            {/* Detailed content - loaded from S3 */}
            {(() => {
              return (
                <div style={{ marginBottom: '12px' }}>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    Details:
                  </Text>

                  {isLoading ? (
                    <div
                      style={{
                        marginTop: '8px',
                        padding: '20px',
                        textAlign: 'center',
                        backgroundColor: '#f8f9fa',
                        borderRadius: '4px',
                      }}
                    >
                      <LoadingOutlined spin style={{ marginRight: '8px' }} />
                      Loading Details...
                    </div>
                  ) : details ? (
                    <div style={{ marginTop: '8px' }}>
                      {/* Chat-style Input and Output */}
                      {(details.input || details.output) && (
                        <div style={{ marginBottom: '12px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {/* Input - user message */}
                            {details.input && (
                              <div
                                style={{
                                  display: 'flex',
                                  flexDirection: 'column',
                                  alignItems: 'flex-end',
                                }}
                              >
                                <div
                                  style={{
                                    fontSize: '11px',
                                    fontWeight: 500,
                                    marginBottom: '4px',
                                    color: '#1890ff',
                                    alignSelf: 'flex-end',
                                  }}
                                >
                                  Me
                                </div>
                                <div
                                  style={{
                                    maxWidth: '80%',
                                    backgroundColor: '#1890ff',
                                    color: 'white',
                                    padding: '12px 16px',
                                    borderRadius: '18px 18px 4px 18px',
                                  }}
                                >
                                  <TruncatedText
                                    content={
                                      typeof details.input === 'string'
                                        ? details.input
                                        : JSON.stringify(details.input, null, 2)
                                    }
                                    key={`input_${interaction.session_id}`}
                                    color="#87ceeb"
                                  />
                                </div>
                              </div>
                            )}

                            {/* Output - agent reply */}
                            {details.output && (
                              <div
                                style={{
                                  display: 'flex',
                                  flexDirection: 'column',
                                  alignItems: 'flex-start',
                                }}
                              >
                                <div
                                  style={{
                                    fontSize: '11px',
                                    fontWeight: 500,
                                    marginBottom: '4px',
                                    color: '#52c41a',
                                    alignSelf: 'flex-start',
                                  }}
                                >
                                  Agent
                                </div>
                                <div
                                  style={{
                                    maxWidth: '80%',
                                    backgroundColor: '#f8f9fa',
                                    border: '1px solid #e9ecef',
                                    color: '#333',
                                    padding: '12px 16px',
                                    borderRadius: '18px 18px 18px 4px',
                                  }}
                                >
                                  <TruncatedText
                                    content={
                                      typeof details.output === 'string'
                                        ? details.output
                                        : JSON.stringify(details.output, null, 2)
                                    }
                                    key={`output_${interaction.session_id}`}
                                    color="#52c41a"
                                  />
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* File info */}
                      {details.files_found && details.files_found.length > 0 && (
                        <div style={{ marginBottom: '8px' }}>
                          <Text type="secondary" style={{ fontSize: '11px' }}>
                            Found Files: {details.files_found.join(', ')}
                          </Text>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div
                      style={{
                        marginTop: '8px',
                        padding: '16px',
                        textAlign: 'center',
                        backgroundColor: '#fafafa',
                        borderRadius: '4px',
                        color: '#999',
                      }}
                    >
                      Click to expand and load details automatically
                    </div>
                  )}
                </div>
              );
            })()}

            {/* Basic info */}
            <div style={{ fontSize: '12px', color: '#666' }}>
              <div>Session ID: {interaction.session_id}</div>
              {interaction.source_node_id && <div>Source Node: {interaction.source_node_id}</div>}
              {interaction.node_id && <div>Node ID: {interaction.node_id}</div>}
              {interaction.retry_process_id && (
                <div>Retry Process: {interaction.retry_process_id}</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const DynamicGenerationBranch = ({ branch }) => {
  const [expanded, setExpanded] = React.useState(true);
  const [shouldRenderInteractions, setShouldRenderInteractions] = React.useState(true);

  const totalDuration = React.useMemo(() => {
    return branch.interactions.reduce(
      (sum: number, interaction: any) => sum + calculateInteractionDuration(interaction),
      0,
    );
  }, [branch.interactions]);

  const toggleExpansion = () => {
    const newExpanded = !expanded;
    setExpanded(newExpanded);
    if (newExpanded && !shouldRenderInteractions) {
      setShouldRenderInteractions(true);
    }
  };

  return (
    <div
      key={branch.branch_id}
      style={{
        marginBottom: '12px',
      }}
    >
      <div
        style={{
          padding: '12px',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          border: '1px solid #e9ecef',
          cursor: 'pointer',
        }}
        onClick={(e) => {
          toggleExpansion();
          e.stopPropagation();
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'stretch',
            flexDirection: 'column',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '8px',
              flex: 1,
              minWidth: 0,
            }}
          >
            {expanded ? <DownOutlined /> : <RightOutlined />}
            <BranchesOutlined style={{ color: '#1890ff' }} />
            <Text strong>Branch #{branch.branch_id}</Text>
            <div style={{ flex: 1 }} />
            <Tag color={branch.state === 'running' ? 'green' : 'blue'}>{branch.state}</Tag>
            <Badge count={branch.total_interactions} showZero color="#faad14" />
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '8px',
              flex: 1,
              minWidth: 0,
            }}
          >
            <Text type="secondary" style={{ fontSize: '12px' }}>
              Total Duration: {formatDuration(totalDuration)}
            </Text>
            <Text type="secondary" style={{ fontSize: '11px' }}>
              End Node: {branch.end_node_id}
            </Text>
          </div>
        </div>

        {expanded && branch.interactions.length > 0 && shouldRenderInteractions && (
          <div style={{ marginTop: '16px' }}>
            {branch.interactions.map((interaction: any) => {
              return (
                <DynamicGenerationInteraction
                  key={`interaction_${interaction.id}`}
                  interaction={interaction}
                />
              );
            })}
          </div>
        )}

        {expanded && branch.interactions.length === 0 && (
          <div
            style={{
              marginTop: '16px',
              padding: '20px',
              textAlign: 'center',
              color: '#999',
              fontSize: '12px',
            }}
          >
            No Interactions
          </div>
        )}
      </div>
    </div>
  );
};

const DynamicGenerationTaskCard: React.FC = ({ task }: any) => {
  const [taskData, setTaskData] = React.useState<any>(null);
  const [isLoadingTaskData, setIsLoadingTaskData] = React.useState(false);
  const [hasLoadedTaskData, setHasLoadedTaskData] = React.useState(false);

  const refreshInterval = React.useRef<NodeJS.Timeout | null>(null);

  const [isBranchListExpanded, setIsBranchListExpanded] = React.useState(true);

  const loadTaskData = useCallback(
    async (taskParam: any, isBranchListExpanded: boolean, showLoading = false) => {
      if (!taskParam.generationId || isBranchListExpanded === false) return;

      if (hasLoadedTaskData && showLoading) return;

      const requestKey = `task_data_${taskParam.generationId}`;

      try {
        if (showLoading) {
          setIsLoadingTaskData(true);
        }

        const response = await requestThrottler.addRequest(requestKey, () =>
          requestDynamicGenerationInteractions(taskParam.generationId),
        );

        if (response && response.data) {
          const { data } = response;
          setTaskData(data);
          if (!hasLoadedTaskData) {
            setHasLoadedTaskData(true);
          }
        }
      } catch (error: any) {
        console.error('Failed to load branch list:', error);
        // Handle insufficient resources error
        if (
          error?.message?.includes('ERR_INSUFFICIENT_RESOURCES') ||
          error?.code === 'ERR_INSUFFICIENT_RESOURCES'
        ) {
          // Retry after a longer delay
          setTimeout(() => {
            if (!hasLoadedTaskData && isBranchListExpanded) {
              loadTaskData(taskParam, isBranchListExpanded, false);
            }
          }, 3000 + Math.random() * 2000);
        }
      } finally {
        if (showLoading) {
          setIsLoadingTaskData(false);
        }
      }
    },
    [hasLoadedTaskData],
  );

  useEffect(() => {
    if (refreshInterval.current) {
      clearInterval(refreshInterval.current);
    }

    if (isBranchListExpanded) {
      const showLoading = !hasLoadedTaskData;
      loadTaskData(task, isBranchListExpanded, showLoading);

      refreshInterval.current = setInterval(
        () => loadTaskData(task, isBranchListExpanded, false),
        10000,
      );
    }

    return () => {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current);
      }
    };
  }, [isBranchListExpanded, hasLoadedTaskData]);

  return (
    <Card
      key={task.generationId}
      style={{
        marginBottom: '16px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
      }}
      title={
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Text strong>Auto Genie Task #{task.generationId}</Text>
          {taskData && (
            <Space>
              <Badge count={taskData.total_branches} showZero color="#1890ff" />
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Branches
              </Text>
            </Space>
          )}
        </div>
      }
      extra={
        <div
          style={{
            background: task.state === 'running' ? '#52c41a' : '#1890ff',
            color: 'white',
            padding: '4px 8px',
            borderRadius: '12px',
            fontSize: '12px',
          }}
        >
          {task.state === 'running' ? 'Running' : 'Completed'}
        </div>
      }
    >
      <div>
        <Text type="secondary">User Request:</Text>
        <div
          style={{
            marginTop: '4px',
            marginBottom: '12px',
            padding: '8px 12px',
            backgroundColor: '#f8f9fa',
            borderRadius: '6px',
            border: '1px solid #e9ecef',
            maxHeight: '80px',
            overflowY: 'auto',
          }}
        >
          <Text
            style={{
              fontSize: '13px',
              lineHeight: '1.4',
              wordBreak: 'break-word',
              whiteSpace: 'pre-wrap',
            }}
          >
            {task.userRequest}
          </Text>
        </div>

        {/* Collapsible run details */}
        <div
          style={{
            padding: '8px 0',
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderTop: '1px solid #f0f0f0',
          }}
          onClick={() => {
            const newExpanded = !isBranchListExpanded;
            setIsBranchListExpanded(newExpanded);
            if (newExpanded && !hasLoadedTaskData) {
              loadTaskData(task, newExpanded, true);
            }
          }}
        >
          <Space>
            {isBranchListExpanded ? <DownOutlined /> : <RightOutlined />}
            <Text>{isBranchListExpanded ? 'Hide Process' : 'Show Process'}</Text>
          </Space>
          {taskData && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              Latest Update: {new Date(taskData.last_updated).toLocaleString()}
            </Text>
          )}
        </div>

        {/* Branch list */}
        {isBranchListExpanded && (
          <div
            style={{
              paddingTop: '12px',
              borderTop: '1px solid #f0f0f0',
              marginTop: '8px',
            }}
          >
            {isLoadingTaskData ? (
              <div
                style={{
                  padding: '40px 20px',
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '12px',
                }}
              >
                <LoadingOutlined spin style={{ fontSize: '24px', color: '#1890ff' }} />
                <span style={{ color: '#666', fontSize: '14px' }}>Loading process data...</span>
              </div>
            ) : taskData && taskData.branches.length > 0 ? (
              taskData.branches.map((branch: any) => (
                <DynamicGenerationBranch key={`branch_${branch.branch_id}`} branch={branch} />
              ))
            ) : (
              <div
                style={{
                  padding: '20px',
                  textAlign: 'center',
                  color: '#999',
                }}
              >
                Empty
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

export default DynamicGenerationTaskCard;
