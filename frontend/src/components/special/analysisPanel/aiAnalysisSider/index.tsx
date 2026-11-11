import { useModel } from 'umi';
import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useReactFlow } from 'reactflow';
import { Table, Badge, Tooltip, Switch, message, Segmented, Select, Modal, Button } from 'antd';
import type { TableColumnsType } from 'antd';
import {
  CloseOutlined,
  CodeOutlined,
  DashOutlined,
  DiffOutlined,
  HighlightOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  UserOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import {
  requestDashboardList,
  requestBugFixerNodeListByAnalysis,
  requestBugFixerSessions,
  requestDynamicGenerationListByAnalysis,
  requestDynamicGenerationSessions,
  requestDynamicGenerationNodesBySession,
} from '@/request/computation';
import { requestFBVersionContent } from '@/request/functionBlock';
import style from './index.less';
import './index.less';
import Editor, { DiffEditor } from '@monaco-editor/react';
import ReactMarkdown from 'react-markdown';
import { writeToClipboard } from '@/util/operationTools';
import { getLocationParams } from '@/util/getUrl';

interface AnalysisDataType {
  key: React.Key;
  node_name: string;
  node_code: string;
  node_id: string;
  status: string;
  create_time: string;
  duration: string;
  user_name: string;
  children?: AnalysisDataType[];
}

interface AutoGenieSessionDataType {
  key: React.Key;
  id: number;
  completionTokens: number;
  createdAt: string;
  dynamicGenerationId: number;
  functionality: string;
  functionalityTaskId: number;
  model: string;
  promptTokens: number;
  sourceNodeId: number;
  totalTokens: number;
}

interface AutoGenieNodeDataType {
  key: React.Key;
  analysisId: number;
  id: number;
  name: string;
  state: string;
  type: string;
  tag: string;
  createdTime: number;
  functionBlockId: number;
  functionBlockVersionId: string;
  dynamicGenerationId: number;
  dynamicGenerationSessionId: number;
  computationParams: string;
  computationResourceConfigure: string;
  systemEnv: string;
  x: number;
  y: number;
}

interface BugFixerDataType {
  key: React.Key;
  old_node_name: string;
  old_node_id: string;
  old_node_version_id: string;
  new_node_name: string;
  new_node_id: string;
  new_node_version_id: string;
  status: string;
  create_time: string;
  max_retries: number;
  rest_retries: number;
  total_completion_tokens: number;
  total_prompt_tokens: number;
  total_tokens: number;
  user_prompt: string;
  computations: BugFixerComputationDataType[];
}

interface BugFixerComputationDataType {
  key: React.Key;
  attemptNodeId: string;
  attemptName: string;
  functionBlockVersionId: string;
  computationState: string;
  startTime: string;
  duration: string;
  errorDescription: string;
  optimizedErrorDescription: string;
  parentIndex: number;
}

interface BugFixerSessionDataType {
  key: React.Key;
  id: number;
  completionTokens: number;
  createdAt: string;
  fixedComputationId: number;
  functionality: string;
  functionalityTaskId: number;
  model: string;
  nodeId: number;
  promptTokens: number;
  retryProcessId: number;
  totalTokens: number;
}

interface ErrorDetails {
  errorDescription: string;
  optimizedErrorDescription: string;
  parsedErrorMessage?: string;
  parsedSolution?: string;
}

export default function AiAnalysisSider(props: any = {}) {
  const { setCenter } = useReactFlow();
  const { isShowAIDashboard } = props;
  const { dictionary } = useModel('localization');
  const { userInfo } = useModel('user');
  const {
    instance,
    nodes,
    setIsCloseBtnClicked,
    analysisUpdatedTime,
    currentSelectedNodes,
    setTemporaryCenteredNodeId,
  } = useModel('analysis');
  const [analysisId] = getLocationParams(['analysis-id']);
  const { setFbVersionId } = useModel('visualPanelControl');
  const [activeTab, setActiveTab] = useState<string>(dictionary.ANALYSIS);
  const [selectedRows, setSelectedRows] = useState<React.Key[]>([]);

  const [agentCategory, setAgentCategory] = useState<string>(dictionary.AUTO_GENIE);
  const [currentColumns, setCurrentColumns] = useState<TableColumnsType<any>>([]);
  const [currentTableSource, setCurrentTableSource] = useState<any>([]);
  const [currentTableLoading, setCurrentTableLoading] = useState<boolean>(false);
  const [showEmptyRows, setShowEmptyRows] = useState<boolean>(true);

  const [isHighlightEnabled, setIsHighlightEnabled] = useState<boolean>(true);
  const [isManualChangingPage, setIsManualChangingPage] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(7);
  const highlightedRowsRef = useRef<Map<string, HTMLElement>>(new Map());
  const tableRef = useRef<any>(null);

  const [isDiffModalVisible, setIsDiffModalVisible] = useState(false);
  const [selectedNodeCode, setSelectedNodeCode] = useState({
    parent: {
      code: '',
      staticConfig: '',
      requirements: '',
    },
    child: {
      code: '',
      staticConfig: '',
      requirements: '',
    },
  });
  const [isLoadingCode, setIsLoadingCode] = useState(false);
  const [versionOptions, setVersionOptions] = useState<
    { label: string; value: string; versionId: string }[]
  >([]);
  const [selectedOption, setSelectedOption] = useState({
    original: {
      nodeName: '',
      versionId: '',
    },
    modified: {
      nodeName: '',
      versionId: '',
    },
  });
  const [selectedError, setSelectedError] = useState<ErrorDetails | null>(null);

  const [isAutoGenieNodesModalVisible, setIsAutoGenieNodesModalVisible] = useState(false);
  const [autoGenieNodesData, setAutoGenieNodesData] = useState<AutoGenieNodeDataType[]>([]);
  const [isLoadingAutoGenieNodes, setIsLoadingAutoGenieNodes] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');

  const [isBugFixerSessionModalVisible, setIsBugFixerSessionModalVisible] = useState(false);
  const [bugFixerSessionData, setBugFixerSessionData] = useState<BugFixerSessionDataType[]>([]);
  const [isLoadingBugFixerSessions, setIsLoadingBugFixerSessions] = useState(false);
  const [selectedRetryProcessId, setSelectedRetryProcessId] = useState<string>('');

  const agentOptions = useMemo(
    () => [
      { value: dictionary.BUG_FIXER, label: dictionary.BUG_FIXER },
      { value: dictionary.AUTO_GENIE, label: dictionary.AUTO_GENIE },
      { value: dictionary.AI_PARAMETER, label: dictionary.AI_PARAMETER },
      { value: dictionary.AI_INTERPRETATION, label: dictionary.AI_INTERPRETATION },
      { value: dictionary.WORKFLOW_REPORT, label: dictionary.WORKFLOW_REPORT },
    ],
    [dictionary],
  );

  const statusBadgeMap = useMemo(
    () => ({
      original: { status: 'default', text: 'Original' },
      pending: { status: 'default', text: 'Pending' },
      queuing: { status: 'default', text: 'Queuing' },
      cancelled: { status: 'default', text: 'Cancelled' },
      stopped: { status: 'default', text: 'Stopped' },
      running: { status: 'processing', text: 'Running' },
      debugging: { status: 'processing', text: 'Debugging' },
      finished: { status: 'success', text: 'Finished' },
      failed: { status: 'error', text: 'Failed' },
    }),
    [],
  );

  // const handleDownloadCSV = () => {
  //   // message.success('Downloading CSV...');
  // };

  const handleAgentCategoryChange = (value: string) => {
    setAgentCategory(value);
    setSelectedRows([]);
    setCurrentPage(1);
  };

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    setSelectedRows([]);
    setAgentCategory(dictionary.BUG_FIXER);
    setCurrentPage(1);
  };

  const groupByNodeId = (data: AnalysisDataType[]) => {
    const groupedData: Record<string, AnalysisDataType[]> = data.reduce((acc, current) => {
      const nodeId = current.node_id;
      if (!acc[nodeId]) {
        acc[nodeId] = [];
      }
      acc[nodeId].push(current);
      return acc;
    }, {});

    return Object.values(groupedData).map((group) => {
      const sortedGroup = group.sort(
        (a, b) => new Date(b.create_time).getTime() - new Date(a.create_time).getTime(),
      );
      const [newestRow, ...otherRows] = sortedGroup;

      return {
        ...newestRow,
        children: otherRows.length ? otherRows : undefined,
      };
    });
  };

  const checkNodeExists = useCallback(
    (nodeId: string): boolean => {
      return nodes.some((node) => node.id === nodeId.toString());
    },
    [nodes],
  );

  const handleNodeClickAndFocus = useCallback(
    (nodeId: string, nodeName?: string) => {
      const node = nodes.find((node) => node.id === nodeId.toString());

      if (!node) {
        message.warning(`Node "${nodeName || nodeId}" no longer exists on the analysis board`);
        return;
      }

      const position: number[] = [];
      instance.toObject().nodes.forEach((element) => {
        if (node && element.id === node.id) {
          position.push(element.position.x);
          position.push(element.position.y);
        }
      });

      setTemporaryCenteredNodeId(nodeId.toString());

      setTimeout(() => {
        setTemporaryCenteredNodeId(null);
      }, 800);

      setCenter(position[0] + 130, position[1] + 75, { duration: 0, zoom: 1 });
    },
    [nodes, instance, setTemporaryCenteredNodeId, setCenter],
  );

  const renderNodeName = (text: string, nodeId: string, record: any, isOldNode = false) => {
    const nodeExists = checkNodeExists(nodeId);
    const cellClass = isOldNode ? 'old-node-cell' : 'node-name-cell';

    if (!nodeExists) {
      return (
        <div className={cellClass} style={{ display: 'flex', alignItems: 'center' }}>
          <Tooltip title="This node has been deleted from the analysis board">
            <span
              style={{
                color: '#d9d9d9',
                cursor: 'not-allowed',
                opacity: 0.5,
              }}
            >
              {text}
            </span>
          </Tooltip>
        </div>
      );
    }

    return (
      <div className={cellClass} style={{ display: 'flex', alignItems: 'center' }}>
        <div className="node-name-cell">
          <a className="node-name" onClick={() => handleNodeClickAndFocus(nodeId, text)}>
            {text}
          </a>
        </div>
        {record.fbVersionId || record.functionBlockVersionId ? (
          <CodeOutlined
            className="code-icon"
            onClick={() => {
              setFbVersionId(record.fbVersionId || record.functionBlockVersionId);
            }}
          />
        ) : null}
      </div>
    );
  };

  useEffect(() => {
    setIsManualChangingPage(false);
  }, [currentSelectedNodes]);

  const findNodePageNumber = useCallback(
    (nodeId: string, data: AnalysisDataType[]) => {
      const index = data.findIndex((item) => item.node_id == nodeId);
      if (index === -1 && data.length > 0) {
        message.warn(`Node not found in the table data`);
        return null;
      }
      return Math.floor(index / pageSize) + 1;
    },
    [pageSize],
  );

  const findAndHighlightRows = useCallback(
    async (nodeIds: string[]) => {
      if (!isHighlightEnabled) return;

      highlightedRowsRef.current.forEach((element) => {
        element.classList.remove(style.highlightRow);
        element.classList.add(style.normalRow);
      });
      highlightedRowsRef.current.clear();

      const existingNodeIds = nodeIds.filter((nodeId) => checkNodeExists(nodeId));

      if (existingNodeIds.length === 0) {
        return;
      }

      if (existingNodeIds.length === 1) {
        const targetPage = findNodePageNumber(existingNodeIds[0], currentTableSource);
        if (targetPage && targetPage !== currentPage && !isManualChangingPage) {
          setCurrentPage(targetPage);
        }
      }

      existingNodeIds.forEach((nodeId) => {
        const element = document.getElementById(`row-${nodeId}`);
        if (element && !element.classList.contains(style.disabledRow)) {
          element.classList.remove(style.normalRow);
          element.classList.add(style.highlightRow);
          highlightedRowsRef.current.set(nodeId, element);

          if (nodeId === existingNodeIds[0]) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }
      });
    },
    [
      isHighlightEnabled,
      currentTableSource,
      currentPage,
      findNodePageNumber,
      isManualChangingPage,
      checkNodeExists,
    ],
  );

  const findBugFixerNodePageNumber = useCallback(
    (nodeId: string, data: BugFixerDataType[]) => {
      const index = data.findIndex(
        (item) => item.old_node_id == nodeId || item.new_node_id == nodeId,
      );
      if (index === -1 && data.length > 0) {
        message.warn(`Node not found in the table data`);
        return null;
      }
      return Math.floor(index / pageSize) + 1;
    },
    [pageSize],
  );

  const findAndHighlightBugFixerRows = useCallback(
    async (nodeIds: string[]) => {
      if (!isHighlightEnabled) return;

      document.querySelectorAll('td.ant-table-cell').forEach((td) => {
        td.classList.remove(style.highlightOldColumn, style.highlightNewColumn);
      });

      if (nodeIds.length === 1) {
        const targetPage = findBugFixerNodePageNumber(nodeIds[0], currentTableSource);
        if (targetPage && targetPage !== currentPage && !isManualChangingPage) {
          setCurrentPage(targetPage);
          await new Promise((resolve) => setTimeout(resolve, 100));
        }
      }

      nodeIds.forEach((nodeId) => {
        currentTableSource.forEach((row) => {
          const rowElement = document.getElementById(`row-${row.key}`);

          if (rowElement) {
            if (row.old_node_id.toString() === nodeId.toString() && row.old_node_id !== '-') {
              const oldNodeTd =
                rowElement.querySelector('td[data-column-key="old_node_name"]') ||
                rowElement.querySelector('td:nth-child(3)');

              if (oldNodeTd) {
                oldNodeTd.classList.add(style.highlightOldColumn);

                if (nodeId === nodeIds[0]) {
                  oldNodeTd.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
              }
            }

            if (row.new_node_id.toString() === nodeId.toString() && row.new_node_id !== '-') {
              const newNodeTd =
                rowElement.querySelector('td[data-column-key="new_node_name"]') ||
                rowElement.querySelector('td:nth-child(4)');

              if (newNodeTd) {
                newNodeTd.classList.add(style.highlightNewColumn);

                if (nodeId === nodeIds[0]) {
                  newNodeTd.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
              }
            }
          }
        });
      });
    },
    [
      isHighlightEnabled,
      currentTableSource,
      currentPage,
      findBugFixerNodePageNumber,
      isManualChangingPage,
    ],
  );

  const clearAllHighlights = useCallback(() => {
    highlightedRowsRef.current.forEach((element) => {
      element.classList.remove(style.highlightRow);
      element.classList.add(style.normalRow);
    });
    highlightedRowsRef.current.clear();
    document.querySelectorAll('td.ant-table-cell').forEach((td) => {
      td.classList.remove(style.highlightOldColumn, style.highlightNewColumn);
    });
  }, []);

  const handleTablePageChange = useCallback((pagination: any) => {
    setIsManualChangingPage(true);
    if (pagination.current > 0 && pagination.pageSize > 0) {
      setCurrentPage(pagination.current);
      setPageSize(pagination.pageSize);
    } else {
      console.error('Invalid pagination values:', pagination);
    }
  }, []);

  const handleHighlightToggle = useCallback((checked: boolean) => {
    setIsHighlightEnabled(checked);
  }, []);

  const handleEmptyRowsToggle = () => {
    setShowEmptyRows(!showEmptyRows);
  };

  useEffect(() => {
    if (!isHighlightEnabled) {
      clearAllHighlights();
      return;
    }

    if (activeTab === dictionary.ANALYSIS) {
      if (currentSelectedNodes && currentSelectedNodes.length > 0) {
        findAndHighlightRows(currentSelectedNodes.map((node) => node.id));
      } else {
        clearAllHighlights();
      }
    } else if (activeTab === dictionary.AGENT && agentCategory === dictionary.BUG_FIXER) {
      if (currentSelectedNodes && currentSelectedNodes.length > 0) {
        findAndHighlightBugFixerRows(currentSelectedNodes.map((node) => node.id));
      } else {
        document.querySelectorAll('td.ant-table-cell').forEach((td) => {
          td.classList.remove(style.highlightOldColumn, style.highlightNewColumn);
        });
      }
    }
  }, [
    currentSelectedNodes,
    findAndHighlightRows,
    findAndHighlightBugFixerRows,
    isHighlightEnabled,
    activeTab,
    agentCategory,
    clearAllHighlights,
  ]);

  const fetchCodeComparison = async (originalId: string, modifiedId: string) => {
    try {
      setIsLoadingCode(true);

      const fetchContent = async (versionId: string, fileName: string) => {
        try {
          const response = await requestFBVersionContent(versionId, fileName);
          return response.data || '';
        } catch (error) {
          console.warn(`Failed to fetch ${fileName} for version ${versionId}:`, error);
          return 'Failed to load content';
        }
      };

      const [originalCode, originalConfig, originalReq, modifiedCode, modifiedConfig, modifiedReq] =
        await Promise.all([
          fetchContent(originalId, 'function_block.py'),
          fetchContent(originalId, 'static-config.json'),
          fetchContent(originalId, 'requirements.txt'),
          fetchContent(modifiedId, 'function_block.py'),
          fetchContent(modifiedId, 'static-config.json'),
          fetchContent(modifiedId, 'requirements.txt'),
        ]);

      setSelectedNodeCode({
        parent: { code: originalCode, staticConfig: originalConfig, requirements: originalReq },
        child: { code: modifiedCode, staticConfig: modifiedConfig, requirements: modifiedReq },
      });
    } catch (error) {
      console.error('Error fetching version content:', error);
      message.error('An error occurred while fetching code comparison data.');
    } finally {
      setIsLoadingCode(false);
    }
  };

  const initializeVersionList = async (
    record: BugFixerDataType,
    attempt_record: BugFixerComputationDataType,
  ) => {
    try {
      setIsLoadingCode(true);

      const options = [
        {
          label: `${dictionary.ORIGINAL}: ${record.old_node_name}`,
          value: `${dictionary.ORIGINAL}: ${record.old_node_name}`,
          versionId: record.old_node_version_id,
        },
      ];

      if (record.computations) {
        const totalAttempts = record.computations.length;
        record.computations.forEach((child, index) => {
          options.push({
            label: `${dictionary.ATTEMPT} ${totalAttempts - index}`,
            value: `${dictionary.ATTEMPT} ${totalAttempts - index}`,
            versionId: child.functionBlockVersionId,
          });
        });
      }

      setVersionOptions(options);
      setSelectedOption({
        original: {
          nodeName: record.old_node_name,
          versionId: record.old_node_version_id,
        },
        modified: {
          nodeName: attempt_record.attemptName,
          versionId: attempt_record.functionBlockVersionId,
        },
      });

      await fetchCodeComparison(record.old_node_version_id, attempt_record.functionBlockVersionId);
      setIsDiffModalVisible(true);
    } catch (error) {
      console.error('Failed to initialize version comparison:', error);
      message.error('An error occurred while preparing version comparison.');
    } finally {
      setIsLoadingCode(false);
    }
  };

  const updateComparison = (newSelectedOption) => {
    setSelectedOption(newSelectedOption);
    fetchCodeComparison(newSelectedOption.original.versionId, newSelectedOption.modified.versionId);
  };

  const handleOriginalChange = (value, option) => {
    updateComparison({
      ...selectedOption,
      original: { nodeName: value, versionId: option.versionId },
    });
  };

  const handleModifiedChange = (value, option) => {
    updateComparison({
      ...selectedOption,
      modified: { nodeName: value, versionId: option.versionId },
    });
  };

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

  const handleCopyCode = (content: string) => {
    try {
      writeToClipboard(content);
      message.success('Code copied to clipboard!');
    } catch (error) {
      message.error('Failed to copy code.');
      console.error('Copy failed:', error);
    }
  };

  const fetchAutoGenieNodes = async (sessionId: string) => {
    try {
      setIsLoadingAutoGenieNodes(true);
      const response = await requestDynamicGenerationNodesBySession(sessionId);
      const formattedData = response.data.map((item, index) => ({
        key: index,
        ...item,
      }));
      setAutoGenieNodesData(formattedData);
      setSelectedSessionId(sessionId);
      setIsAutoGenieNodesModalVisible(true);
    } catch (error) {
      console.error('Error fetching auto genie nodes:', error);
      message.error('Failed to fetch auto genie nodes');
    } finally {
      setIsLoadingAutoGenieNodes(false);
    }
  };

  const fetchBugFixerSessions = async (retryProcessId: string) => {
    try {
      setIsLoadingBugFixerSessions(true);
      const response = await requestBugFixerSessions(retryProcessId);
      const formattedData = response.data.map((item, index) => ({
        key: index,
        ...item,
      }));
      setBugFixerSessionData(formattedData);
      setSelectedRetryProcessId(retryProcessId);
      setIsBugFixerSessionModalVisible(true);
    } catch (error) {
      console.error('Error fetching bug fixer sessions:', error);
      message.error('Failed to fetch bug fixer sessions');
    } finally {
      setIsLoadingBugFixerSessions(false);
    }
  };

  const analysisTableColumns: TableColumnsType<AnalysisDataType> = useMemo(
    () => [
      {
        title: `${dictionary.NODE}`,
        width: 40,
        dataIndex: 'node_name',
        key: 'node_name',
        fixed: 'left',
        render: (text, record) => renderNodeName(text, record.node_id, record),
      },
      {
        title: `${dictionary.STATUS}`,
        width: 40,
        dataIndex: 'status',
        key: 'status',
        render: (status) => {
          const badgeInfo = statusBadgeMap[status] || { status: 'warning', text: 'Unknown' };
          return (
            <Badge
              status={badgeInfo.status}
              text={badgeInfo.text}
              style={{ whiteSpace: 'nowrap' }}
            />
          );
        },
      },
      {
        title: `${dictionary.CREATED_TIME}`,
        dataIndex: 'create_time',
        key: 'create_time',
        width: 50,
        sorter: {
          compare: (a, b) => new Date(a.create_time).getTime() - new Date(b.create_time).getTime(),
        },
      },
      {
        title: `${dictionary.DURATION} (s)`,
        dataIndex: 'duration',
        key: 'duration',
        width: 32,
      },
      {
        title: `${dictionary.USER}`,
        dataIndex: 'user_name',
        key: 'user_name',
        width: 35,
        render: (text) => (
          <div className="user-cell">
            <UserOutlined /> {text}
          </div>
        ),
      },
    ],
    [selectedRows, currentTableSource],
  );

  const autoGenieTableColumns: TableColumnsType<AutoGenieSessionDataType> = [
    {
      title: `${dictionary.SOURCE_NODE}`,
      dataIndex: 'sourceNodeId',
      key: 'sourceNodeId',
      width: 120,
      render: (text) => {
        const nodeExists = checkNodeExists(text.toString());

        if (!nodeExists) {
          return (
            <Tooltip title="This source node has been deleted from the analysis board">
              <span
                style={{
                  color: '#d9d9d9',
                  cursor: 'not-allowed',
                  opacity: 0.5,
                }}
              >
                {text}
              </span>
            </Tooltip>
          );
        }

        return <a onClick={() => handleNodeClickAndFocus(text.toString())}>{text}</a>;
      },
    },
    {
      title: `${dictionary.GENERATED_NODES}`,
      width: 100,
      render: (record) => (
        <Tooltip title="View Generated Nodes">
          <InfoCircleOutlined
            onClick={() => fetchAutoGenieNodes(record.id.toString())}
            style={{ cursor: 'pointer' }}
          />
        </Tooltip>
      ),
    },
    {
      title: `${dictionary.CREATED_TIME}`,
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 120,
    },
    {
      title: `${dictionary.MODEL}`,
      dataIndex: 'model',
      key: 'model',
      width: 100,
    },
    {
      title: `${dictionary.PROMPT_TOKENS}`,
      dataIndex: 'promptTokens',
      key: 'promptTokens',
      width: 100,
    },
    {
      title: `${dictionary.COMPLETION_TOKENS}`,
      dataIndex: 'completionTokens',
      key: 'completionTokens',
      width: 130,
    },
    {
      title: `${dictionary.TOTAL_TOKENS}`,
      dataIndex: 'totalTokens',
      key: 'totalTokens',
      width: 100,
    },
  ];

  const bugFixerTableColumns: TableColumnsType<BugFixerDataType> = [
    {
      title: `${dictionary.ORIGINAL_NODE}`,
      width: 40,
      dataIndex: 'old_node_name',
      key: 'old_node_name',
      render: (text, record) =>
        text && text !== '-' ? (
          renderNodeName(text, record.old_node_id, record, true)
        ) : (
          <DashOutlined />
        ),
    },
    {
      title: `${dictionary.NEW_NODE}`,
      width: 40,
      dataIndex: 'new_node_name',
      key: 'new_node_name',
      render: (text, record) =>
        text && text !== '-' ? renderNodeName(text, record.new_node_id, record) : <DashOutlined />,
    },
    {
      title: `${dictionary.STATUS}`,
      width: 35,
      dataIndex: 'status',
      key: 'status',
      ellipsis: {
        showTitle: false,
      },
      render: (status) => {
        const badgeInfo = statusBadgeMap[status] || { status: 'warning', text: 'Unknown' };
        return (
          <Badge
            status={badgeInfo.status}
            text={badgeInfo.text}
            color={badgeInfo.color}
            style={{ whiteSpace: 'nowrap' }}
          />
        );
      },
    },
    {
      title: `${dictionary.CREATED_TIME}`,
      dataIndex: 'create_time',
      key: 'create_time',
      width: 45,
      sorter: {
        compare: (a, b) => new Date(a.create_time).getTime() - new Date(b.create_time).getTime(),
      },
    },
    {
      title: `${dictionary.MAX_RETRIES}`,
      width: 30,
      dataIndex: 'max_retries',
      key: 'max_retries',
    },
    {
      title: `${dictionary.REMAINING_RETRIES}`,
      width: 40,
      dataIndex: 'rest_retries',
      key: 'rest_retries',
    },
    {
      title: `${dictionary.TOTAL_COMPLETION_TOKENS}`,
      width: 40,
      dataIndex: 'total_completion_tokens',
      key: 'total_completion_tokens',
    },
    {
      title: `${dictionary.TOTAL_PROMPT_TOKENS}`,
      width: 40,
      dataIndex: 'total_prompt_tokens',
      key: 'total_prompt_tokens',
    },
    {
      title: `${dictionary.TOTAL_TOKENS}`,
      width: 30,
      dataIndex: 'total_tokens',
      key: 'total_tokens',
    },
    {
      title: `${dictionary.USER_PROMPT}`,
      width: 50,
      dataIndex: 'user_prompt',
      key: 'user_prompt',
      render: (text) => (
        <div className="user-prompt-cell">
          <span className="user-prompt-text">{text}</span>
          {text && text.trim() !== '-' && (
            <CopyOutlined
              className="copy-icon"
              onClick={() => handleCopyCode(text)}
              style={{ marginLeft: '8px' }}
            />
          )}
        </div>
      ),
    },
    {
      title: `${dictionary.SESSIONS}`,
      width: 30,
      render: (record) => (
        <Tooltip title="View Bug Fixer Sessions">
          <InfoCircleOutlined
            onClick={() => fetchBugFixerSessions(record.key.toString())}
            style={{ cursor: 'pointer' }}
          />
        </Tooltip>
      ),
    },
  ];

  const bugFixerComputationTableColumns: TableColumnsType<BugFixerComputationDataType> = [
    {
      title: `${dictionary.ATTEMPT}`,
      dataIndex: 'attemptName',
      key: 'attemptName',
      width: 70,
      render: (text, record) => {
        if (!text || text === '-') {
          return <DashOutlined />;
        }

        const nodeExists = checkNodeExists(record.attemptNodeId);

        if (!nodeExists) {
          return (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Tooltip title="This attempt node has been deleted from the analysis board">
                <span
                  style={{
                    color: '#d9d9d9',
                    cursor: 'not-allowed',
                    opacity: 0.5,
                  }}
                >
                  {text}
                </span>
              </Tooltip>
              <>
                {record.functionBlockVersionId && record.functionBlockVersionId !== '-' ? (
                  <Tooltip title="View Code">
                    <CodeOutlined
                      className="code-icon"
                      onClick={() => {
                        setFbVersionId(record.functionBlockVersionId);
                      }}
                    />
                  </Tooltip>
                ) : null}
                {record.attemptNodeId && record.attemptNodeId !== '-' ? (
                  <Tooltip title={dictionary.COMPARE_WITH_ORIGINAL_NODE}>
                    <DiffOutlined
                      className="code-icon"
                      onClick={() => {
                        initializeVersionList(currentTableSource[record.parentIndex], record);
                      }}
                    />
                  </Tooltip>
                ) : null}
                {record.attemptName &&
                record.attemptName.split(' ')[1] ==
                  currentTableSource[record.parentIndex].computations.length ? (
                  <Tooltip title="Latest node generated by bug fixer">
                    <Badge
                      count="in use"
                      style={{
                        backgroundColor: '#52c41a',
                        fontSize: '11px',
                        marginLeft: '10px',
                        cursor: 'default',
                      }}
                    />
                  </Tooltip>
                ) : null}
              </>
            </div>
          );
        }

        return (
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div className="node-name-cell">
              <a
                className="node-name"
                onClick={() => handleNodeClickAndFocus(record.attemptNodeId)}
              >
                {text}
              </a>
            </div>
            <>
              {record.functionBlockVersionId && record.functionBlockVersionId !== '-' ? (
                <Tooltip title="View Code">
                  <CodeOutlined
                    className="code-icon"
                    onClick={() => {
                      setFbVersionId(record.functionBlockVersionId);
                    }}
                  />
                </Tooltip>
              ) : null}
              {record.attemptNodeId && record.attemptNodeId !== '-' ? (
                <Tooltip title={dictionary.COMPARE_WITH_ORIGINAL_NODE}>
                  <DiffOutlined
                    className="code-icon"
                    onClick={() => {
                      initializeVersionList(currentTableSource[record.parentIndex], record);
                    }}
                  />
                </Tooltip>
              ) : null}
              {record.attemptName &&
              record.attemptName.split(' ')[1] ==
                currentTableSource[record.parentIndex].computations.length ? (
                <Tooltip title="Latest node generated by bug fixer">
                  <Badge
                    count="in use"
                    style={{
                      backgroundColor: '#52c41a',
                      fontSize: '11px',
                      marginLeft: '10px',
                      cursor: 'default',
                    }}
                  />
                </Tooltip>
              ) : null}
            </>
          </div>
        );
      },
    },
    {
      title: `${dictionary.STATUS}`,
      dataIndex: 'computationState',
      key: 'computationState',
      width: 40,
      render: (status) => {
        const badgeInfo = statusBadgeMap[status] || { status: 'warning', text: 'Unknown' };
        return (
          <Badge
            status={badgeInfo.status}
            text={badgeInfo.text}
            color={badgeInfo.color}
            style={{ whiteSpace: 'nowrap' }}
          />
        );
      },
    },
    {
      title: `${dictionary.START_TIME}`,
      dataIndex: 'startTime',
      key: 'startTime',
      width: 50,
    },
    {
      title: `${dictionary.DURATION} (s)`,
      dataIndex: 'duration',
      key: 'duration',
      width: 40,
    },
    {
      title: `${dictionary.ERROR_DESCRIPTION}`,
      width: 30,
      render: (record) =>
        record.errorDescription ? (
          <Tooltip title="View Error Details">
            <Tooltip title="View Error Details">
              <InfoCircleOutlined onClick={() => handleErrorClick(record)} />
            </Tooltip>
          </Tooltip>
        ) : (
          <DashOutlined />
        ),
    },
  ];

  const CodeDiffEditor = ({ title, language, original, modified, height }) => (
    <div style={{ position: 'relative', flex: '1' }}>
      <div style={{ padding: '10px 0 0 10px', fontWeight: 'bold' }}>{title}:</div>
      <DiffEditor
        language={language}
        theme="vs-dark"
        height={height}
        original={original}
        modified={modified}
        options={{
          fontSize: 14,
          readOnly: true,
          renderSideBySide: true,
          minimap: { enabled: false },
          automaticLayout: true,
        }}
      />
    </div>
  );

  const renderDiffModal = () => {
    const mainEditorHeight = Math.floor((window.innerHeight * 0.85 - 120) * 0.6);
    const subEditorHeight = Math.floor((window.innerHeight * 0.85 - 120) * 0.4);

    return (
      <Modal
        centered
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
              <div> {dictionary.CODE_DIFF + ': '}</div>
              <Select
                style={{ width: 200 }}
                options={versionOptions}
                value={selectedOption.original.nodeName}
                onChange={handleOriginalChange}
                placeholder="Select original version"
                disabled={isLoadingCode}
              />
              <div>vs</div>
              <Select
                style={{ width: 200 }}
                options={versionOptions}
                value={selectedOption.modified.nodeName}
                onChange={handleModifiedChange}
                placeholder="Select modified version"
                disabled={isLoadingCode}
              />
            </div>
          </div>
        }
        open={isDiffModalVisible}
        onCancel={() => {
          setVersionOptions([]);
          setIsDiffModalVisible(false);
          setSelectedOption({
            original: { nodeName: '', versionId: '' },
            modified: { nodeName: '', versionId: '' },
          });
          setSelectedNodeCode({
            parent: {
              code: '',
              staticConfig: '',
              requirements: '',
            },
            child: {
              code: '',
              staticConfig: '',
              requirements: '',
            },
          });
        }}
        width="100vw"
        footer={null}
        bodyStyle={{
          padding: 10,
          overflowY: 'auto',
          position: 'relative',
        }}
      >
        {isLoadingCode ? (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <LoadingOutlined /> Loading code...
          </div>
        ) : (
          <div style={{ height: '100%', position: 'relative', padding: '0 10px' }}>
            <CodeDiffEditor
              title="Core Code"
              language="python"
              original={selectedNodeCode.parent.code}
              modified={selectedNodeCode.child.code}
              height={`${mainEditorHeight}px`}
            />
            <div style={{ display: 'flex', gap: '20px', height: `${subEditorHeight}px` }}>
              <CodeDiffEditor
                title="Static Configure"
                language="json"
                original={selectedNodeCode.parent.staticConfig}
                modified={selectedNodeCode.child.staticConfig}
                height={subEditorHeight - 40}
              />
              <CodeDiffEditor
                title="Requirements"
                language="text"
                original={selectedNodeCode.parent.requirements}
                modified={selectedNodeCode.child.requirements}
                height={subEditorHeight - 40}
              />
            </div>
          </div>
        )}
      </Modal>
    );
  };

  const renderErrDetailModal = () => {
    return (
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
              <span style={{ fontWeight: 'bold' }}>{dictionary.ERROR_DESCRIPTION + ':'}</span>
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
                <span style={{ fontWeight: 'bold' }}>{dictionary.ERROR_MESSAGE + ':'}</span>
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
                <span style={{ fontWeight: 'bold' }}>{dictionary.SUGGESTED_SOLUTION + ':'}</span>
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
    );
  };

  const renderAutoGenieNodesModal = () => {
    const nodeColumns: TableColumnsType<AutoGenieNodeDataType> = [
      {
        title: 'Node Name',
        dataIndex: 'name',
        key: 'name',
        width: 200,
        render: (text, record) => (
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div className="node-name-cell">
              <a
                className="node-name"
                onClick={() => handleNodeClickAndFocus(record.id.toString())}
              >
                {text}
              </a>
            </div>
            {record.functionBlockVersionId ? (
              <CodeOutlined
                className="code-icon"
                onClick={() => {
                  setFbVersionId(record.functionBlockVersionId);
                }}
              />
            ) : null}
          </div>
        ),
      },
      {
        title: 'Status',
        dataIndex: 'state',
        key: 'state',
        width: 100,
        render: (status) => {
          const badgeInfo = statusBadgeMap[status] || { status: 'warning', text: 'Unknown' };
          return (
            <Badge
              status={badgeInfo.status}
              text={badgeInfo.text}
              style={{ whiteSpace: 'nowrap' }}
            />
          );
        },
      },
      {
        title: 'Type',
        dataIndex: 'type',
        key: 'type',
        width: 120,
      },
      {
        title: 'Tag',
        dataIndex: 'tag',
        key: 'tag',
        width: 150,
      },
      {
        title: 'Created Time',
        dataIndex: 'createdTime',
        key: 'createdTime',
        width: 150,
        render: (timestamp) => new Date(timestamp).toLocaleString(),
      },
      {
        title: 'System Env',
        dataIndex: 'systemEnv',
        key: 'systemEnv',
        width: 120,
      },
    ];

    return (
      <Modal
        width={window.innerWidth * 0.9}
        centered
        title={`Generated Nodes - Session ID: ${selectedSessionId}`}
        open={isAutoGenieNodesModalVisible}
        onCancel={() => {
          setIsAutoGenieNodesModalVisible(false);
          setAutoGenieNodesData([]);
          setSelectedSessionId('');
        }}
        footer={null}
        bodyStyle={{
          height: window.innerHeight * 0.7,
          overflowY: 'auto',
        }}
      >
        <Table
          columns={nodeColumns}
          dataSource={autoGenieNodesData}
          loading={isLoadingAutoGenieNodes}
          pagination={{
            pageSize: 10,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items`,
          }}
          scroll={{ x: 'max-content' }}
        />
      </Modal>
    );
  };

  const renderBugFixerSessionModal = () => {
    const sessionColumns: TableColumnsType<BugFixerSessionDataType> = [
      {
        title: 'Node ID',
        dataIndex: 'nodeId',
        key: 'nodeId',
        width: 80,
      },
      {
        title: 'Created At',
        dataIndex: 'createdAt',
        key: 'createdAt',
        width: 150,
      },
      {
        title: 'Model',
        dataIndex: 'model',
        key: 'model',
        width: 200,
      },
      {
        title: 'Prompt Tokens',
        dataIndex: 'promptTokens',
        key: 'promptTokens',
        width: 100,
      },
      {
        title: 'Completion Tokens',
        dataIndex: 'completionTokens',
        key: 'completionTokens',
        width: 130,
      },
      {
        title: 'Total Tokens',
        dataIndex: 'totalTokens',
        key: 'totalTokens',
        width: 100,
      },
    ];

    return (
      <Modal
        width={window.innerWidth * 0.8}
        centered
        title={`Bug Fixer Sessions - Retry Process ID: ${selectedRetryProcessId}`}
        open={isBugFixerSessionModalVisible}
        onCancel={() => {
          setIsBugFixerSessionModalVisible(false);
          setBugFixerSessionData([]);
          setSelectedRetryProcessId('');
        }}
        footer={null}
        bodyStyle={{
          height: window.innerHeight * 0.6,
          overflowY: 'auto',
        }}
      >
        <Table
          columns={sessionColumns}
          dataSource={bugFixerSessionData}
          loading={isLoadingBugFixerSessions}
          pagination={{
            pageSize: 10,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items`,
          }}
          scroll={{ x: 'max-content' }}
        />
      </Modal>
    );
  };

  const fetchAnalysisTableData = useCallback(async () => {
    try {
      setCurrentTableLoading(true);
      const { data: nodeDetail } = await requestDashboardList(analysisId ?? '');
      const tableData = await Promise.all(
        nodeDetail.map(async (nodeDetail, index) => {
          const nodeName = nodeDetail.nodeName;
          const fbVersionId = nodeDetail.functionBlockVersionId;
          const nodeId = nodeDetail.nodeId;
          const status = nodeDetail.nodeState;
          const createTime = new Date(nodeDetail.nodeCreatedTime).toLocaleString();
          const duration = nodeDetail.computationDuration;

          return {
            key: index,
            node_name: nodeName,
            fbVersionId: fbVersionId,
            node_id: nodeId,
            status: status,
            create_time:
              status !== 'running' || status !== 'debugging' ? createTime : <DashOutlined />,
            duration: status !== 'running' || status !== 'debugging' ? duration : <DashOutlined />,
            user_name: userInfo?.userName || 'guest',
          };
        }),
      );

      const groupedTableData = groupByNodeId(tableData.filter(Boolean));
      setCurrentColumns(analysisTableColumns);
      setCurrentTableSource(groupedTableData);
    } catch (error) {
      console.error('Failed to fetch table data:', error);
    } finally {
      setCurrentTableLoading(false);
    }
  }, [nodes]);

  const fetchAutoGenieTableData = useCallback(async () => {
    setCurrentTableLoading(true);
    try {
      const generationsResponse = await requestDynamicGenerationListByAnalysis(analysisId ?? '');

      const allSessions: any[] = [];
      for (const generation of generationsResponse.data) {
        try {
          const sessionsResponse = await requestDynamicGenerationSessions(generation.generationId);
          const sessionsWithGenInfo = sessionsResponse.data.map((session) => ({
            key: `${generation.generation_id}-${session.id}`,
            ...session,
          }));
          allSessions.push(...sessionsWithGenInfo);
        } catch (error) {
          console.warn(
            `Failed to fetch sessions for generation ${generation.generation_id}:`,
            error,
          );
        }
      }

      setCurrentColumns(autoGenieTableColumns);
      setCurrentTableSource(allSessions);
    } catch (error) {
      console.error('Error fetching auto genie data:', error);
    } finally {
      setCurrentTableLoading(false);
    }
  }, [analysisId]);

  const expandedRowRender = (record: BugFixerDataType) => (
    <Table
      columns={bugFixerComputationTableColumns}
      dataSource={record.computations}
      pagination={false}
    />
  );

  const fetchBugFixerTableData = useCallback(async () => {
    setCurrentTableLoading(true);
    try {
      const response = await requestBugFixerNodeListByAnalysis(analysisId ?? '');
      let formattedData = response.data.map((item, parentIndex) => ({
        key: item.id,
        old_node_name: item.old_node?.name || '-',
        old_node_id: item.old_node?.id || '-',
        old_node_version_id: item.old_node?.functionBlockVersionId || '-',
        new_node_name: item.new_node?.name || '-',
        new_node_id: item.new_node?.id || '-',
        new_node_version_id: item.new_node?.functionBlockVersionId || '-',
        status: item.state,
        create_time: item.createdTime,
        max_retries: item.maxRetry,
        rest_retries: item.restRetry,
        total_completion_tokens: item.totalCompletionTokens,
        total_prompt_tokens: item.totalPromptTokens,
        total_tokens: item.totalTokens,
        user_prompt: item.userPrompt || '-',
        computations: item.computations.map((comp, compIndex) => ({
          key: comp.id,
          attemptNodeId: comp.functionBlockId,
          attemptName: `Attempt ${item.computations.length - compIndex}`,
          functionBlockVersionId: comp.functionBlockVersionId,
          computationState: comp.computationState,
          startTime: new Date(comp.startTime).toLocaleString(),
          duration: comp.duration.toFixed(2),
          errorDescription: comp.errorDescription || 'No Error',
          optimizedErrorDescription: comp.optimizedErrorDescription || 'No Error',
          parentIndex,
        })),
      }));

      if (!showEmptyRows) {
        formattedData = formattedData.filter(
          (item) => !(item.old_node_name === '-' && item.new_node_name === '-'),
        );
      }

      setCurrentColumns(bugFixerTableColumns);
      setCurrentTableSource(formattedData);
    } catch (error) {
      console.error('Error fetching bug fixer data:', error);
    } finally {
      setCurrentTableLoading(false);
    }
  }, [nodes, showEmptyRows]);

  const fetchAIParameterTableData = useCallback(async () => {
    setCurrentColumns([]);
    setCurrentTableSource([]);
  }, [nodes]);

  const fetchAIInterpretationTableData = useCallback(async () => {
    setCurrentColumns([]);
    setCurrentTableSource([]);
  }, [nodes]);

  const fetchWorkflowReportTableData = useCallback(async () => {
    setCurrentColumns([]);
    setCurrentTableSource([]);
  }, [nodes]);

  useEffect(() => {
    if (isShowAIDashboard && analysisUpdatedTime) {
      switch (activeTab) {
        case dictionary.ANALYSIS:
          fetchAnalysisTableData();
          break;
        case dictionary.AGENT:
          switch (agentCategory) {
            case dictionary.AUTO_GENIE:
              fetchAutoGenieTableData();
              break;
            case dictionary.BUG_FIXER:
              fetchBugFixerTableData();
              break;
            case dictionary.AI_PARAMETER:
              fetchAIParameterTableData();
              break;
            case dictionary.AI_INTERPRETATION:
              fetchAIInterpretationTableData();
              break;
            case dictionary.WORKFLOW_REPORT:
              fetchWorkflowReportTableData();
              break;
            default:
              console.error('Invalid agent category:', agentCategory);
          }
          break;
        default:
          console.error('Invalid active tab:', activeTab);
      }
    }
  }, [isShowAIDashboard, analysisUpdatedTime, activeTab, agentCategory, showEmptyRows]);

  return (
    <div className={style.rightSider}>
      {isShowAIDashboard ? (
        <div className="dashboard-container">
          <div className="dashboard-title-container">
            <span className="dashboard-title">
              {dictionary.TASK}
              {/* <Button
                icon={<DownloadOutlined />}
                onClick={handleDownloadCSV}
                disabled={selectedRows.length === 0}
                style={{ marginLeft: '20px' }}
              >
                {dictionary.DOWNLOAD_CSV}
              </Button> */}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              <Tooltip title="In highlight mode, the selected nodes will be highlighted in the table.">
                <Switch
                  checkedChildren={
                    <span>
                      <HighlightOutlined /> {dictionary.HIGHLIGHT}
                    </span>
                  }
                  unCheckedChildren="Highlight"
                  checked={isHighlightEnabled}
                  onChange={handleHighlightToggle}
                />
              </Tooltip>
              <CloseOutlined
                onClick={() => setIsCloseBtnClicked(true)}
                style={{ cursor: 'pointer' }}
              />
            </div>
          </div>
          <div className="dashboard-content">
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                marginBottom: '16px',
              }}
            >
              <Segmented
                block
                options={[dictionary.ANALYSIS, dictionary.AGENT]}
                value={activeTab}
                onChange={(value) => handleTabChange(value.toString())}
                style={{
                  borderRadius: '6px',
                  padding: '5px',
                  width: '100%',
                  fontSize: '14px',
                  fontWeight: '500',
                  font: 'Roboto',
                }}
              />
            </div>
            {activeTab === dictionary.AGENT && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '10px',
                  width: '99%',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontWeight: 500 }}>{dictionary.AGENT_CATEGORY}:</span>
                  <Select
                    options={agentOptions}
                    value={agentCategory}
                    onChange={handleAgentCategoryChange}
                  />
                </div>
                {agentCategory === dictionary.BUG_FIXER && currentTableSource.length > 0 && (
                  <Tooltip title="Hide rows where both original and new nodes are empty">
                    <Switch
                      checkedChildren={<span>{dictionary.SHOW_EMPTY_ROWS}</span>}
                      unCheckedChildren={dictionary.HIDE_EMPTY_ROWS}
                      checked={showEmptyRows}
                      onChange={handleEmptyRowsToggle}
                    />
                  </Tooltip>
                )}
              </div>
            )}
            <Table
              ref={tableRef}
              columns={currentColumns}
              dataSource={currentTableSource}
              loading={currentTableLoading}
              scroll={{
                x: '1000',
                y: activeTab === dictionary.ANALYSIS ? 'calc(88vh - 250px)' : 'calc(88vh - 400px)',
              }}
              pagination={{
                current: currentPage,
                pageSize: pageSize,
                position: ['topLeft'],
                showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items`,
              }}
              expandable={
                activeTab === dictionary.AGENT && agentCategory === dictionary.BUG_FIXER
                  ? { expandedRowRender, columnWidth: 20 }
                  : undefined
              }
              onChange={handleTablePageChange}
              onRow={(record) => ({
                id:
                  activeTab === dictionary.AGENT && agentCategory === dictionary.BUG_FIXER
                    ? `row-${record.key}`
                    : `row-${record.node_id}`,
                className:
                  isHighlightEnabled &&
                  currentSelectedNodes?.some((node) =>
                    activeTab === dictionary.AGENT && agentCategory === dictionary.BUG_FIXER
                      ? record.old_node_id === node.id || record.new_node_id === node.id
                      : record.node_id === node.id,
                  )
                    ? style.highlightRow
                    : style.normalRow,
              })}
              rowSelection={{
                selectedRowKeys: selectedRows,
                onChange: (selectedRowKeys) => {
                  setSelectedRows(selectedRowKeys);
                },
                columnWidth: 15,
              }}
            />
          </div>
          {renderDiffModal()}
          {renderErrDetailModal()}
          {renderAutoGenieNodesModal()}
          {renderBugFixerSessionModal()}
        </div>
      ) : null}
    </div>
  );
}
