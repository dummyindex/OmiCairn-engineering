import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { requestDynamicGenerationListByAnalysis } from '@/request/computation';
import type {
  DynamicGenerationBranch,
  DynamicGenerationInteraction,
  DynamicGenerationInteractionsResponse,
  InteractionDetailsResponse,
} from '@/request/dynamicGenerationLlmMonitor';
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
  MoreOutlined,
  RightOutlined,
  ThunderboltOutlined,
  ToolOutlined,
} from '@ant-design/icons';
import { Badge, Card, Collapse, Dropdown, Space, Tabs, Tag, Typography } from 'antd';
import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { useModel } from 'umi';

const { Text } = Typography;
const { Panel } = Collapse;

interface DynamicGenerationTask {
  generationId: number;
  userRequest: string;
  state: string;
  createdTime: number;
}

interface ExpandedState {
  tasks: Record<number, boolean>;
  branches: Record<string, boolean>; // key: `${taskId}_${branchId}`
  interactions: Record<string, boolean>; // key: `${taskId}_${branchId}_${interactionId}`
}

interface ErrorAndProcessTabsProps {
  // Error Message props
  activeErrorKey?: string;
  errorNodeList?: any[];
  activePanelKey?: string | string[] | number | number[];
  errorMessage?: any;
  errorSolution?: any;
  errorMessageAndSolution?: any;
  errorMessageAndSolutionLoading?: any;
  errorLogShow?: any;
  errorMessageLog?: any;
  errorMessageLogLoading?: any;
  onCollapseChange?: (key: string | string[] | number | number[]) => void;
  getErrorMessageMenu?: (nodeId: string) => React.ReactNode;
  collapseRefs?: React.MutableRefObject<Record<string, HTMLDivElement | null>>;
  // Process props
  analysisId?: string;
  onTabChange?: (activeTab: string) => void;
  activeTab?: string;
}

