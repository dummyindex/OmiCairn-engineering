import { NODE_FONT_FAMILY } from '@/constants/font';
import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { AnalysisType } from '@/constants/analysis';
import { NodeState, NodeType } from '@/constants/node';
import { requestLatestComputation } from '@/request/computation';
import { requestDataInfo, requestDownloadDataSource } from '@/request/data';
import { cutString, cutStringByCharType } from '@/util/stringHelpers';
import VisualizerAgentModal from './computationNodeV2/visualizerModal';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  CodeOutlined,
  ControlOutlined,
  CopyOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  EllipsisOutlined,
  FileTextOutlined,
  HistoryOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  LockOutlined,
  PlaySquareOutlined,
  SisternodeOutlined,
  StarOutlined,
  SubnodeOutlined,
  ThunderboltOutlined,
  ToolOutlined,
  RightOutlined,
  LeftOutlined,
  WarningFilled,
} from '@ant-design/icons';
import {
  Button,
  Checkbox,
  Divider,
  Dropdown,
  Image,
  Menu,
  message,
  Modal,
  Popover,
  Space,
  Spin,
  Tag,
} from 'antd';
// import 'antd/dist/antd.css';
import promiseConfirm from '@/components/common/promiseConfirm';
import { requestGetFigureInfo } from '@/request/attachedData';
import { downloadFile } from '@/request/awsOperation';
import { requestCreateEdge } from '@/request/edge';
import { requestListFigureByNodeId } from '@/request/figure';
import {
  requestCancelSubtreeComputations,
  requestContinueDynamicGeneration,
  requestCreateNode,
  requestDynamicGenerationPlanGet,
  requestGenerateBranchReport,
  requestGenerateBranchReportAutomated,
  requestGetDynamicGeneration,
  requestPreviousNodeList,
} from '@/request/node';
import { FlowTool } from '@/util/flowTool';
import { getLocationParams } from '@/util/getUrl';
import { writeToClipboard } from '@/util/operationTools';
import { downloadJsonText } from '@/util/saveHelpers';
import { ProjectOutlined } from '@ant-design/icons';
import { Collapse } from 'antd';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Handle, Position, useReactFlow, useViewport } from 'reactflow';
import { useModel } from 'umi';
import CodeAgentMessageDialog from './CodeAgentMessageDialog';
import './CustomCheckbox.css';
import styles from './overview.less';
import CodeAgentInvokeDialog from './CodeAgentInvokeDialog';
import FBStructureDialog from './FBStructureDialog';
import { PresetFBs } from '@/constants/functionBlock';
import JobReviewErrorModal from './computationNodeV2/jobReviewErrorModal';
import ProgrammingAgentModal from './computationNodeV2/programmingAgentModal';
import ReporterFunctionBlockSelectionModal from './ReporterFunctionBlockSelectionModal';
import ReporterAutomatedSelectionModal from './ReporterAutomatedSelectionModal';

export interface PlanDetails {
  generationId: string;
  nodeId: string;
  steps: string;
}

const { Panel } = Collapse;
const { confirm } = Modal;

const bgColorMap: any = {
  [NodeState.ORIGINAL]: '#8cebdeff',
  [NodeState.RUNNING]: '#93f1eaff',
  [NodeState.FINISHED]: '#7c73f5ff',
  [NodeState.FAILED]: '#db640fff',
  [NodeState.PENDING]: '#27dbc3ff',
  [NodeState.DEBUGGING]: '#27dbc3ff',
  [NodeState.GENERATING]: '#27dbc3ff',
  [NodeState.BEAUTIFYING]: '#27dbc3ff',
  [NodeState.CANCELLED]: '#b7f1faff',
};

const stateFontColorMap: any = {
  [NodeState.ORIGINAL]: '#000',
  [NodeState.RUNNING]: '#fff',
  [NodeState.FINISHED]: '#fefeffff',
  [NodeState.FAILED]: '#fff',
  [NodeState.PENDING]: '#fff',
  [NodeState.DEBUGGING]: '#fff',
  [NodeState.GENERATING]: '#fff',
  [NodeState.BEAUTIFYING]: '#fff',
  [NodeState.CANCELLED]: '#000',
};

const useNodeVisibility = (nodeId: string) => {
  const { getNodes } = useReactFlow();
  const viewport = useViewport();
  const [isVisible, setIsVisible] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState(0);

  const {
    isShowMenu,
    isShowVisual,
    isShowAIDashboard,
    leftSiderWidth,
    rightSiderWidth,
    dashboardSiderWidth,
  } = useModel('visualPanelControl');

  const checkVisibility = useCallback(() => {
    const now = Date.now();
    if (now - lastUpdateTime < 100) return;

    const allNodes = getNodes();
    const currentNode = allNodes.find((node) => node.id === nodeId);

    if (!currentNode) {
      setIsVisible(false);
      return;
    }

    let viewportWidth = window.innerWidth;
    let viewportHeight = window.innerHeight;
    let viewportLeft = 0;

    if (isShowMenu) {
      const leftPanelWidth = (leftSiderWidth / 100) * window.innerWidth;
      viewportLeft += leftPanelWidth;
      viewportWidth -= leftPanelWidth;
    }

    if (isShowVisual && !isShowAIDashboard) {
      const rightPanelWidth = (rightSiderWidth / 100) * window.innerWidth;
      viewportWidth -= rightPanelWidth;
    } else if (isShowAIDashboard) {
      const dashboardPanelWidth = (dashboardSiderWidth / 100) * window.innerWidth;
      viewportWidth -= dashboardPanelWidth;
    }

    const toolbarHeight = 50;
    viewportHeight -= toolbarHeight;

    const nodeWidth = 280;
    const leftShift = nodeWidth / viewport.zoom;

    const viewportBounds = {
      left: (-viewport.x + viewportLeft) / viewport.zoom - leftShift,
      top: -viewport.y / viewport.zoom,
      right: (-viewport.x + viewportLeft + viewportWidth) / viewport.zoom,
      bottom: (-viewport.y + viewportHeight) / viewport.zoom,
    };

    const nodeLeft = currentNode.position.x;
    const nodeTop = currentNode.position.y;
    const nodeRight = nodeLeft + (currentNode.width || 280);
    const nodeBottom = nodeTop + (currentNode.height || 200);

    const nodeIsVisible = !(
      nodeRight < viewportBounds.left ||
      nodeLeft > viewportBounds.right ||
      nodeBottom < viewportBounds.top ||
      nodeTop > viewportBounds.bottom
    );

    setIsVisible(nodeIsVisible);
    setLastUpdateTime(now);
  }, [
    nodeId,
    viewport,
    getNodes,
    lastUpdateTime,
    isShowMenu,
    isShowVisual,
    isShowAIDashboard,
    leftSiderWidth,
    rightSiderWidth,
    dashboardSiderWidth,
  ]);

  useEffect(() => {
    const timeoutId = setTimeout(checkVisibility, 50);
    return () => clearTimeout(timeoutId);
  }, [viewport, checkVisibility]);

  useEffect(() => {
    checkVisibility();
  }, [checkVisibility]);

  return isVisible;
};