const ErrorAndProcessTabs: React.FC<ErrorAndProcessTabsProps> = ({
  // Error Message props
  // activeErrorKey,
  errorNodeList = [],
  activePanelKey,
  errorMessage = {},
  errorSolution = {},
  errorMessageAndSolution = {},
  errorMessageAndSolutionLoading = {},
  errorLogShow = {},
  errorMessageLog = {},
  errorMessageLogLoading = {},
  onCollapseChange,
  getErrorMessageMenu,
  collapseRefs,
  // Process props
  analysisId,
  onTabChange,
  activeTab = 'error',
}) => {
  const { dictionary } = useModel('localization');

  // Auto Genie Process states
  const [dynamicGenerationTasks, setDynamicGenerationTasks] = useState<DynamicGenerationTask[]>([]);
  const [taskData, setTaskData] = useState<
    Record<number, DynamicGenerationInteractionsResponse['data']>
  >({});
  const [loading, setLoading] = useState<Record<number, boolean>>({});
  const [expanded, setExpanded] = useState<ExpandedState>({
    tasks: {},
    branches: {},
    interactions: {},
  });

  // State for interaction details
  const [interactionDetails, setInteractionDetails] = useState<
    Record<string, InteractionDetailsResponse['data']>
  >({});
  const [interactionDetailsLoading, setInteractionDetailsLoading] = useState<
    Record<string, boolean>
  >({});

  // Text expand/collapse state
  const [expandedTexts, setExpandedTexts] = useState<Record<string, boolean>>({});

  const toggleTextExpansion = (key: string) => {
    setExpandedTexts((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const renderTruncatedText = (content: string, key: string, color: string = '#52c41a') => {
    const isExpanded = expandedTexts[key];
    const shouldTruncate = content.length > 100;
    const displayContent = shouldTruncate && !isExpanded ? content.slice(0, 100) : content;

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
        {shouldTruncate && !isExpanded && (
          <span
            style={{
              color,
              cursor: 'pointer',
              textDecoration: 'underline',
              marginLeft: '4px',
            }}
            onClick={(e) => {
              e.stopPropagation();
              toggleTextExpansion(key);
            }}
          >
            ...more
          </span>
        )}
        {shouldTruncate && isExpanded && (
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
              toggleTextExpansion(key);
            }}
          >
            Show less
          </span>
        )}
      </div>
    );
  };

  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const getInteractionDescription = (source: string): string => {
    switch (source) {
      case 'next_fb_generation':
        return dictionary.GENERATING_NEXT_FUNCTION_BLOCKS;
      case 'computation_retry_bug_fixer':
        return dictionary.RETRYING_COMPUTATION_WITH_BUG_FIXER;
      default:
        return dictionary.RUNNING;
    }
  };

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

  const fetchDynamicGenerationTasks = async () => {
    if (!analysisId) return;

    try {
      const response = await requestDynamicGenerationListByAnalysis(analysisId);
      if (response.code === 200 && response.data) {
        const sortedTasks = response.data.sort(
          (a: DynamicGenerationTask, b: DynamicGenerationTask) =>
            b.createdTime > a.createdTime ? 1 : -1,
        );
        setDynamicGenerationTasks(sortedTasks);
      }
    } catch (error) {
      console.error('Failed to fetch dynamic generation task list:', error);
    }
  };

  const fetchTaskInteractions = async (taskId: number) => {
    if (loading[taskId]) return;

    setLoading((prev) => ({ ...prev, [taskId]: true }));

    try {
      const response: DynamicGenerationInteractionsResponse =
        await requestDynamicGenerationInteractions(taskId);
      if (response.code === 200) {
        setTaskData((prev) => ({
          ...prev,
          [taskId]: response.data,
        }));
      }
    } catch (error) {
      console.error(`Failed to fetch interaction data for task ${taskId}:`, error);
    } finally {
      setLoading((prev) => ({ ...prev, [taskId]: false }));
    }
  };

  const toggleTaskExpansion = async (taskId: number) => {
    const isExpanded = expanded.tasks[taskId];

    setExpanded((prev) => ({
      ...prev,
      tasks: {
        ...prev.tasks,
        [taskId]: !isExpanded,
      },
    }));

    // If expanding and no data yet, fetch it
    if (!isExpanded && !taskData[taskId]) {
      await fetchTaskInteractions(taskId);
    }
  };

  const toggleBranchExpansion = (taskId: number, branchId: number) => {
    const key = `${taskId}_${branchId}`;
    setExpanded((prev) => ({
      ...prev,
      branches: {
        ...prev.branches,
        [key]: !prev.branches[key],
      },
    }));
  };

  const fetchInteractionDetails = async (
    interaction: DynamicGenerationInteraction,
    taskData: DynamicGenerationInteractionsResponse['data'],
  ) => {
    const detailsKey = `${interaction.type}_${interaction.session_id}`;

    if (interactionDetailsLoading[detailsKey] || interactionDetails[detailsKey]) {
      return;
    }

    setInteractionDetailsLoading((prev) => ({ ...prev, [detailsKey]: true }));
    console.log('Fetching interaction details for:', detailsKey, interaction, taskData);

    try {
      const response = await requestInteractionDetails(
        interaction.type,
        interaction.session_id,
        interaction.dynamic_generation_id || taskData.generation_id,
        interaction.retry_process_id,
        interaction.node_id,
      );

      console.log('Fetched interaction details:', response);

      if (response.code === 200) {
        setInteractionDetails((prev) => ({
          ...prev,
          [detailsKey]: response.data,
        }));
      }
    } catch (error) {
      console.error(`Failed to fetch interaction details: ${error}`);
    } finally {
      setInteractionDetailsLoading((prev) => ({ ...prev, [detailsKey]: false }));
    }
  };

  const toggleInteractionExpansion = async (
    taskId: number,
    branchId: number,
    interactionId: string,
    interaction: DynamicGenerationInteraction,
  ) => {
    const key = `${taskId}_${branchId}_${interactionId}`;
    const wasExpanded = expanded.interactions[key];

    setExpanded((prev) => ({
      ...prev,
      interactions: {
        ...prev.interactions,
        [key]: !wasExpanded,
      },
    }));

    // If expanding and no detail data yet, fetch the details
    if (!wasExpanded) {
      const currentTaskData = taskData[taskId];
      if (currentTaskData) {
        await fetchInteractionDetails(interaction, currentTaskData);
      }
    }
  };

  const startPolling = () => {
    fetchDynamicGenerationTasks();
    pollingRef.current = setInterval(() => {
      // Poll for updates on all expanded tasks
      Object.entries(expanded.tasks).forEach(([taskIdStr, isExpanded]) => {
        if (isExpanded) {
          const taskId = parseInt(taskIdStr);
          fetchTaskInteractions(taskId);
        }
      });
    }, 5000);
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => {
    if (activeTab === 'process' && analysisId) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [activeTab, analysisId]);

  const handleTabChange = (key: string) => {
    onTabChange?.(key);
  };

  // Render an interaction item
  const renderInteraction = (
    taskId: number,
    branchId: number,
    interaction: DynamicGenerationInteraction,
  ) => {
    const interactionKey = `${taskId}_${branchId}_${interaction.id}`;
    const isExpanded = expanded.interactions[interactionKey];
    const duration = calculateInteractionDuration(interaction);
    const durationText = formatDuration(duration);

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
            toggleInteractionExpansion(taskId, branchId, interaction.id, interaction);
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div
              style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: 0 }}
            >
              {isExpanded ? (
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
                {getInteractionDescription(interaction.interaction_source)}
              </Text>
              {/* <Tag 
                color={getInteractionTypeColor(interaction.type)}
                style={{ fontSize: '11px', padding: '0 6px', height: '20px', lineHeight: '18px', flexShrink: 0 }}
              >
                {interaction.type}
              </Tag> */}
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
          {isExpanded && (
            <div
              style={{
                marginTop: '12px',
                paddingTop: '12px',
                borderTop: '1px solid #e8e8e8',
              }}
            >
              {/* Timing information */}
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

              {/* Error information */}
              {/* {interaction.errors && (
                <div style={{ marginBottom: '12px' }}>
                  <Text type="secondary" style={{ fontSize: '12px' }}>Error Information:</Text>
                  <div style={{ 
                    marginTop: '4px',
                    padding: '8px',
                    backgroundColor: '#fff2f0',
                    border: '1px solid #ffccc7',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontFamily: 'monospace',
                    maxHeight: '100px',
                    overflowY: 'auto'
                  }}>
                    {interaction.errors}
                  </div>
                </div>
              )}
               */}
              {/* Detailed content - loaded from S3 */}
              {(() => {
                const detailsKey = `${interaction.type}_${interaction.session_id}`;
                const details = interactionDetails[detailsKey];
                const isLoading = interactionDetailsLoading[detailsKey];

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
                                    {renderTruncatedText(
                                      typeof details.input === 'string'
                                        ? details.input
                                        : JSON.stringify(details.input, null, 2),
                                      `input_${detailsKey}`,
                                      '#87ceeb',
                                    )}
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
                                    {renderTruncatedText(
                                      typeof details.output === 'string'
                                        ? details.output
                                        : JSON.stringify(details.output, null, 2),
                                      `output_${detailsKey}`,
                                      '#52c41a',
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* File information */}
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

              {/* Basic information */}
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

  // Render branches
  const renderBranch = (taskId: number, branch: DynamicGenerationBranch) => {
    const branchKey = `${taskId}_${branch.branch_id}`;
    const isExpanded = expanded.branches[branchKey];
    const totalDuration = branch.interactions.reduce(
      (sum, interaction) => sum + calculateInteractionDuration(interaction),
      0,
    );

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
            toggleBranchExpansion(taskId, branch.branch_id);
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
              {isExpanded ? <DownOutlined /> : <RightOutlined />}
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

          {isExpanded && branch.interactions.length > 0 && (
            <div style={{ marginTop: '16px' }}>
              {branch.interactions.map((interaction) =>
                renderInteraction(taskId, branch.branch_id, interaction),
              )}
            </div>
          )}

          {isExpanded && branch.interactions.length === 0 && (
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

  const tabItems = [
    {
      key: 'error',
      label: dictionary.ERROR_MESSAGE || 'Error Message',
      children: (
        <div className="error-message-content">
          {errorNodeList.map((item) => (
            <div
              key={item.id}
              ref={collapseRefs ? (el) => (collapseRefs.current[item.id] = el) : undefined}
              data-node-id={item.id}
            >
              <Collapse
                ghost
                collapsible="icon"
                activeKey={activePanelKey}
                onChange={onCollapseChange}
              >
                <Panel
                  key={item.id}
                  header={
                    <div className="error-message-header">
                      <span>{item.name}</span>
                    </div>
                  }
                  extra={
                    getErrorMessageMenu && (
                      <Dropdown overlay={getErrorMessageMenu(item.id)} trigger={['hover']}>
                        <MoreOutlined style={{ cursor: 'pointer' }} />
                      </Dropdown>
                    )
                  }
                >
                  {errorMessageAndSolutionLoading[item.id] ? (
                    <div>
                      <LoadingOutlined /> {dictionary.LOADING || 'Loading'}...
                    </div>
                  ) : errorSolution[item.id] !== '' && errorMessage[item.id] !== '' ? (
                    <div>
                      <div className="errorDetails">
                        <ReactMarkdown className="markdown-content">
                          {errorMessage[item.id]}
                        </ReactMarkdown>
                      </div>
                      <div className="errorSolutionTitle">SOLUTION</div>
                      <div className="errorSolution">
                        <ReactMarkdown className="markdown-content">
                          {errorSolution[item.id]}
                        </ReactMarkdown>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="errorSolutionTitle">ERROR MESSAGE AND SOLUTION</div>
                      <div className="errorSolution">
                        <ReactMarkdown className="markdown-content">
                          {errorMessageAndSolution[item.id]}
                        </ReactMarkdown>
                      </div>
                    </div>
                  )}
                  <div>
                    {/* <div
                      className="errorLogTitle"
                      onClick={() => {
                        const newErrorLogShow = {
                          ...errorLogShow,
                          [item.id]: !errorLogShow[item.id],
                        };
                      }}
                    >
                      LOG {errorLogShow[item.id] ? <CaretDownOutlined /> : <CaretUpOutlined />}
                    </div> */}
                    {errorMessageLogLoading[item.id] ? (
                      <div className="loading" style={{ marginTop: '20px' }}>
                        <LoadingOutlined /> {dictionary.LOADING || 'Loading'}...
                      </div>
                    ) : errorMessageLog[item.id] ? (
                      <div
                        className="errorLogContent"
                        style={{
                          marginTop: '7px',
                          display: errorLogShow[item.id] ? 'block' : 'none',
                        }}
                      >
                        {errorMessageLog[item.id]}
                      </div>
                    ) : null}
                  </div>
                </Panel>
              </Collapse>
            </div>
          ))}
        </div>
      ),
    },
    {
      key: 'process',
      label: (
        <Space>
          <CustomImage name={customIconNames.AIICONSTAR} style={{ height: '14px' }} />
          {dictionary.AUTO_GENIE_PROCESS || 'Auto Genie Process'}
        </Space>
      ),
      children: (
        <div>
          {dynamicGenerationTasks.length === 0 ? (
            <div
              style={{
                padding: '40px',
                textAlign: 'center',
                color: '#999',
                background: 'white',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
              }}
            >
              {dictionary.NO_DYNAMIC_GENERATION_TASKS || 'No dynamic generation tasks'}
            </div>
          ) : (
            dynamicGenerationTasks.map((task) => {
              const isTaskExpanded = expanded.tasks[task.generationId];
              const data = taskData[task.generationId];
              const isLoading = loading[task.generationId];

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
                      {data && (
                        <Space>
                          <Badge count={data.total_branches} showZero color="#1890ff" />
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
                      onClick={() => toggleTaskExpansion(task.generationId)}
                    >
                      <Space>
                        {isTaskExpanded ? <DownOutlined /> : <RightOutlined />}
                        <Text>{isTaskExpanded ? 'Hide Process' : 'Show Process'}</Text>
                      </Space>
                      {data && (
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          Latest Update: {new Date(data.last_updated).toLocaleString()}
                        </Text>
                      )}
                    </div>

                    {/* Branch list */}
                    {isTaskExpanded && (
                      <div
                        style={{
                          paddingTop: '12px',
                          borderTop: '1px solid #f0f0f0',
                          marginTop: '8px',
                        }}
                      >
                        {isLoading ? (
                          <div
                            style={{
                              padding: '20px',
                              textAlign: 'center',
                              color: '#1890ff',
                            }}
                          >
                            <LoadingOutlined spin style={{ marginRight: '8px' }} />
                            Loading Branch
                          </div>
                        ) : data && data.branches.length > 0 ? (
                          <>
                            {data.branches.map((branch) => renderBranch(task.generationId, branch))}
                          </>
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
            })
          )}
        </div>
      ),
    },
  ];

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 9,
          backgroundColor: 'white',
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={handleTabChange}
          items={tabItems.map((item) => ({
            ...item,
            children: null, // Drop children; show only the tab header
          }))}
          size="small"
          tabBarStyle={{
            margin: 0,
            padding: '0 16px',
          }}
        />
      </div>
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
        }}
      >
        {/* Render content for the activeTab */}
        {activeTab === 'error' && tabItems[0].children}
        {activeTab === 'process' && tabItems[1].children}
      </div>
    </div>
  );
};

export default ErrorAndProcessTabs;