const NotebookNode = (node: any) => {
  const { data, id } = node;
  // const [analysisId] = getLocationParams(['analysis-id']);
  const {
    state,
    fbId,
    fbVersionId,
    locked,
    plotOnly,
    computationResourceConfigure,
    systemEnv,
    annotated,
    isReviewError,
  } = data;
  // const [isSubtreeCollapsed, setIsSubtreeCollapsed] = useState(false);

  const [figureList, setFigureList] = useState<any[]>([]);
  const [currentFigure, setCurrentFigure] = useState<any>(null);
  const [currentFigureUrl, setCurrentFigureUrl] = useState<string>('');
  const [isFigureLoading, setIsFigureLoading] = useState<boolean>(false);
  const [shouldLoadFigure, setShouldLoadFigure] = useState<boolean>(false);
  const [figureOriginalUrls, setFigureOriginalUrls] = useState<Record<string, string>>({});
  const [isCustomPreviewVisible, setIsCustomPreviewVisible] = useState<boolean>(false);
  const [previewCurrentIndex, setPreviewCurrentIndex] = useState<number>(0);
  const [thumbnailPage, setThumbnailPage] = useState<number>(0);
  const [loadedThumbnails, setLoadedThumbnails] = useState<Record<string, string>>({});
  const THUMBNAILS_PER_PAGE = 10;
  const isNodeVisible = useNodeVisibility(id);

  const [isPlanModalVisible, setIsPlanModalVisible] = useState(false);
  const [isLoadingPlanDetails, setIsLoadingPlanDetails] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<PlanDetails | null>(null);
  const [isContinuingExecution, setIsContinuingExecution] = useState(false);
  const [dynamicGenerationState, setDynamicGenerationState] = useState<string | null>(null);
  const [reporterModalState, setReporterModalState] = useState<
    'mode' | 'manual' | 'automated' | null
  >(null);
  const [codeAgentMessagesDialogConfig, setCodeAgentMessagesDialogConfig] = useState<{
    visible: boolean;
    computationId: string;
  }>({
    visible: false,
    computationId: '',
  });

  const [codeAgentInvokeDialogVisible, setCodeAgentInvokeDialogVisible] = useState<boolean>(false);

  const {
    nodeId,
    setNodeId,
    reportSelectedNodeIds,
    setReportSelectedNodeIds,
    isAiRepoGenSelected,
    setCurrentFigureIndex,
    isFiguresLoaded,
    setIsFiguresLoaded,
    chatbotState,
    setChatbotState,
  } = useModel('visualPanelControl');

  const { dictionary } = useModel('localization');
  const { isGuest } = useModel('user');
  const isGuestUser = isGuest();

  const {
    shiftKey,
    analysisId,
    instance,
    currentSelectedNodes,
    setCurrentSelectedNodes,
    temporaryCenteredNodeId,
    previteStateDict,
    analysisDetail,
    analysisAccessType,
    setFixedNodeId,
    deleteNodeBatch,
    runSubTree,
    copyNode,
    runNode,
    openRenameNode,
    setJobDetailsInspectedNodeId,
    setDataCollectedNodeId,
    setOutputsListInspectedNodeId,
    openEditParamterModal,
    setComputationResourceChangingNodeId,
    setComputationResourceChangingInfo,
    setIsViewOnlyMode,
    setBugFixerHistoryInspectedNodeId,
    setAutoGenieContextInspectedNodeId,
    setAutoGenieInspectedNodeId,
    setAgentHistoryInspectedNodeId,
    compactMode,
  } = useModel('analysis');
  const { showModal: showDetailModal } = useModel('functionBlockDetail');
  const { fbId2Group } = useModel('functionBlock');
  const [isNodeDeleting, setIsNodeDeleting] = useState(false);

  const [visualizerModalVisible, setVisualizerModalVisible] = useState(false);

  const [jobReviewErrorModalVisible, setJobReviewErrorModalVisible] = useState(false);

  const [programmingAgentModalVisible, setProgrammingAgentModalVisible] = useState(false);

  const [fbStructureDialogConfig, setFbStructureDialogConfig] = useState<{
    visible: boolean;
    fbvId: string;
    nodeId?: string;
    nodeName?: string;
  }>({
    visible: false,
    fbvId: '',
    nodeId: undefined,
    nodeName: undefined,
  });

  const previteState = previteStateDict[id];

  const { zoom } = useViewport();
  const maxScale = 4;
  const inverseZoom = Math.min(1 / zoom, maxScale);

  const maxWidth = 280 * 0.85;

  const zoomResistantLabelStyle = useMemo(
    () => ({
      width: `${100 / inverseZoom}%`,
      maxWidth: `${maxWidth}px`,
      fontFamily: NODE_FONT_FAMILY,
      fontSize: '16px',
      fontWeight: 500,
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      transformOrigin: 'left center',
      transform: `scale(${inverseZoom})`,
    }),
    [inverseZoom, maxWidth],
  );
  const cutStringMemoized = useMemo(
    () => (data.label ? cutString(data.label, 25) : ''),
    [data.label],
  );

  const findLastFinishedComputationNodeId = (nodes: any[]) => {
    const filteredNodes = nodes.filter(
      (node) => node.type === 'computation node' && node.data.state === 'finished',
    );
    if (filteredNodes.length > 0) {
      return filteredNodes[filteredNodes.length - 1].id;
    }
    return null;
  };

  const lastFinishedComputationNodeId = findLastFinishedComputationNodeId(
    instance.toObject().nodes,
  );

  const nodeStateIcon = () => {
    switch (state) {
      case NodeState.CANCELLED:
      case NodeState.ORIGINAL: {
        return dictionary.READY_TO_RUN;
      }
      case NodeState.PENDING:
      case NodeState.BEAUTIFYING:
      case NodeState.GENERATING:
      case NodeState.DEBUGGING:
      case NodeState.RUNNING: {
        return (
          <div style={{ color: stateFontColorMap[state] }}>
            <LoadingOutlined style={{ marginRight: '5px', width: '16px', height: '16px' }} />
            <div
              style={{
                display: 'inline-block',
                fontSize: '13px',
                fontWeight: 300,
                fontFamily: NODE_FONT_FAMILY,
                textTransform: 'capitalize',
              }}
            >
              {state}
            </div>
          </div>
        );
      }
      case NodeState.FINISHED: {
        return (
          <div style={{ color: stateFontColorMap[NodeState.FINISHED] }}>
            <CheckCircleOutlined style={{ marginRight: '5px', width: '16px', height: '16px' }} />
            <div
              style={{
                display: 'inline-block',
                fontSize: '13px',
                fontWeight: 300,
                fontFamily: NODE_FONT_FAMILY,
              }}
            >
              {dictionary.RUN_COMPLETED}
              {isReviewError && (
                <WarningFilled
                  style={{ marginLeft: '5px', width: '16px', height: '16px', cursor: 'pointer' }}
                  onClick={() => setJobReviewErrorModalVisible(true)}
                />
              )}
            </div>
          </div>
        );
      }
      case NodeState.FAILED: {
        return (
          <div style={{ color: stateFontColorMap[state] }}>
            <CloseCircleOutlined style={{ marginRight: '5px', width: '16px', height: '16px' }} />
            <div
              style={{
                display: 'inline-block',
                fontSize: '13px',
                fontWeight: 300,
                fontFamily: NODE_FONT_FAMILY,
              }}
            >
              {isReviewError ? dictionary.REVIEWED_ERROR : dictionary.RUNTIME_ERROR}
            </div>
          </div>
        );
      }

      default:
        return;
    }
  };

  const getBgColor = () => {
    switch (state) {
      case NodeState.CANCELLED:
      case NodeState.ORIGINAL:
      case NodeState.PENDING:
      case NodeState.RUNNING:
      case NodeState.DEBUGGING:
      case NodeState.FAILED:
      case NodeState.GENERATING:
      case NodeState.BEAUTIFYING:
        return bgColorMap[state];
      case NodeState.FINISHED:
        return bgColorMap[state];
      default:
        return bgColorMap[NodeState.ORIGINAL];
    }
  };

  const editParams = () => {
    openEditParamterModal(id, fbId);
  };

  const runAllTree = () => {
    runSubTree(id, instance);
  };

  const removeNode = async () => {
    const confirmed = await promiseConfirm({
      title: dictionary.DELETE,
      content: 'Are you sure to delete this node?',
      okText: dictionary.DELETE,
      okType: 'primary',
      cancelText: dictionary.CANCEL,
      centered: true,
    });

    if (!confirmed) {
      message.info('Cancel delete');
      return;
    }

    setIsNodeDeleting(true);
    const hideLoadingMessage = message.loading('Deletion in progress...', 0);
    try {
      const { remove } = data;
      const edges = instance.toObject().edges;
      const flowTool = new FlowTool(instance);
      const node = flowTool.getNode(id);
      if (currentSelectedNodes.some((node) => node.id === id)) {
        setCurrentSelectedNodes(currentSelectedNodes.filter((node) => node.id !== id));
      }
      if (reportSelectedNodeIds.includes(id)) {
        setReportSelectedNodeIds(reportSelectedNodeIds.filter((nodeId) => nodeId !== id));
      }
      await remove(id, node, edges);
      if (id === nodeId) {
        setNodeId(null);
      }
      hideLoadingMessage();
      message.success('Delete node successful');
    } catch (error) {
      hideLoadingMessage();
      message.error('Error while deleting the node.');
    } finally {
      setIsNodeDeleting(false);
    }
  };

  const removeSubTree = async () => {
    const flowTool = new FlowTool(instance);
    const nodeIdArr = flowTool.findNextComputable(id);
    const nodeArr = nodeIdArr.map((id) => flowTool.getNode(id));
    const edges = instance.toObject().edges;
    await deleteNodeBatch(nodeIdArr, nodeArr, edges);
    message.success('delete node successful');
  };

  const cancelComputation = async () => {
    await requestCancelSubtreeComputations(id);
  };

  const handleClick = () => {
    if (shiftKey) {
      if (currentSelectedNodes.some((node) => node.id === id)) {
        setCurrentSelectedNodes(currentSelectedNodes.filter((node) => node.id !== id));
      } else {
        setCurrentSelectedNodes([...currentSelectedNodes, node]);
      }
    } else {
      if (currentSelectedNodes.some((node) => node.id === id)) {
        setCurrentSelectedNodes(currentSelectedNodes.filter((node) => node.id !== id));
      } else {
        setCurrentSelectedNodes([node]);
      }
    }
  };

  const downloadDataSummary = async () => {
    const { data: latestComputation } = await requestLatestComputation(id);
    const { resultDataId } = latestComputation;
    const { data: dataInfo } = await requestDataInfo(resultDataId);
    const { summary } = dataInfo;
    // Save the summary as a file (downloadFile is not available)
    downloadJsonText(summary, 'data_summary');
  };

  const fixNode = (nodeId: string) => {
    setFixedNodeId(nodeId);
  };

  const isFiguresLoadedRef = useRef(isFiguresLoaded);

  const loadFigureList = async () => {
    if (!isNodeVisible) {
      return;
    }

    setIsFigureLoading(true);
    try {
      const { data: figuresResponse } = await requestListFigureByNodeId(id);

      const staticFigureList = figuresResponse || [];

      let figureUrl = '';
      if (staticFigureList.length > 0) {
        figureUrl = staticFigureList[0].thumbnailUrl;
      }

      setFigureList(staticFigureList);
      setCurrentFigure(staticFigureList[0] || null);
      setCurrentFigureUrl(figureUrl);

      if (id === lastFinishedComputationNodeId) {
        setIsFiguresLoaded(true);
      }
    } catch (error) {
      console.error('Error loading figure list:', error);
      setFigureList([]);
      setCurrentFigure(null);
      setCurrentFigureUrl('');
    } finally {
      setIsFigureLoading(false);
    }
  };

  useEffect(() => {
    isFiguresLoadedRef.current = isFiguresLoaded;
  }, [isFiguresLoaded]);

  useEffect(() => {
    if (analysisDetail?.figureVisible && state === NodeState.FINISHED) {
      loadFigureList();
    }
  }, [analysisDetail?.figureVisible, state]);

  const loadCurrentFigureUrl = async () => {
    if (!currentFigure) {
      setCurrentFigureUrl('');
      return;
    }

    try {
      const url = await requestGetFigureInfo(currentFigure.figureUuid, true);
      setCurrentFigureUrl(url);
    } catch (error) {
      console.error('Error loading figure URL:', error);
      setCurrentFigureUrl('');
    }
  };

  const loadThumbnailsForPage = async (page: number) => {
    const startIndex = page * THUMBNAILS_PER_PAGE;
    const endIndex = Math.min(startIndex + THUMBNAILS_PER_PAGE, figureList.length);
    const figuresToLoad = figureList.slice(startIndex, endIndex);

    const urlPromises = figuresToLoad.map(async (figure) => {
      if (!loadedThumbnails[figure.figureUuid]) {
        try {
          const url = await requestGetFigureInfo(figure.figureUuid, true);
          return { figureUuid: figure.figureUuid, url };
        } catch (error) {
          console.error('Error loading thumbnail for figure:', figure.figureUuid, error);
          return { figureUuid: figure.figureUuid, url: figure.thumbnailUrl || '' };
        }
      }
      return null;
    });

    const results = await Promise.all(urlPromises);
    const newThumbnails: Record<string, string> = {};
    results.forEach((result) => {
      if (result) {
        newThumbnails[result.figureUuid] = result.url;
      }
    });
    setLoadedThumbnails((prev) => ({ ...prev, ...newThumbnails }));
  };

  const loadOriginalImageForFigure = async (figureUuid: string) => {
    if (!figureOriginalUrls[figureUuid]) {
      try {
        const url = await requestGetFigureInfo(figureUuid, false);
        setFigureOriginalUrls((prev) => ({ ...prev, [figureUuid]: url }));
      } catch (error) {
        console.error('Error loading original URL for figure:', figureUuid, error);
      }
    }
  };

  useEffect(() => {
    const shouldLoadFigureData =
      analysisDetail?.figureVisible && state === NodeState.FINISHED && isNodeVisible;
    setShouldLoadFigure(shouldLoadFigureData);

    if (shouldLoadFigureData) {
      loadFigureList();
    }
  }, [analysisDetail?.figureVisible, state, id, isNodeVisible]);

  useEffect(() => {
    if (currentFigure && isNodeVisible) {
      loadCurrentFigureUrl();
      // Clear the original image URL; fetch it again when a preview is needed
    }
  }, [currentFigure, isNodeVisible]);

  useEffect(() => {
    const handleOpenVisualizationPanel = async (e: any) => {
      console.log('handleOpenVisualizationPanel', e);
      if (!plotOnly) {
        const eventSelectedNodes = e.detail?.currentSelectedNodes;
        const eventAnalysisId = e.detail?.analysisId;

        const nodesToUse =
          eventSelectedNodes && eventSelectedNodes.length > 0
            ? eventSelectedNodes
            : currentSelectedNodes;

        const analysisIdToUse = eventAnalysisId || analysisId;

        const nodeId = nodesToUse && nodesToUse.length > 0 ? nodesToUse[0].id : id;

        if (!nodeId) {
          console.error('No node selected for visualization panel');
          return;
        }

        const { data: latestComputation } = await requestLatestComputation(nodeId);
        const { resultDataId } = latestComputation;
        window.open(
          `/visual-panel?analysis-id=${analysisIdToUse}&node-id=${nodeId}&data-id=${resultDataId}`,
        );
      }
    };

    window.addEventListener('openVisualizationPanel', handleOpenVisualizationPanel);

    return () => {
      window.removeEventListener('openVisualizationPanel', handleOpenVisualizationPanel);
    };
  }, [plotOnly]);

  const handleFigureChange = (figure: any, index: number) => {
    setCurrentFigure(figure);
    setCurrentFigureIndex(index);
  };

  const openCustomPreview = async () => {
    const currentIndex = figureList.findIndex(
      (fig: any) => fig.figureUuid === currentFigure?.figureUuid,
    );
    setPreviewCurrentIndex(currentIndex >= 0 ? currentIndex : 0);
    const initialPage = Math.floor((currentIndex >= 0 ? currentIndex : 0) / THUMBNAILS_PER_PAGE);
    setThumbnailPage(initialPage);
    setIsCustomPreviewVisible(true);
    await loadThumbnailsForPage(initialPage);
    // Load the full-size image for the current figure
    if (currentFigure?.figureUuid) {
      await loadOriginalImageForFigure(currentFigure.figureUuid);
    }
  };

  const handlePreviewFigureChange = async (index: number) => {
    setPreviewCurrentIndex(index);
    handleFigureChange(figureList[index], index);

    const figure = figureList[index];
    if (figure?.figureUuid) {
      await loadOriginalImageForFigure(figure.figureUuid);
    }

    const newPage = Math.floor(index / THUMBNAILS_PER_PAGE);
    if (newPage !== thumbnailPage) {
      setThumbnailPage(newPage);
      await loadThumbnailsForPage(newPage);
    }
  };

  const handleCheckboxChange = (e, nodeId) => {
    e.stopPropagation();
    if (e.target.checked) {
      setReportSelectedNodeIds([...reportSelectedNodeIds, nodeId]);
    } else {
      setReportSelectedNodeIds(reportSelectedNodeIds.filter((id) => id !== nodeId));
    }
  };

  const handleOpenPlanModal = async (e) => {
    e.stopPropagation();
    setIsPlanModalVisible(true);
    setIsLoadingPlanDetails(true);

    try {
      const generationId = node.generationId || data.dynamicGenerationId;
      if (!generationId) {
        message.error('No plan available for this node.');
        setSelectedPlan(null);
        setIsLoadingPlanDetails(false);
        return;
      }
      const response = await requestDynamicGenerationPlanGet(id, generationId);
      if (response.code === 200 && response.data?.presigned_url) {
        const planResponse = await fetch(response.data.presigned_url);
        if (!planResponse.ok) {
          throw new Error(`Failed to fetch plan data: ${planResponse.statusText}`);
        }

        const planData = await planResponse.json();
        setSelectedPlan({
          generationId,
          nodeId: id,
          steps: planData.steps,
        });

        try {
          const response = await requestGetDynamicGeneration(generationId);
          if (response.code === 200) {
            setDynamicGenerationState(response.data.state);
          }
        } catch (error) {
          console.error('Error fetching dynamic generation state:', error);
        }
      } else {
        message.error('Failed to get plan URL from server.');
        setSelectedPlan(null);
      }
    } catch (error) {
      console.error('Error fetching plan details:', error);
      message.error('Failed to load plan details.');
      setSelectedPlan(null);
    } finally {
      setIsLoadingPlanDetails(false);
    }
  };

  const handleClosePlanModal = () => {
    setIsPlanModalVisible(false);
    setSelectedPlan(null);
  };

  const handleContinueExecution = async () => {
    if (!selectedPlan) return;

    setIsContinuingExecution(true);
    try {
      const response = await requestContinueDynamicGeneration(
        selectedPlan.generationId,
        selectedPlan.nodeId,
      );

      if (response.code === 200) {
        message.success('Dynamic generation continued successfully');
        handleClosePlanModal();
      } else {
        const errorMessage =
          response.data?.error || response.msg || 'Failed to continue dynamic generation';
        message.error(errorMessage);
      }
    } catch (error) {
      console.error('Error continuing dynamic generation:', error);
      message.error('Failed to continue dynamic generation');
    } finally {
      setIsContinuingExecution(false);
    }
  };

  const handleOpenReporterModal = async () => {
    setReporterModalState('manual');
  };

  const handleCloseReporterModal = () => {
    setReporterModalState(null);
  };

  const handleBackToModeSelection = () => {
    setReporterModalState('mode');
  };

  const handleProceedToReport = async (
    selectedNodeIds: string[],
    selectedFigures: Record<string, { figureUuid: string; figureName: string }[]>,
    selectedReporterLLMModel: string,
  ) => {
    message.success('Branch report generation started');
    const { data } = await requestPreviousNodeList(id, true);
    const branchNodes = data.filter(
      (node: any) =>
        (node.type === NodeType.COMPUTATION_NODE ||
          node.type === NodeType.COMPUTATION_NODE_V2 ||
          node.type === NodeType.NOTEBOOK_NODE) &&
        node.state === 'finished',
    );
    const selectedNodes = branchNodes.filter((node: any) => selectedNodeIds.includes(node.id));
    setReportSelectedNodeIds(selectedNodeIds);
    setReporterModalState(null);

    let reportNode: any = null;
    let newNodes: any[] = [];

    try {
      const reportPosition = { x: (node.xPos || 0) + 350, y: (node.yPos || 0) + 100 };

      const { data: newNodeEntity } = await requestCreateNode(
        NodeType.REPORT_NODE,
        reportPosition.x,
        reportPosition.y,
        analysisId || '',
        '', // dataId - not needed for report nodes
        '', // fbId - not needed for report nodes
        'Branch Report Generation',
      );

      reportNode = {
        id: newNodeEntity.id.toString(),
        type: NodeType.REPORT_NODE,
        position: reportPosition,
        data: {
          label: 'Branch Report Generation',
          state: NodeState.RUNNING,
          sourceNodeIds: branchNodes.map((node) => node.id),
          reportStatus: 'initializing',
          branchAnalysis: true,
          ...newNodeEntity,
        },
      };

      newNodes = [...instance.toObject().nodes, reportNode];
      instance.setNodes(newNodes);

      if (analysisId) {
        const { data: edgeEntity } = await requestCreateEdge(id, reportNode.id, analysisId);
        const newEdge = {
          id: edgeEntity.id.toString(),
          animated: true,
          source: id,
          target: reportNode.id,
        };
        const currentEdges = instance.toObject().edges;
        instance.setEdges([...currentEdges, newEdge]);
      }

      const reportGenerationPayload = {
        reportNode: reportNode,
        analysisId: analysisId || '',
        branchNodes: selectedNodes.map((n: any) => ({
          id: n.id,
          name: n.name,
          state: n.state,
          figures: selectedFigures[n.id] || [],
        })),
        model: selectedReporterLLMModel,
      };

      if (reporterModalState === 'manual') {
        await requestGenerateBranchReport(reportGenerationPayload);
      } else if (reporterModalState === 'automated') {
        await requestGenerateBranchReportAutomated(reportGenerationPayload);
      }
    } catch (error) {
      console.error('Error preparing report generation:', error);
      message.error('Failed to start branch report generation');
    }
  };

  const openCodeAgentMessagesDialog = async () => {
    const { data: latestComputation } = await requestLatestComputation(id);
    const { id: computationId } = latestComputation;
    setCodeAgentMessagesDialogConfig({
      visible: true,
      computationId,
    });
  };

  const parseSteps = (stepsString: string | any): { text: string; completed: boolean }[] => {
    let steps: string;
    if (typeof stepsString === 'string') {
      steps = stepsString;
    } else if (Array.isArray(stepsString)) {
      steps = stepsString.join('\n');
    } else if (stepsString && typeof stepsString === 'object') {
      steps = JSON.stringify(stepsString, null, 2);
    } else {
      steps = String(stepsString || '');
    }

    const lines = steps.split('\n').filter((line) => line.trim());
    return lines.map((line) => {
      const match = line.match(/^-\s*\[([\sxX]?)\]\s*(.*)$/);
      if (match) {
        return {
          text: match[2].trim(),
          completed: match[1].toLowerCase() === 'x',
        };
      }
      return { text: line.trim(), completed: false };
    });
  };

  const renderExecutionSteps = () => {
    if (!selectedPlan?.steps) return null;

    const parsedSteps = parseSteps(selectedPlan.steps);
    return parsedSteps.map((step, index) => (
      <div
        key={`step-${index}-${step.text.slice(0, 10)}`}
        className="execution-step"
        style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
      >
        <span>{step.text}</span>
      </div>
    ));
  };

  const jumpToVisualization = async () => {
    const { data: latestComputation } = await requestLatestComputation(id);
    const { resultDataId } = latestComputation;
    window.open(
      `/visual-panel?analysis-id=${analysisId}&node-id=${id}&data-id=${resultDataId}&dataType=general`,
    );
  };

  const menu = (
    <div
      onClick={(e) => {
        e.stopPropagation();
      }}
    >
      <Menu>
        <Popover
          title={<span style={{ color: '#fff' }}>{dictionary.RUN_SUB_TREE}</span>}
          content={
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
              }}
            >
              <CustomImage name={customIconNames.RUNNODESECOND} style={{ margin: '1vh 0' }} />
              <span style={{ color: '#fff' }}>for node data with sub tree</span>
            </div>
          }
          color="#000"
        >
          <Menu.Item
            key="Run tree"
            style={
              analysisAccessType === AnalysisType.PUBLIC
                ? { cursor: 'not-allowed' }
                : { cursor: 'pointer' }
            }
            disabled={analysisAccessType === AnalysisType.PUBLIC || locked}
            onClick={() => {
              runAllTree();
            }}
          >
            {dictionary.RUN_TREE}
          </Menu.Item>
        </Popover>
        {/* <Menu.Item
          key="Job info"
          style={{ cursor: 'pointer' }}
          disabled={![NodeState.FAILED, NodeState.FINISHED].includes(state)}
          onClick={() => {
            setJobInfoInspectedNodeId(id);
          }}
        >
          {dictionary.JOB_INFO}
        </Menu.Item>
        <Menu.Item
          key="Calculate log"
          style={
            analysisAccessType === AnalysisType.PUBLIC || locked
              ? { cursor: 'not-allowed' }
              : { cursor: 'pointer' }
          }
          disabled={analysisAccessType === AnalysisType.PUBLIC || locked}
          onClick={() => {
            setCalcuLogInspectedNodeId(id);
          }}
        >
          {dictionary.CALCULATION_LOG}
        </Menu.Item> */}
        <Menu.Item
          key="Job detail"
          style={{ cursor: 'pointer' }}
          disabled={
            ![NodeState.FAILED, NodeState.FINISHED].includes(state) ||
            (locked && data.state !== NodeState.FINISHED)
          }
          onClick={() => {
            setJobDetailsInspectedNodeId(id);
          }}
        >
          {dictionary.JOB_DETAILS}
        </Menu.Item>
        <Menu.Item
          key="Output files"
          style={
            analysisAccessType === AnalysisType.PUBLIC ||
            (locked && data.state !== NodeState.FINISHED)
              ? { cursor: 'not-allowed' }
              : { cursor: 'pointer' }
          }
          disabled={
            analysisAccessType === AnalysisType.PUBLIC ||
            (locked && data.state !== NodeState.FINISHED)
          }
          onClick={() => {
            setOutputsListInspectedNodeId(id);
          }}
        >
          {dictionary.OUTPUTS}
        </Menu.Item>
        <Menu.Item
          key="Share"
          style={{ cursor: 'pointer' }}
          onClick={() => {
            const [analysisId] = getLocationParams(['analysis-id']);
            const host = window.location.host;
            const protocol = window.location.protocol;
            writeToClipboard(
              `${protocol}//${host}/analysisPanel/flowPanel?analysis-id=${analysisId}&nodeId=${id}&open-viz-panel=${false}`,
            )
              .then(() => {
                message.success('Link copied');
              })
              .catch(() => {
                console.error('Link cannot be copied');
              });
          }}
        >
          {dictionary.SHARE}
        </Menu.Item>
        <Menu.Item
          key="Delete"
          style={
            analysisAccessType === AnalysisType.PUBLIC || locked || isNodeDeleting
              ? { cursor: 'not-allowed' }
              : { color: 'red' }
          }
          disabled={analysisAccessType === AnalysisType.PUBLIC || locked || isNodeDeleting}
          onClick={removeNode}
        >
          {dictionary.DELETE}
        </Menu.Item>
        <Menu.Item
          key="Delete SubTree"
          style={
            analysisAccessType === AnalysisType.PUBLIC || locked
              ? { cursor: 'not-allowed' }
              : { color: 'red' }
          }
          disabled={analysisAccessType === AnalysisType.PUBLIC || locked}
          onClick={() => {
            confirm({
              title: dictionary.DELETE_SUBTREE,
              // icon: <ExclamationCircleFilled />,
              content: 'Are you sure to delete this subTree?',
              okText: dictionary.DELETE,
              okType: 'primary',
              cancelText: dictionary.CANCEL,
              centered: true,
              async onOk() {
                removeSubTree();
              },
              onCancel() {
                console.log('Cancel Delete');
              },
            });
          }}
        >
          {dictionary.DELETE_SUBTREE}
        </Menu.Item>
        <Menu.Item
          key="Cancel the computation"
          style={
            analysisAccessType === AnalysisType.PUBLIC ||
            ![NodeState.PENDING, NodeState.RUNNING, NodeState.DEBUGGING].includes(state)
              ? { cursor: 'not-allowed' }
              : { color: 'red' }
          }
          disabled={
            analysisAccessType === AnalysisType.PUBLIC ||
            ![NodeState.PENDING, NodeState.RUNNING, NodeState.DEBUGGING].includes(state)
          }
          onClick={() => {
            confirm({
              title: 'Cancel the computation',
              // icon: <ExclamationCircleFilled />,
              content: 'Are you sure to cancel the computation?',
              okText: 'Yes',
              okType: 'primary',
              cancelText: 'No',
              centered: true,
              onOk: cancelComputation,
              onCancel() {
                console.log('Delete cancelled');
              },
            });
          }}
        >
          {dictionary.CANCEL_COMPUTATION}
        </Menu.Item>
        <Menu.Item
          key="Config computation resource"
          style={
            analysisAccessType === AnalysisType.PUBLIC ||
            [NodeState.PENDING, NodeState.RUNNING, NodeState.DEBUGGING].includes(state)
              ? { cursor: 'not-allowed' }
              : {}
          }
          disabled={
            analysisAccessType === AnalysisType.PUBLIC ||
            [NodeState.PENDING, NodeState.RUNNING, NodeState.DEBUGGING].includes(state)
          }
          onClick={() => {
            setComputationResourceChangingNodeId(id);
            setComputationResourceChangingInfo({
              ...JSON.parse(computationResourceConfigure),
              systemEnv,
            });
            setIsViewOnlyMode(false);
          }}
        >
          {dictionary.CONFIG_COMPUTATION_RESOURCE}
        </Menu.Item>
        {data.state === NodeState.FINISHED && !plotOnly && (
          <Menu.Item
            key="Download data summary"
            style={{ cursor: 'pointer' }}
            onClick={downloadDataSummary}
          >
            {dictionary.DOWNLOAD_DATA_SUMMARY}
          </Menu.Item>
        )}
        {data.state === NodeState.FINISHED && (
          <Menu.Item
            key="Download pipeline plots"
            style={{ cursor: 'pointer' }}
            onClick={async () => {
              const messageKey = 'download-pipeline-plots';
              try {
                message.loading({
                  content: 'Preparing plots for download...',
                  key: messageKey,
                  duration: 0,
                });

                const { data: previousNodes } = await requestPreviousNodeList(id, true);

                const finishedComputationNodes = previousNodes.filter(
                  (node: any) =>
                    (node.type === NodeType.COMPUTATION_NODE ||
                      node.type === NodeType.COMPUTATION_NODE_V2) &&
                    node.state === NodeState.FINISHED,
                );

                if (finishedComputationNodes.length === 0) {
                  message.warning({
                    content: 'No finished computation nodes found in the pipeline',
                    key: messageKey,
                  });
                  return;
                }

                const JSZip = (await import('jszip')).default;
                const zip = new JSZip();

                let totalDownloadedCount = 0;
                let totalFigureCount = 0;

                const mainFolderName = `Pipeline_Plots_${data.label || 'Node'}`;

                for (let nodeIndex = 0; nodeIndex < finishedComputationNodes.length; nodeIndex++) {
                  const node = finishedComputationNodes[nodeIndex];
                  try {
                    const { data: figuresResponse } = await requestListFigureByNodeId(node.id);
                    const figures = figuresResponse || [];

                    if (figures.length === 0) {
                      continue;
                    }

                    totalFigureCount += figures.length;

                    const nodeFolderPath = `${mainFolderName}`;

                    for (const figure of figures) {
                      try {
                        const imageUrl = figure.url;

                        const response = await fetch(imageUrl);
                        if (!response.ok) {
                          console.warn(
                            `Failed to download figure: ${figure.figureName} from node ${node.id}`,
                          );
                          continue;
                        }

                        const imageBlob = await response.blob();
                        const imageArrayBuffer = await imageBlob.arrayBuffer();

                        const fileName = figure.figureName;
                        const fullPath = `${nodeFolderPath}/${fileName}`;

                        zip.file(fullPath, imageArrayBuffer);
                        totalDownloadedCount++;

                        message.loading({
                          content: `Downloaded ${totalDownloadedCount}/${totalFigureCount} plots from ${
                            nodeIndex + 1
                          }/${finishedComputationNodes.length} nodes...`,
                          key: messageKey,
                          duration: 0,
                        });
                      } catch (error) {
                        console.error(
                          `Error downloading figure ${figure.figureName} from node ${node.id}:`,
                          error,
                        );
                      }
                    }
                  } catch (error) {
                    console.error(`Error processing node ${node.id}:`, error);
                  }
                }

                if (totalDownloadedCount === 0) {
                  message.warning({
                    content: 'No plots were found in any of the pipeline nodes',
                    key: messageKey,
                  });
                  return;
                }

                message.loading({ content: 'Creating zip file...', key: messageKey, duration: 0 });

                const zipBlob = await zip.generateAsync({ type: 'blob' });

                const downloadUrl = window.URL.createObjectURL(zipBlob);
                const downloadLink = document.createElement('a');
                downloadLink.href = downloadUrl;
                downloadLink.download = `${mainFolderName}.zip`;

                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);

                window.URL.revokeObjectURL(downloadUrl);

                message.success({
                  content: `Downloaded ${totalDownloadedCount} plots from ${finishedComputationNodes.length} pipeline nodes successfully!`,
                  key: messageKey,
                });
              } catch (error) {
                console.error('Error downloading pipeline plots:', error);
                message.error({
                  content: 'Failed to download pipeline plots. Please try again.',
                  key: messageKey,
                });
              }
            }}
          >
            Download Pipeline Plots
          </Menu.Item>
        )}
        <Menu.Item
          key="Bug fixer history"
          style={{ cursor: 'pointer' }}
          onClick={() => {
            setBugFixerHistoryInspectedNodeId(id);
          }}
        >
          {dictionary.BUG_FIXER_HISTORY}
        </Menu.Item>
        <Menu.Item
          key="Code Agent Messages"
          style={{ cursor: 'pointer' }}
          icon={<CodeOutlined />}
          onClick={openCodeAgentMessagesDialog}
        >
          Code Agent Messages
        </Menu.Item>
        {data.type === NodeType.NOTEBOOK_NODE && (
          <Menu.Item
            key="Open in Notebook"
            style={{ cursor: 'pointer' }}
            onClick={() => {
              setProgrammingAgentModalVisible(true);
            }}
          >
            Open in Notebook
          </Menu.Item>
        )}
        <Menu.Item
          key="Auto Genie Context"
          style={{ cursor: 'pointer' }}
          onClick={() => {
            setAutoGenieContextInspectedNodeId(id);
          }}
        >
          {dictionary.AUTO_GENIE_CONTEXT}
        </Menu.Item>
        <Menu.Item
          key="Fix"
          style={{ cursor: 'pointer' }}
          onClick={() => {
            fixNode(id);
          }}
        >
          {dictionary.FIX}
        </Menu.Item>
      </Menu>
    </div>
  );

  const aiActionsMenu = (
    <div>
      <Menu>
        <Menu.ItemGroup title="Node">
          <Menu.Item
            key="1"
            icon={<ThunderboltOutlined />}
            disabled={
              (data.state !== NodeState.FINISHED && data.dataId === null) ||
              analysisAccessType === AnalysisType.PUBLIC ||
              isGuestUser ||
              plotOnly ||
              (locked && data.state !== NodeState.FINISHED)
            }
            onClick={() => {
              message.info('Data interpretation is not available yet.');
            }}
          >
            {dictionary.DATA_INTERPRETATION}
          </Menu.Item>
          <Menu.Item
            key="2"
            icon={<SubnodeOutlined />}
            style={{ marginBottom: '5px' }}
            disabled={
              (data.state !== NodeState.FINISHED && data.dataId === null) ||
              analysisAccessType === AnalysisType.PUBLIC ||
              isGuestUser ||
              plotOnly ||
              (locked && data.state !== NodeState.FINISHED)
            }
            onClick={() => {
              setAutoGenieInspectedNodeId(id);
            }}
          >
            {dictionary.AUTO_GENIE}
          </Menu.Item>
          <Menu.Item
            key="3"
            icon={<SisternodeOutlined />}
            style={{ marginBottom: '5px' }}
            disabled={
              (data.state !== NodeState.FINISHED && data.dataId === null) ||
              analysisAccessType === AnalysisType.PUBLIC ||
              isGuestUser ||
              (locked && data.state !== NodeState.FINISHED)
            }
            onClick={() => {
              setVisualizerModalVisible(true);
            }}
          >
            {dictionary.BEAUTIFY}
          </Menu.Item>
          <Menu.Item
            key="4"
            icon={<ToolOutlined />}
            style={{ marginBottom: '5px' }}
            disabled={data.state !== NodeState.FAILED}
            onClick={() => {
              setCodeAgentInvokeDialogVisible(true);
            }}
          >
            {dictionary.BUG_FIXER}
          </Menu.Item>
          <Menu.Item
            key="5"
            icon={<HistoryOutlined />}
            style={{ marginBottom: '5px' }}
            onClick={() => {
              setAgentHistoryInspectedNodeId(id);
            }}
          >
            {dictionary.AGENT_HISTORY}
          </Menu.Item>
          <Menu.Item
            key="6"
            icon={<FileTextOutlined />}
            style={{ marginBottom: '5px' }}
            disabled={
              (data.state !== NodeState.FINISHED && data.dataId === null) ||
              analysisAccessType === AnalysisType.PUBLIC ||
              isGuestUser ||
              (locked && data.state !== NodeState.FINISHED)
            }
            onClick={handleOpenReporterModal}
          >
            {dictionary.REPORTER}
          </Menu.Item>
          <Menu.Item
            key="7"
            icon={
              <CustomImage
                name={customIconNames.AIICONSTAR}
                style={{
                  height: '15px',
                  marginBottom: '2px',
                }}
              />
            }
            style={{ marginBottom: '5px' }}
            onClick={() => {
              if (!chatbotState.isVisible) {
                setChatbotState((prev) => ({
                  ...prev,
                  isVisible: true,
                  mode: 'expanded',
                }));
              }
              setCurrentSelectedNodes([node]);
            }}
          >
            <span className="gradient-text">{dictionary.CHAT}</span>
          </Menu.Item>
        </Menu.ItemGroup>
      </Menu>
    </div>
  );

  const showPlot = shouldLoadFigure && figureList.length > 0;

  return (
    <>
      {compactMode && currentSelectedNodes.some((node) => node.id === id) ? (
        <div
          style={{
            position: 'absolute',
            top: annotated ? -70 : -45,
            left: 0,
            width: '100%',
            zIndex: 1,
          }}
        >
          <div
            style={{
              height: '38px',
              backgroundColor: '#FFF',
              display: 'flex',
              borderTop: '1px solid #E2E4EC',
              justifyContent: 'space-between',
              alignItems: 'center',
              boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)',
              padding: '0 15px',
              borderRadius: '2px',
            }}
          >
            <Space
              style={{
                width: '100%',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              {
                <div style={{ flex: 1, textAlign: 'center' }}>
                  <Popover
                    content={<span style={{ color: '#fff' }}>{dictionary.VIEW_CODE}</span>}
                    color="#000"
                  >
                    <CodeOutlined
                      style={{ cursor: 'pointer' }}
                      onClick={async () => {
                        setFbStructureDialogConfig({
                          visible: true,
                          fbvId: fbVersionId,
                          nodeId: id,
                          nodeName: data.label,
                        });
                      }}
                    />
                  </Popover>
                </div>
              }
              <div style={{ flex: 1, textAlign: 'center' }}>
                <Popover
                  content={<span style={{ color: '#fff' }}>{dictionary.MODIFY_PARAMETER}</span>}
                  color="#000"
                >
                  <ControlOutlined
                    style={{ cursor: 'pointer' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      editParams();
                    }}
                  />
                </Popover>
              </div>
              {!locked && (
                <div style={{ flex: 1, textAlign: 'center' }}>
                  <Popover
                    title={<span style={{ color: '#fff' }}>{dictionary.RUN_NODE}</span>}
                    content={
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'center',
                        }}
                      >
                        <CustomImage name={customIconNames.RUNNODEFIRST} />
                        <span style={{ color: '#fff' }}>
                          {dictionary.FOR_NODE_CONNECTED_WITH_DATA}
                        </span>
                      </div>
                    }
                    color="#000"
                  >
                    <PlaySquareOutlined
                      style={
                        analysisAccessType === AnalysisType.PUBLIC
                          ? { cursor: 'not-allowed' }
                          : { cursor: 'pointer' }
                      }
                      onClick={(e) => {
                        e.stopPropagation();
                        if (analysisAccessType !== AnalysisType.PUBLIC) {
                          runNode(id, instance);
                        }
                      }}
                    />
                  </Popover>
                </div>
              )}
              {!locked && (
                <div style={{ flex: 1, textAlign: 'center' }}>
                  <DeleteOutlined
                    style={
                      analysisAccessType === AnalysisType.PUBLIC
                        ? { cursor: 'not-allowed' }
                        : { cursor: 'pointer' }
                    }
                    onClick={(e) => {
                      e.stopPropagation();
                      if (analysisAccessType !== AnalysisType.PUBLIC) {
                        removeNode();
                      }
                    }}
                  />
                </div>
              )}
              {!locked && (
                <div style={{ flex: 1, textAlign: 'center' }}>
                  <Popover
                    content={<span style={{ color: 'black' }}>{dictionary.DOWNLOAD_DATA}</span>}
                  >
                    <DownloadOutlined
                      style={{
                        cursor: 'pointer',
                      }}
                      onClick={async (e) => {
                        e.stopPropagation();
                        try {
                          const { data: latestComputation } = await requestLatestComputation(
                            node.id,
                          );
                          const { data: downloadUrl } = await requestDownloadDataSource(
                            latestComputation.resultDataId,
                          );
                          await downloadFile(downloadUrl, '');
                        } catch {
                          message.error('download failed');
                        }
                      }}
                    />
                  </Popover>
                </div>
              )}
              {locked && (
                <div style={{ flex: 1, textAlign: 'center', color: '#000' }}>
                  <LockOutlined />
                </div>
              )}
              <Divider
                type="vertical"
                style={{
                  backgroundColor: 'rgba(191, 191, 191, 1)',
                  height: '15px',
                  margin: '0 2px 0 4px',
                }}
              />
              <div style={{ flex: 1, textAlign: 'center' }}>
                <Dropdown overlay={aiActionsMenu} trigger={['hover']}>
                  <div style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <CustomImage
                      name={customIconNames.AIICONSTAR}
                      style={{
                        height: '15px',
                        marginRight: '7px',
                        marginBottom: '4px',
                      }}
                    />
                    <span className={styles.askAITitle}>{dictionary.ASK_AI}</span>
                  </div>
                </Dropdown>
              </div>
              <Divider
                type="vertical"
                style={{
                  backgroundColor: 'rgba(191, 191, 191, 1)',
                  height: '15px',
                  margin: '0 2px 0 4px',
                }}
              />
              <div style={{ flex: 1, textAlign: 'center' }}>
                <Dropdown overlay={menu}>
                  <EllipsisOutlined
                    rotate={90}
                    style={{ cursor: 'pointer' }}
                    onClick={(e) => {
                      e.stopPropagation();
                    }}
                  />
                </Dropdown>
              </div>
            </Space>
          </div>
          <div
            style={{
              flex: 1,
              paddingTop: '5px',
              backgroundColor: 'transparent',
            }}
          />
          {annotated ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <CustomImage
                style={{ height: '16px', marginRight: '4px', cursor: 'default' }}
                name={customIconNames.ANNOTATED_ICON}
              />
              <span style={{ font: 'Roboto', color: 'rgba(47, 84, 235, 1)', cursor: 'default' }}>
                {dictionary.ANNOTATED}
              </span>
            </div>
          ) : null}
        </div>
      ) : null}

      <div
        style={{
          width: '280px',
          border:
            currentSelectedNodes.some((node) => node.id === id) || temporaryCenteredNodeId === id
              ? '1px solid rgba(89, 126, 247, 1)'
              : '1px solid rgba(217, 217, 217, 1)',
          boxShadow:
            currentSelectedNodes.some((node) => node.id === id) || temporaryCenteredNodeId === id
              ? '0 0 0 2px #b8c4fc'
              : 'none',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: '7px',
          overflow: 'hidden',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          transform:
            currentSelectedNodes.some((node) => node.id === id) || temporaryCenteredNodeId === id
              ? 'translateY(-1px) scale(1.02)'
              : 'translateY(0) scale(1)',
          opacity: temporaryCenteredNodeId === id ? 0.9 : 1,
        }}
        onClick={handleClick}
        title={data.label}
      >
        <div
          style={{
            width: '279px',
            height: compactMode ? '6px' : '32px',
            backgroundColor: getBgColor(),
            borderBottom: '1px solid #eaeaea',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingLeft: '13px',
            paddingRight: '15px',
          }}
        >
          {!compactMode ? <div>{nodeStateIcon()}</div> : null}

          {!compactMode ? (
            <div>
              {data.state === NodeState.FINISHED && !plotOnly ? (
                <div>
                  <CustomImage
                    name={customIconNames.AIICONSTARWHITE}
                    style={{
                      height: '15px',
                      marginRight: '7px',
                      marginBottom: '4px',
                      cursor: 'pointer',
                    }}
                    dropdownMenu={aiActionsMenu}
                  />
                  <Popover
                    content={<span style={{ color: '#fff' }}>{dictionary.COLLECT_DATA}</span>}
                    color="#000"
                  >
                    <StarOutlined
                      style={
                        analysisAccessType !== AnalysisType.PUBLIC
                          ? {
                              cursor: 'pointer',
                              fontSize: '16px',
                              width: '16px',
                              height: '16px',
                              color: '#fff',
                              paddingTop: '2px',
                            }
                          : {
                              cursor: 'not-allowed',
                              fontSize: '16px',
                              width: '16px',
                              height: '16px',
                              color: '#fff',
                              marginTop: '5px',
                            }
                      }
                      onClick={(e) => {
                        e.stopPropagation();
                        if (analysisAccessType !== AnalysisType.PUBLIC) {
                          setDataCollectedNodeId(id);
                        }
                      }}
                    />
                  </Popover>
                  <Popover
                    content={<span style={{ color: '#fff' }}>{dictionary.DOWNLOAD_DATA}</span>}
                    color="#000"
                  >
                    <DownloadOutlined
                      style={{
                        cursor: 'pointer',
                        fontSize: '17px',
                        color: '#fff',
                        marginLeft: '6px',
                      }}
                      onClick={async (e) => {
                        e.stopPropagation();
                        try {
                          const { data: latestComputation } = await requestLatestComputation(
                            node.id,
                          );
                          const { data: downloadUrl } = await requestDownloadDataSource(
                            latestComputation.resultDataId,
                          );
                          await downloadFile(downloadUrl, '');
                        } catch {
                          message.error('download failed');
                        }
                      }}
                    />
                  </Popover>
                  {previteState && (
                    <Popover
                      content={
                        <span style={{ color: '#fff' }}>
                          {dictionary.VSPATIAL_PREHANDLE_STATE}: {previteState}
                        </span>
                      }
                      color="#000"
                    >
                      <span
                        style={{
                          cursor: 'pointer',
                          fontSize: '18px',
                          color: '#fff',
                          marginLeft: '6.5px',
                        }}
                      >
                        S
                      </span>
                    </Popover>
                  )}
                  {isAiRepoGenSelected && (
                    <Popover
                      content={<span style={{ color: '#fff' }}>{dictionary.SELECT}</span>}
                      color="#000"
                    >
                      <Checkbox
                        className="custom-checkbox"
                        style={{
                          cursor: 'pointer',
                          color: '#fff',
                          marginLeft: '8.5px',
                          paddingBottom: '3px',
                        }}
                        onChange={(e) => handleCheckboxChange(e, id)}
                        checked={reportSelectedNodeIds.includes(id)}
                      />
                    </Popover>
                  )}
                </div>
              ) : data.state === NodeState.ORIGINAL || data.state === NodeState.CANCELLED ? (
                <div>
                  <CustomImage
                    name={customIconNames.AIICONSTAR}
                    style={{ height: '16px', cursor: 'pointer' }}
                    dropdownMenu={aiActionsMenu}
                  />
                </div>
              ) : (
                <div>
                  <CustomImage
                    name={customIconNames.AIICONSTARWHITE}
                    style={{ height: '16px', cursor: 'pointer' }}
                    dropdownMenu={aiActionsMenu}
                  />
                </div>
              )}
            </div>
          ) : null}
        </div>

        <div
          style={{
            width: '100%',
            height: compactMode ? '38px' : '69px',
            backgroundColor: '#FFF',
            display: 'flex',
            flexDirection: 'column',
            paddingLeft: '15px',
            paddingRight: '17px',
          }}
        >
          <div
            style={{
              width: '100%',
              height: '40px',
              backgroundColor: '#FFF',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '10px',
            }}
          >
            {' '}
            {!compactMode ? (
              <div
                style={{
                  width: '85%',
                  color: '#000000',
                  fontFamily: NODE_FONT_FAMILY,
                  fontSize: '16px',
                  fontWeight: 550,
                  textAlign: 'left',
                  whiteSpace: 'nowrap',
                }}
              >
                {data.label ? cutStringByCharType(data.label, 14, 21) : ''}
              </div>
            ) : (
              <div style={zoomResistantLabelStyle}>{cutStringMemoized}</div>
            )}
            {!compactMode ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                {data.dynamicGenerationId && (
                  <Popover content={<span style={{ color: '#fff' }}>View Plan</span>} color="#000">
                    <ProjectOutlined
                      style={{
                        cursor: 'pointer',
                        width: '16px',
                        height: '16px',
                        fontSize: '15px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                      onClick={handleOpenPlanModal}
                    />
                  </Popover>
                )}
                <Popover
                  content={<span style={{ color: '#fff' }}>{dictionary.RENAME}</span>}
                  color="#000"
                >
                  <EditOutlined
                    style={{
                      cursor:
                        analysisAccessType === AnalysisType.PUBLIC ? 'not-allowed' : 'pointer',
                      width: '16px',
                      height: '16px',
                      fontSize: '15px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (analysisAccessType !== AnalysisType.PUBLIC) {
                        openRenameNode(id);
                      }
                    }}
                  />
                </Popover>
              </div>
            ) : null}
          </div>
          {!compactMode ? (
            <div
              style={{
                width: '99.5%',
                height: '35px',
                backgroundColor: '#FFF',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: '10px',
              }}
            >
              {' '}
              <div
                style={{
                  width: '60%',
                  font: 'Roboto',
                  fontSize: '12px',
                  fontWeight: 400,
                  lineHeight: '22px',
                  whiteSpace: 'nowrap',
                  textAlign: 'left',
                  textOverflow: 'ellipsis',
                  backgroundColor: '#FFF',
                }}
              >
                <Tag>{fbId2Group[fbId]?.public ? dictionary.PUBLIC : dictionary.PRIVATE}</Tag>
                {plotOnly ? (
                  <Tag color="purple" style={{ marginLeft: '5px' }}>
                    {dictionary.PLOT_ONLY}
                  </Tag>
                ) : null}
                {annotated ? (
                  <Tag color="cyan" style={{ marginLeft: '5px' }}>
                    {dictionary.ANNOTATED}
                  </Tag>
                ) : null}
                {fbId === PresetFBs.VISUAL.ID && state === NodeState.FINISHED ? null : null}
              </div>
            </div>
          ) : null}
        </div>
        <div
          style={{
            flex: 1,
            paddingTop: '10px',
            backgroundColor: '#FFF',
          }}
        />

        {!compactMode ? (
          <div>
            {
              <div
                style={{
                  width: '100%',
                  height: '32px',
                  backgroundColor: '#FFF',
                  display: 'flex',
                  borderTop: '1px solid #E2E4EC',
                  justifyContent: 'space-between',
                  paddingLeft: '15px',
                  paddingRight: '15px',
                  alignItems: 'center',
                }}
              >
                <div
                  style={{
                    width: '60%',
                    font: 'Roboto',
                    fontSize: '12px',
                    fontStyle: 'italic',
                    fontWeight: 400,
                    lineHeight: '22px',
                    whiteSpace: 'nowrap',
                    textAlign: 'left',
                    textOverflow: 'ellipsis',
                    backgroundColor: '#FFF',
                    overflow: 'hidden',
                  }}
                >
                  {data.fbName ? cutString(data.fbName, 8) : 'null'}
                  <Popover
                    content={<span style={{ color: '#fff' }}>Function Block description</span>}
                    color="#000"
                  >
                    <InfoCircleOutlined
                      style={{ cursor: 'pointer', marginLeft: '3px' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        showDetailModal(fbId);
                      }}
                    />
                  </Popover>
                </div>
                <Space>
                  {fbId === PresetFBs.VISUAL.ID && state === NodeState.FINISHED ? (
                    <Popover
                      content={<span style={{ color: '#fff' }}>Open Visualization Panel</span>}
                      color="#000"
                    >
                      <Button
                        size="small"
                        type="primary"
                        style={{
                          padding: '0 4px',
                          height: '22px',
                          fontSize: '12px',
                          lineHeight: '20px',
                          backgroundColor: 'transparent',
                          color: '#52c41a',
                          borderColor: '#52c41a',
                        }}
                        onClick={jumpToVisualization}
                      >
                        Visual
                      </Button>
                    </Popover>
                  ) : null}
                  {
                    <Popover
                      content={<span style={{ color: '#fff' }}>{dictionary.VIEW_CODE}</span>}
                      color="#000"
                    >
                      <CodeOutlined
                        style={{ cursor: 'pointer' }}
                        onClick={async () => {
                          setFbStructureDialogConfig({
                            visible: true,
                            fbvId: fbVersionId,
                            nodeId: id,
                            nodeName: data.label,
                          });
                        }}
                      />
                    </Popover>
                  }
                  <Popover
                    content={<span style={{ color: '#fff' }}>{dictionary.MODIFY_PARAMETER}</span>}
                    color="#000"
                  >
                    <ControlOutlined
                      style={{ cursor: 'pointer' }}
                      onKeyDown={(e) => {
                        e.stopPropagation();
                      }}
                      onKeyUp={(e: any) => {
                        e.stopPropagation();
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        editParams();
                      }}
                    />
                  </Popover>
                  {!locked && (
                    <Popover
                      title={<span style={{ color: '#fff' }}>{dictionary.RUN_NODE}</span>}
                      content={
                        <div
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'center',
                          }}
                        >
                          <CustomImage name={customIconNames.RUNNODEFIRST} />
                          <span style={{ color: '#fff' }}>
                            {dictionary.FOR_NODE_CONNECTED_WITH_DATA}
                          </span>
                        </div>
                      }
                      color="#000"
                    >
                      <PlaySquareOutlined
                        style={
                          analysisAccessType === AnalysisType.PUBLIC
                            ? { cursor: 'not-allowed' }
                            : { cursor: 'pointer' }
                        }
                        onClick={(e) => {
                          e.stopPropagation();
                          if (analysisAccessType !== AnalysisType.PUBLIC) {
                            runNode(id, instance);
                          }
                        }}
                      />
                    </Popover>
                  )}
                  {!locked && (
                    <CopyOutlined
                      style={
                        analysisAccessType === AnalysisType.PUBLIC
                          ? { cursor: 'not-allowed' }
                          : { cursor: 'pointer' }
                      }
                      onClick={(e) => {
                        e.stopPropagation();
                        if (analysisAccessType !== AnalysisType.PUBLIC) {
                          copyNode(id);
                        }
                      }}
                    />
                  )}
                  {locked && (
                    <div style={{ color: '#000' }}>
                      <LockOutlined />
                    </div>
                  )}
                  <Dropdown overlay={menu}>
                    <EllipsisOutlined
                      rotate={90}
                      style={{ cursor: 'pointer' }}
                      onClick={(e) => {
                        e.stopPropagation();
                      }}
                    />
                  </Dropdown>
                </Space>
              </div>
            }
          </div>
        ) : null}
      </div>
      {showPlot ? (
        <div>
          <div
            style={{
              flex: 1,
              paddingTop: '5px',
              backgroundColor: 'transparent',
            }}
          />
          <div
            style={{
              background: 'white',
              borderRadius: '7px',
              border: '1px solid rgba(217, 217, 217, 1)',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-start',
                flexWrap: 'wrap',
              }}
              onClick={(e) => {
                e.stopPropagation();
              }}
            />
            <div
              style={{
                height: '237px',
                overflow: 'auto',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                position: 'relative',
              }}
            >
              {isFigureLoading ? (
                <LoadingOutlined style={{ fontSize: 24 }} />
              ) : (
                <>
                  <Image
                    style={{
                      width: '250px',
                      cursor: 'pointer',
                    }}
                    src={currentFigureUrl}
                    placeholder={<LoadingOutlined style={{ fontSize: 24 }} />}
                    preview={false}
                    onClick={openCustomPreview}
                  />
                </>
              )}
            </div>
          </div>
        </div>
      ) : (
        ![NodeState.FINISHED, NodeState.FAILED, NodeState.DEBUGGING].includes(node.data.state) && (
          <div
            style={{
              display: 'flex',
              paddingLeft: '5px',
              paddingTop: '1px',
              color: 'rgba(0, 0, 0, 0.45)',
            }}
          >
            <ClockCircleOutlined style={{ marginRight: '4px' }} />
            <span
              style={{
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => {
                (e.target as HTMLElement).style.borderBottom = '1px solid rgba(0, 0, 0, 0.45)';
              }}
              onMouseLeave={(e) => {
                (e.target as HTMLElement).style.borderBottom = 'none';
              }}
              onClick={() => {
                setComputationResourceChangingNodeId(id);
                setComputationResourceChangingInfo({
                  ...JSON.parse(computationResourceConfigure),
                  systemEnv,
                });
                setIsViewOnlyMode(true);
              }}
            >
              {node.data.avgDuration ? (
                <span> Average runtime: {node.data.avgDuration.toFixed(2)} seconds </span>
              ) : (
                <span> Runtime not available </span>
              )}
            </span>
          </div>
        )
      )}
      {!compactMode ? (
        <Handle
          style={{
            top: 75,
            left: -7,
            width: 15,
            height: 60,
            backgroundColor: '#979797',
            border: '1px solid #979797',
            borderRadius: 5,
          }}
          type="target"
          position={Position.Left}
        />
      ) : (
        <Handle
          style={{
            top: 30,
            left: -2,
            width: 1,
            height: 20,
            backgroundColor: '#979797',
            border: '1px solid #979797',
            borderRadius: 5,
          }}
          type="target"
          position={Position.Left}
        />
      )}
      {!compactMode ? (
        <div>
          {!plotOnly && (
            <Handle
              style={{
                top: 75,
                right: -7,
                width: 15,
                height: 60,
                backgroundColor: '#979797',
                border: '1px solid #979797',
                borderRadius: 5,
              }}
              type="source"
              position={Position.Right}
            />
          )}
        </div>
      ) : (
        <div>
          {!plotOnly && (
            <Handle
              style={{
                top: 30,
                right: -2,
                width: 1,
                height: 20,
                backgroundColor: '#979797',
                border: '1px solid #979797',
                borderRadius: 5,
              }}
              type="source"
              position={Position.Right}
            />
          )}
        </div>
      )}
      <Modal
        title="Plan Details"
        visible={isPlanModalVisible}
        onCancel={handleClosePlanModal}
        footer={[
          <Button key="close" onClick={handleClosePlanModal}>
            Close
          </Button>,
          selectedPlan &&
            node.data.state === 'finished' &&
            dynamicGenerationState === 'stopped' && (
              <Button
                key="continue"
                type="primary"
                onClick={handleContinueExecution}
                loading={isContinuingExecution}
                icon={<PlaySquareOutlined />}
              >
                Continue Execution
              </Button>
            ),
        ].filter(Boolean)}
        width={900}
        bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
      >
        {isLoadingPlanDetails ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>Loading plan details...</div>
          </div>
        ) : selectedPlan ? (
          <div>
            <Collapse defaultActiveKey={['1']}>
              <Panel
                header={
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <span>Execution Steps</span>
                  </div>
                }
                key="1"
              >
                {renderExecutionSteps()}
              </Panel>
            </Collapse>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '20px 0', color: '#999' }}>
            {selectedPlan ? 'No steps found in plan' : 'Failed to load plan details'}
          </div>
        )}
      </Modal>

      <ReporterFunctionBlockSelectionModal
        visible={reporterModalState === 'manual'}
        nodeId={id}
        onCancel={handleCloseReporterModal}
        onProceed={handleProceedToReport}
      />

      <ReporterAutomatedSelectionModal
        visible={reporterModalState === 'automated'}
        nodeId={id}
        analysisId={analysisId}
        onCancel={handleCloseReporterModal}
        onBack={handleBackToModeSelection}
        onProceed={handleProceedToReport}
      />

      {/* Code Agent Message Dialog */}
      <CodeAgentMessageDialog
        visible={codeAgentMessagesDialogConfig.visible}
        computationId={codeAgentMessagesDialogConfig.computationId}
        onClose={() => setCodeAgentMessagesDialogConfig({ visible: false, computationId: '' })}
      />

      <CodeAgentInvokeDialog
        visible={codeAgentInvokeDialogVisible}
        nodeId={id}
        onClose={() => setCodeAgentInvokeDialogVisible(false)}
      />

      <FBStructureDialog
        visible={fbStructureDialogConfig.visible}
        onClose={() =>
          setFbStructureDialogConfig({
            visible: false,
            fbvId: '',
            nodeId: undefined,
            nodeName: undefined,
          })
        }
        functionBlockVersionId={fbStructureDialogConfig.fbvId}
        nodeId={fbStructureDialogConfig.nodeId}
        nodeName={fbStructureDialogConfig.nodeName}
      />

      <VisualizerAgentModal
        nodeId={id}
        visible={visualizerModalVisible}
        onClose={() => setVisualizerModalVisible(false)}
      />

      <JobReviewErrorModal
        visible={jobReviewErrorModalVisible}
        nodeId={id}
        onClose={() => setJobReviewErrorModalVisible(false)}
      />

      <ProgrammingAgentModal
        nodeId={id}
        visible={programmingAgentModalVisible}
        onClose={() => setProgrammingAgentModalVisible(false)}
      />

      {/* Custom Preview Modal */}
      <Modal
        visible={isCustomPreviewVisible}
        onCancel={() => setIsCustomPreviewVisible(false)}
        width="90vw"
        style={{ maxWidth: '1200px' }}
        bodyStyle={{ padding: 0 }}
        footer={null}
        centered
      >
        <div style={{ display: 'flex', flexDirection: 'column', height: '80vh' }}>
          {/* Thumbnail Gallery */}
          <div
            style={{
              padding: '16px',
              borderBottom: '1px solid #f0f0f0',
              background: '#fafafa',
            }}
          >
            <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>
              Figure {previewCurrentIndex + 1} of {figureList.length}
            </div>
            <div>
              <div
                style={{
                  display: 'flex',
                  gap: '8px',
                  paddingBottom: '8px',
                  alignItems: 'center',
                }}
              >
                {/* Previous Page Button */}
                {thumbnailPage > 0 && (
                  <Button
                    icon={<LeftOutlined />}
                    size="small"
                    onClick={async () => {
                      const newPage = thumbnailPage - 1;
                      setThumbnailPage(newPage);
                      await loadThumbnailsForPage(newPage);
                    }}
                  />
                )}

                {/* Thumbnails */}
                <div
                  style={{
                    display: 'flex',
                    gap: '8px',
                    flex: 1,
                    overflowX: 'hidden',
                  }}
                >
                  {figureList
                    .slice(
                      thumbnailPage * THUMBNAILS_PER_PAGE,
                      Math.min((thumbnailPage + 1) * THUMBNAILS_PER_PAGE, figureList.length),
                    )
                    .map((figure: any, offsetIndex: number) => {
                      const actualIndex = thumbnailPage * THUMBNAILS_PER_PAGE + offsetIndex;
                      return (
                        <div
                          key={figure.figureUuid}
                          onClick={() => handlePreviewFigureChange(actualIndex)}
                          style={{
                            width: '80px',
                            height: '80px',
                            border:
                              actualIndex === previewCurrentIndex
                                ? '3px solid #1890ff'
                                : '1px solid #d9d9d9',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            overflow: 'hidden',
                            flexShrink: 0,
                            background: '#fff',
                          }}
                        >
                          <img
                            src={loadedThumbnails[figure.figureUuid] || figure.thumbnailUrl || ''}
                            alt={figure.figureName}
                            style={{
                              width: '100%',
                              height: '100%',
                              objectFit: 'cover',
                            }}
                          />
                        </div>
                      );
                    })}
                </div>

                {/* Next Page Button */}
                {(thumbnailPage + 1) * THUMBNAILS_PER_PAGE < figureList.length && (
                  <Button
                    icon={<RightOutlined />}
                    size="small"
                    onClick={async () => {
                      const newPage = thumbnailPage + 1;
                      setThumbnailPage(newPage);
                      await loadThumbnailsForPage(newPage);
                    }}
                  />
                )}
              </div>

              {/* Page Info */}
              <div style={{ textAlign: 'center', fontSize: '12px', color: '#888' }}>
                Page {thumbnailPage + 1} of {Math.ceil(figureList.length / THUMBNAILS_PER_PAGE)}
              </div>
            </div>
            <div style={{ marginTop: '8px', fontSize: '14px', color: '#666' }}>
              {figureList[previewCurrentIndex]?.figureName || 'Figure'}
            </div>
          </div>

          {/* Main Image Display */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              padding: '20px',
              background: '#f5f5f5',
              position: 'relative',
              overflow: 'hidden',
              minHeight: 0,
            }}
          >
            {/* Previous Button */}
            {previewCurrentIndex > 0 && (
              <Button
                icon={<LeftOutlined />}
                style={{
                  position: 'absolute',
                  left: '20px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  zIndex: 1,
                }}
                onClick={() => handlePreviewFigureChange(previewCurrentIndex - 1)}
              />
            )}

            {/* Image */}
            <img
              src={
                figureOriginalUrls[figureList[previewCurrentIndex]?.figureUuid] ||
                figureList[previewCurrentIndex]?.thumbnailUrl ||
                ''
              }
              alt={figureList[previewCurrentIndex]?.figureName}
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
              }}
            />

            {/* Next Button */}
            {previewCurrentIndex < figureList.length - 1 && (
              <Button
                icon={<RightOutlined />}
                style={{
                  position: 'absolute',
                  right: '20px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  zIndex: 1,
                }}
                onClick={() => handlePreviewFigureChange(previewCurrentIndex + 1)}
              />
            )}
          </div>
        </div>
      </Modal>
    </>
  );
};

export default NotebookNode;
