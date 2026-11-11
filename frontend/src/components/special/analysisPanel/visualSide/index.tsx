import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { AnalysisType } from '@/constants/analysis';
import { NodeState, NodeType } from '@/constants/node';
import { VISUAL_FBID } from '@/constants/visual';
import {
  requestGetDataStructure,
  requestGetFigureInfo,
  requestGetTagList,
} from '@/request/attachedData';
import {
  requestComputationReport,
  requestComputationTrail,
  requestLatestComputation,
  requestRefreshOptimizedErrorDescription,
} from '@/request/computation';
import {
  requestGenerateSingleNodeReport,
  requestGetBranchReportPresignedUrl,
} from '@/request/node';
import { requestSubmitReport } from '@/request/report';
import { processFigurePlaceholders } from '@/util/markdown';
import { writeToClipboard } from '@/util/operationTools';
import { downloadJsonText } from '@/util/saveHelpers';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  CopyOutlined,
  DownloadOutlined,
  DownOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  QuestionCircleOutlined,
  RightOutlined,
  SwapLeftOutlined,
  SwapRightOutlined,
} from '@ant-design/icons';
import {
  Button,
  Empty,
  Form,
  Image,
  Input,
  InputNumber,
  Menu,
  message,
  Modal,
  Space,
  Spin,
  Tabs,
  Tooltip,
} from 'antd';
import { useEffect, useRef, useState } from 'react';
import { default as Markdown, default as ReactMarkdown } from 'react-markdown';
import { useReactFlow } from 'reactflow';
import { useModel } from 'umi';
import AutoGenieProcessTab from './autoGenieProcessTab';
import ErrorMessageTab from './errorMessageTab';
import './index.less';
import style from './index.less';

export default function VisualSider() {
  const collapseRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const { setCenter } = useReactFlow();
  const {
    dataId,
    nodeId,
    plotOnly,
    nodeInfo,
    vitessceState,
    openVitessceDetail,
    isAiRepoGenSelected,
    currentFigureIndex,
    setCurrentFigureIndex,
    targetGenerationId,
  } = useModel('visualPanelControl');
  const {
    analysisId,
    analysisAccessType,
    analysisUpdatedTime,
    activeErrorKey,
    showError,
    errorNodeList,
    currentSelectedNodes,
    instance,
    setTemporaryCenteredNodeId,
  } = useModel('analysis');
  const { dictionary } = useModel('localization');

  const [activePanelKey, setActivePanelKey] = useState<string | string[] | number | number[]>([]);
  const [errorMessage, setErrorMessage] = useState({});
  const [errorSolution, setErrorSolution] = useState({});
  const [errorMessageAndSolution, setErrorMessageAndSolution] = useState({});
  const [errorMessageAndSolutionLoading, setErrorMessageAndSolutionLoading] = useState({});
  const [errorLogShow, setErrorLogShow] = useState({});
  const [errorMessageLog, setErrorMessageLog] = useState({});
  const [errorMessageLogLoading, setErrorMessageLogLoading] = useState({});
  const [errorMessageReportForm] = Form.useForm();
  const [errMessageReportNodeId, setErrMessageReportNodeId] = useState(null);
  const [isErrorReporting, setIsErrorReporting] = useState(false);

  // const [isVisualPanelExpanded, setIsVisualPanelExpanded] = useState(true);
  const [figureList, setFigureList] = useState([]);
  const [currentFigure, setCurrentFigure] = useState<any>(null);
  const [currentFigureUrl, setCurrentFigureUrl] = useState<string>('');
  const [currentFigureUuidList, setCurrentFigureUuidList] = useState<string[]>([]);
  const [isNodeHasFigure, setIsNodeHasFigure] = useState(false);
  const [isFigureLoading, setIsFigureLoading] = useState(false);

  const { status, statusReason, createdTime } = vitessceState || {};
  const [isSpatialCollapsed, setIsSpatialCollapsed] = useState(true);

  const [isDataFieldCollapsed, setIsDataFieldCollapsed] = useState(true);
  const [isDataFieldLoading, setIsDataFieldLoading] = useState(false);
  const [dataStructure, setDataStructure] = useState<any>({});
  const [layersNames, setLayersNames] = useState<string[]>([]);
  const [layersData, setLayersData] = useState<any[]>([]);
  const [obsData, setObsData] = useState([]);
  const [isObsDataCatModalVisible, setIsObsDataCatModalVisible] = useState(false);
  const [obsModalContent, setObsModalContent] = useState([]);
  const [obsmNames, setObsmNames] = useState<string[]>([]);
  const [obsmData, setObsmData] = useState<any[]>([]);
  const [varData, setVarData] = useState<any[]>([]);
  const [isVarDataCatModalVisible, setIsVarDataCatModalVisible] = useState(false);
  const [varModalContent, setVarModalContent] = useState([]);
  const [varmNames, setVarmNames] = useState<string[]>([]);
  const [varmData, setVarmData] = useState<any[]>([]);
  const [trimmedDataFieldContent, setTrimmedDataFieldContent] = useState<{
    layers: any;
    obs: any;
    obsm: any;
    var: any;
    varm: any;
  } | null>(null);
  const [showDataFieldDownloadModal, setShowDataFieldDownloadModal] = useState(false);

  const [aiInterpDetail, setAiInterpDetail] = useState<null | string>(null);
  const [isAiInterpDetailLoading, setIsAiInterpDetailLoading] = useState(false);
  const [aiInterpGenerating, setAiInterpGenerating] = useState(false);
  const [aiInterpGenerated, setAiInterpGenerated] = useState(false);
  const [isReportViewModalVisible, setIsReportViewModalVisible] = useState(false);
  const [reportMarkdownContent, setReportMarkdownContent] = useState<string>('');
  const [reportContentSections, setReportContentSections] = useState<
    {
      type: 'markdown' | 'figure';
      content: string;
      nodeId?: string;
      nodeName?: string;
      alt?: string;
    }[]
  >([]);
  const [isViewingReport, setIsViewingReport] = useState(false);
  const [isDownloadingReport, setIsDownloadingReport] = useState(false);

  // Tab management state
  const [activeTabKey, setActiveTabKey] = useState('auto-genie-process');

  const allButtonsDisabled =
    nodeInfo.state === NodeState.RUNNING ||
    nodeInfo.state === NodeState.PENDING ||
    nodeInfo.state === NodeState.DEBUGGING;

  const linkNewVpPage = () => {
    if (analysisId && nodeId && dataId) {
      window.open(`/visual-panel/?analysis-id=${analysisId}&node-id=${nodeId}&data-id=${dataId}`);
    } else {
      message.error(
        'An error occurred while trying to open the visual panel. Please check the console for details.',
      );
    }
  };

  const jumpToVisualPanel = async () => {
    try {
      if (
        !analysisId ||
        !nodeId ||
        currentFigureIndex === undefined ||
        !nodeInfo?.tag ||
        !currentFigureUuidList
      ) {
        throw new Error('One or more required parameters are missing or undefined.');
      }

      const { data: latestComputation } = await requestLatestComputation(nodeId ?? '');
      const { resultDataId } = latestComputation;
      const currentFigureUuid = currentFigureUuidList[currentFigureIndex];

      window.open(
        `/visual-panel?analysis-id=${analysisId}&node-id=${nodeId}&data-id=${resultDataId}&tag-name=${nodeInfo.tag}&chart-uuid=${currentFigureUuid}`,
      );
    } catch (error) {
      console.error('Error in jumpToVisualPanel:', error);
      alert(
        'An error occurred while trying to open the visual panel. Please check the console for details.',
      );
    }
  };

  const processErrorMessage = async (curErrorNodeId, latestComputation) => {
    const errorMessage = latestComputation.optimizedErrorDescription;

    if (errorMessage) {
      if (errorMessage.startsWith('```')) {
        // Handle markdown format
        const parts = errorMessage.split('error_message:');
        if (parts.length > 1) {
          const solutionParts = parts[1].split('solution:');
          if (solutionParts.length > 1) {
            setErrorMessage({ ...errorMessage, [curErrorNodeId]: solutionParts[0].trim() });
            setErrorSolution({ ...errorSolution, [curErrorNodeId]: solutionParts[1].trim() });
            setErrorMessageAndSolution({ ...errorMessageAndSolution, [curErrorNodeId]: '' });
          } else {
            setErrorMessageAndSolution({
              ...errorMessageAndSolution,
              [curErrorNodeId]: errorMessage,
            });
            setErrorMessage({ ...errorMessage, [curErrorNodeId]: '' });
            setErrorSolution({ ...errorSolution, [curErrorNodeId]: '' });
          }
        } else {
          setErrorMessageAndSolution({
            ...errorMessageAndSolution,
            [curErrorNodeId]: errorMessage,
          });
          setErrorMessage({ ...errorMessage, [curErrorNodeId]: '' });
          setErrorSolution({ ...errorSolution, [curErrorNodeId]: '' });
        }
      } else {
        // Handle non-markdown format with backticks
        const parts = errorMessage.split('`error_message:`');
        if (parts.length > 1) {
          const solutionParts = parts[1].split('`solution:`');
          if (solutionParts.length > 1) {
            setErrorMessage({ ...errorMessage, [curErrorNodeId]: solutionParts[0].trim() });
            setErrorSolution({ ...errorSolution, [curErrorNodeId]: solutionParts[1].trim() });
            setErrorMessageAndSolution({ ...errorMessageAndSolution, [curErrorNodeId]: '' });
          } else {
            setErrorMessageAndSolution({
              ...errorMessageAndSolution,
              [curErrorNodeId]: errorMessage,
            });
            setErrorMessage({ ...errorMessage, [curErrorNodeId]: '' });
            setErrorSolution({ ...errorSolution, [curErrorNodeId]: '' });
          }
        } else {
          setErrorMessageAndSolution({
            ...errorMessageAndSolution,
            [curErrorNodeId]: errorMessage,
          });
          setErrorMessage({ ...errorMessage, [curErrorNodeId]: '' });
          setErrorSolution({ ...errorSolution, [curErrorNodeId]: '' });
        }
      }
    } else {
      setErrorMessageAndSolution({
        ...errorMessageAndSolution,
        [curErrorNodeId]: 'Please refer to the error log below',
      });
      setErrorMessage({ ...errorMessage, [curErrorNodeId]: '' });
      setErrorSolution({ ...errorSolution, [curErrorNodeId]: '' });
    }
    setErrorMessageLog({
      ...errorMessageLog,
      [curErrorNodeId]: latestComputation.errorDescription,
    });
    setErrorMessageAndSolutionLoading({
      ...errorMessageAndSolutionLoading,
      [curErrorNodeId]: false,
    });
    setErrorMessageLogLoading({ ...errorMessageLogLoading, [curErrorNodeId]: false });
  };

  const handleErrPanelChange = async (activePanelKey) => {
    const newErrorLogShow = { ...errorLogShow, [activePanelKey]: true };
    setErrorLogShow(newErrorLogShow);
    setErrorMessageLogLoading({ ...errorMessageLogLoading, [activePanelKey]: true });
    setErrorMessageAndSolutionLoading({
      ...errorMessageAndSolutionLoading,
      [activePanelKey]: true,
    });

    const { data: latestComputation } = await requestLatestComputation(activePanelKey);
    processErrorMessage(activePanelKey, latestComputation);
    setActivePanelKey([activePanelKey]);
  };

  const onErrMessageRefresh = async (curErrorNodeId) => {
    setErrorMessageAndSolutionLoading((prevState) => ({ ...prevState, [curErrorNodeId]: true }));
    setErrorMessageLogLoading((prevState) => ({ ...prevState, [curErrorNodeId]: true }));
    try {
      const { data: latestComputation } = await requestLatestComputation(curErrorNodeId);
      const { id } = latestComputation;
      await requestRefreshOptimizedErrorDescription(id);
      const { data: refreshResult } = await requestLatestComputation(curErrorNodeId);
      await processErrorMessage(curErrorNodeId, refreshResult);

      message.success('Refresh successfully.');
    } catch (e) {
      message.error('Refresh failed.');
    }
  };

  const onErrMessageReport = async (curErrorNodeId) => {
    setErrMessageReportNodeId(curErrorNodeId);
    errorMessageReportForm.setFieldValue('nodeId', activeErrorKey);
  };

  const onReportConfirm = () => {
    errorMessageReportForm.submit();
  };

  const onReportSubmit = async (values) => {
    try {
      setIsErrorReporting(true);
      const { nodeId, summary, description } = values;
      await requestSubmitReport(nodeId, summary, description);
      setErrMessageReportNodeId(null);
      errorMessageReportForm.resetFields();
      message.success('Report successfully.');
    } catch (e) {
      message.error('Report failed.');
    } finally {
      setIsErrorReporting(false);
    }
  };

  const onCancelReport = () => {
    setErrMessageReportNodeId(null);
    errorMessageReportForm.resetFields();
  };

  const handleErrorMessageMenuClick =
    (curErrorNodeId) =>
    async ({ key }) => {
      if (key === 'refresh') {
        await onErrMessageRefresh(curErrorNodeId);
      } else if (key === 'report') {
        await onErrMessageReport(curErrorNodeId);
      }
    };

  const getErrorMessageMenu = (curErrorNodeId) => (
    <Menu onClick={handleErrorMessageMenuClick(curErrorNodeId)}>
      <Menu.Item key="refresh" disabled={analysisAccessType === AnalysisType.PUBLIC}>
        Refresh
      </Menu.Item>
      <Menu.Item key="report" disabled={analysisAccessType === AnalysisType.PUBLIC}>
        Report
      </Menu.Item>
    </Menu>
  );

  const onCollapseChange = async (key: string | string[] | number | number[]) => {
    setActivePanelKey(key);
    if (Array.isArray(key)) {
      for (const k of key) {
        await handleErrPanelChange(k);
      }
    } else {
      await handleErrPanelChange(key);
    }
  };

  useEffect(() => {
    const updateErrorNodeInfo = async () => {
      if (!activeErrorKey) {
        return;
      }
      try {
        const { data: latestComputation } = await requestLatestComputation(activeErrorKey + '');
        processErrorMessage(activeErrorKey, latestComputation);
      } catch (error) {
        console.error('Error fetching node info:', error);
      }
    };

    updateErrorNodeInfo();
  }, [activeErrorKey, analysisUpdatedTime]);

  useEffect(() => {
    const handleErrorNodeFocus = async () => {
      if (!activeErrorKey) {
        return;
      }

      try {
        const position: { x: number; y: number } | null = (() => {
          const targetNode = instance
            .toObject()
            .nodes.find((element) => element.id + '' === activeErrorKey + '');

          return targetNode ? { x: targetNode.position.x, y: targetNode.position.y } : null;
        })();

        if (position) {
          setTemporaryCenteredNodeId(activeErrorKey.toString());

          setTimeout(() => {
            setTemporaryCenteredNodeId(null);
          }, 800);
          await setCenter(position.x + 130, position.y + 75, { duration: 0, zoom: 1 });
        }

        await handleErrPanelChange(activeErrorKey);

        setTimeout(() => {
          const collapseElement = collapseRefs.current[activeErrorKey];
          if (collapseElement) {
            collapseElement.scrollIntoView({
              behavior: 'smooth',
              block: 'start',
              inline: 'nearest',
            });
          }
        }, 300);
      } catch (error) {
        console.error('Error focusing node:', error);
      }
    };

    handleErrorNodeFocus();
  }, [activeErrorKey, showError]);

  // const toggleVisualPanelCollapse = () => {
  //   setIsVisualPanelExpanded(!isVisualPanelExpanded);
  // };

  const resetFigureState = () => {
    setIsNodeHasFigure(false);
    setFigureList([]);
    setCurrentFigure(null);
  };

  const loadFigureList = async () => {
    if (nodeInfo.state !== NodeState.FINISHED || !nodeId || !dataId) {
      resetFigureState();
      return;
    }
    try {
      const { data: latestComputation } = await requestLatestComputation(nodeId);
      const { resultDataId } = latestComputation;
      const tagList = await requestGetTagList(resultDataId);
      if (!Array.isArray(tagList)) {
        resetFigureState();
        return;
      }

      const currentTag = tagList.find((tag: any) => +tag.node_id === +nodeId);
      if (!currentTag) {
        resetFigureState();
        return;
      }
      setIsNodeHasFigure(true);
      setIsFigureLoading(true);
      const { charts } = currentTag;
      setCurrentFigureUuidList(charts.map((chart: any) => chart.chart_uuid));
      const staticFigureList = charts.filter((chart: any) => chart.exist_type === 'static-image');
      setFigureList(staticFigureList);
      setCurrentFigure(staticFigureList[currentFigureIndex] || null);
    } catch (error) {
      console.error('Error loading figure list:', error);
      resetFigureState();
    }
  };

  const nextFigure = () => {
    setCurrentFigureIndex((prevIndex) => (prevIndex + 1) % figureList.length);
  };

  const prevFigure = () => {
    setCurrentFigureIndex((prevIndex) => (prevIndex === 0 ? figureList.length - 1 : prevIndex - 1));
  };

  useEffect(() => {
    if (nodeId) {
      loadFigureList();
    }
  }, [nodeId, currentFigureIndex, nodeInfo.state]);

  const loadCurrentFigureUrl = async () => {
    if (!currentFigure) {
      setCurrentFigureUrl('');
      return;
    }
    const { chart_uuid } = currentFigure;
    const url = await requestGetFigureInfo(chart_uuid);
    setIsFigureLoading(false);
    setCurrentFigureUrl(url);
  };

  useEffect(() => {
    loadCurrentFigureUrl();
  }, [currentFigure]);

  const toggleSpatialCollapse = () => {
    setIsSpatialCollapsed(!isSpatialCollapsed);
  };

  const toggleDataFieldCollapse = () => {
    setIsDataFieldCollapsed(!isDataFieldCollapsed);
  };

  const resetDataFieldState = () => {
    setLayersNames([]);
    setLayersData([]);
    setObsData([]);
    setObsmNames([]);
    setObsmData([]);
    setVarData([]);
    setVarmNames([]);
    setVarmData([]);
  };

  const fetchDataField = async () => {
    if (
      (nodeInfo.type !== NodeType.DATA_NODE &&
        nodeInfo.type !== NodeType.DATA_NODE_V2 &&
        nodeInfo.state !== NodeState.FINISHED) ||
      !dataId
    ) {
      resetDataFieldState();
      return;
    }
    setIsDataFieldLoading(true);
    const dataStructure = await requestGetDataStructure(dataId);
    setDataStructure(dataStructure);
    const { layers, obs, obsm, var: varData, varm } = dataStructure ?? {};

    setLayersNames(Object.keys(layers ?? {}));
    setLayersData(Object.values(layers ?? {}));

    setObsData(obs ?? []);

    setObsmNames(Object.keys(obsm ?? {}));
    setObsmData(Object.values(obsm ?? {}));

    setVarData(varData ?? []);

    setVarmNames(Object.keys(varm ?? {}));
    setVarmData(Object.values(varm ?? {}));

    setIsDataFieldLoading(false);
  };

  useEffect(() => {
    if (nodeId) {
      fetchDataField();
    }
  }, [dataId, nodeInfo.state]);

  const showObsModal = (categories) => {
    setObsModalContent(categories);
    setIsObsDataCatModalVisible(true);
  };

  const handleObsModalOk = () => {
    setIsObsDataCatModalVisible(false);
  };

  const showVarModal = (categories) => {
    setVarModalContent(categories);
    setIsVarDataCatModalVisible(true);
  };

  const handleVarModalOk = () => {
    setIsVarDataCatModalVisible(false);
  };

  const openDataFieldDownloadModal = () => {
    setShowDataFieldDownloadModal(true);
  };

  const closeDataFieldDownloadModal = () => {
    setShowDataFieldDownloadModal(false);
  };

  const getFilteredDataStructure = (dataStructure) => {
    let isCategoryItemsLarge = false;
    const hasLargeCategories = (item) => item.categories && item.categories.length > 50;

    const filteredObs = dataStructure.obs.map((item) => {
      if (hasLargeCategories(item)) {
        isCategoryItemsLarge = true;
        return {
          ...item,
          categories: null,
          notes:
            'This category contains more than 50 types. Thus the trimmed json file does not show them here.',
        };
      }
      return item;
    });
    const filteredVar = dataStructure.var.map((item) => {
      if (hasLargeCategories(item)) {
        isCategoryItemsLarge = true;
        return {
          ...item,
          categories: null,
          notes:
            'This category contains more than 50 types. Thus the trimmed json file does not show them here.',
        };
      }
      return item;
    });

    return {
      filteredDataStructure: {
        layers: dataStructure.layers,
        obs: filteredObs,
        obsm: dataStructure.obsm,
        var: filteredVar,
        varm: dataStructure.varm,
      },
      isCategoryItemsLarge,
    };
  };

  const prepareDataStructureForDownload = () => {
    if (!dataStructure) {
      message.error(
        'Data structure is still loading or not available yet. Please try again later.',
      );
      return;
    }
    try {
      const { filteredDataStructure, isCategoryItemsLarge } =
        getFilteredDataStructure(dataStructure);
      if (isCategoryItemsLarge) {
        setTrimmedDataFieldContent(filteredDataStructure);
        openDataFieldDownloadModal();
      } else {
        downloadJsonText(filteredDataStructure, 'data_field');
      }
    } catch (error) {
      message.error('An error occurred while processing the download.');
    }
  };

  const downloadDataField = () => {
    if (!dataStructure) {
      message.error(
        'Data structure is still loading or not available yet. Please try again later.',
      );
      return;
    }
    try {
      const originalDataStructure = dataStructure;
      downloadJsonText(originalDataStructure, 'data_field');
    } catch (error) {
      message.error('An error occurred while processing the download.');
    }
  };

  const loadAiInterpretation = async (nodeId: string) => {
    setIsAiInterpDetailLoading(true);
    try {
      const { data: latestComputation } = await requestLatestComputation(nodeId);
      if (!latestComputation) {
        setAiInterpDetail(null);
        setAiInterpGenerated(false);
        return;
      }
      const { data: aiInterpPresignedUrl } = await requestComputationReport(latestComputation.id);
      if (!aiInterpPresignedUrl) {
        setAiInterpDetail(null);
        setAiInterpGenerated(false);
        return;
      }

      const response = await fetch(aiInterpPresignedUrl);
      const aiInterpDetail = await response.text();

      setAiInterpDetail(aiInterpDetail);
      setAiInterpGenerated(true);
    } catch (error) {
      console.error('Error loading AI interpretation:', error);
      setAiInterpDetail(null);
      setAiInterpGenerated(false);
    } finally {
      setIsAiInterpDetailLoading(false);
    }
  };

  useEffect(() => {
    if (nodeId && nodeInfo.state === NodeState.FINISHED) {
      loadAiInterpretation(nodeId);
    }
  }, [nodeId, nodeInfo.state]);

  const fillAiInterpDetail = async (nodeId: string) => {
    try {
      const { data: computationTrail } = await requestComputationTrail(nodeId);

      try {
        const { data: aiInterpDetail } = await requestGenerateSingleNodeReport(
          nodeId,
          computationTrail,
        );
        setAiInterpDetail(aiInterpDetail);
        setAiInterpGenerated(true);
      } catch (error) {
        setAiInterpGenerating(false);
        message.error({
          content: 'Error requesting single node report.',
          duration: 2,
        });
      }
    } catch (error) {
      setAiInterpGenerating(false);
      message.error({
        content: 'Error requesting node history.',
        duration: 2,
      });
    } finally {
      setAiInterpGenerating(false);
    }
  };

  const handleGenInterpClick = async () => {
    setAiInterpGenerating(true);
    await fillAiInterpDetail(nodeId ?? '');
  };

  const handleCopy = (aiInterpDetail) => (e) => {
    e.stopPropagation();

    if (aiInterpDetail) {
      writeToClipboard(aiInterpDetail)
        .then(() => {
          message.success('Report copied to clipboard');
        })
        .catch((error) => {
          console.error('Copy failed', error); // Debugging line
          message.error('Failed to copy report to clipboard');
        });
    } else {
      message.error('Nothing to copy');
    }
  };

  const handleDownloadReport = async () => {
    setIsDownloadingReport(true);
    try {
      const reportNode = currentSelectedNodes.find((node) => node.type === NodeType.REPORT_NODE);
      if (!reportNode) {
        message.error('No report node selected');
        return;
      }

      const reportId = reportNode.data.reportUuid || reportNode.id;
      const { data } = await requestGetBranchReportPresignedUrl(reportId);

      if (data && data.url) {
        window.open(data.url, '_blank');
        message.success('Report downloaded');
      } else {
        message.error('No download URL available');
      }
    } catch (error) {
      console.error('Download error:', error);
      message.error('Failed to download report');
    } finally {
      setIsDownloadingReport(false);
    }
  };

  const handleViewReport = async () => {
    setIsViewingReport(true);
    try {
      const reportNode = currentSelectedNodes.find((node) => node.type === NodeType.REPORT_NODE);
      if (!reportNode) {
        message.error('No report node selected');
        return;
      }

      const reportId = reportNode.data.reportUuid || reportNode.id;
      const { data } = await requestGetBranchReportPresignedUrl(reportId);

      if (data && data.url) {
        const response = await fetch(data.url);
        const contentType = response.headers.get('content-type');
        let markdownContent = '';

        const urlWithoutQuery = data.url.split('?')[0];
        const isZipFile =
          urlWithoutQuery.endsWith('.zip') || contentType?.includes('application/zip');

        if (isZipFile) {
          const JSZip = (await import('jszip')).default;
          const arrayBuffer = await response.arrayBuffer();
          const zip = await JSZip.loadAsync(arrayBuffer);

          const markdownFiles = Object.keys(zip.files).filter(
            (filename) => filename.endsWith('.md') && !filename.toLowerCase().includes('readme'),
          );

          if (markdownFiles.length > 0) {
            const mainReportFile = markdownFiles[0];
            markdownContent = (await zip.file(mainReportFile)?.async('text')) || '';
          } else {
            const anyMdFile = Object.keys(zip.files).find((filename) => filename.endsWith('.md'));
            if (anyMdFile) {
              markdownContent = (await zip.file(anyMdFile)?.async('text')) || '';
            } else {
              message.error('No markdown file found in the report zip');
              return;
            }
          }

          const contentSections = await processFigurePlaceholders(markdownContent, zip);
          setReportContentSections(contentSections);
          setReportMarkdownContent('');
        } else {
          markdownContent = await response.text();
          setReportContentSections([
            {
              type: 'markdown',
              content: markdownContent,
            },
          ]);
          setReportMarkdownContent('');
        }
        setIsReportViewModalVisible(true);
      } else {
        message.error('No report content available');
      }
    } catch (error) {
      console.error('View error:', error);
      message.error('Failed to load report content');
    } finally {
      setIsViewingReport(false);
    }
  };

  const handleCloseReportViewModal = () => {
    setIsReportViewModalVisible(false);
    setReportMarkdownContent('');
    setReportContentSections([]);
  };

  // Build tab items based on current state and conditions
  const buildTabItems = () => {
    const tabItems: any[] = [
      // Auto Genie Process tab is always present
      {
        key: 'auto-genie-process',
        label: (
          <Space>
            <CustomImage name={customIconNames.AIICONSTAR} style={{ height: '14px' }} />
            Auto Genie Process
          </Space>
        ),
        children: (
          <div className="tab-content-wrapper">
            <AutoGenieProcessTab
              analysisId={analysisId || undefined}
              targetGenerationId={targetGenerationId}
            />
          </div>
        ),
      },
    ];

    // Add Error Message tab if there are error conditions
    if (
      !!activeErrorKey &&
      nodeId &&
      nodeInfo.state === NodeState.FAILED &&
      currentSelectedNodes.length === 1 &&
      !isAiRepoGenSelected
    ) {
      tabItems.push({
        key: 'error-message',
        label: dictionary.ERROR_MESSAGE || 'Error Message',
        children: (
          <div className="tab-content-wrapper">
            <ErrorMessageTab
              errorNodeList={errorNodeList}
              activePanelKey={activePanelKey}
              errorMessage={errorMessage}
              errorSolution={errorSolution}
              errorMessageAndSolution={errorMessageAndSolution}
              errorMessageAndSolutionLoading={errorMessageAndSolutionLoading}
              errorLogShow={errorLogShow}
              errorMessageLog={errorMessageLog}
              errorMessageLogLoading={errorMessageLogLoading}
              onCollapseChange={onCollapseChange}
              getErrorMessageMenu={getErrorMessageMenu}
              collapseRefs={collapseRefs}
            />
          </div>
        ),
      });
    }

    // Add AI Interpretation tab if applicable
    if (
      nodeId &&
      nodeInfo.state === NodeState.FINISHED &&
      !isAiRepoGenSelected &&
      currentSelectedNodes.length === 1
    ) {
      tabItems.push({
        key: 'ai-interpretation',
        label: (
          <Space>
            <CustomImage name={customIconNames.AIICONSTAR} style={{ height: '14px' }} />
            {dictionary.AI_INTERPRETATION}
          </Space>
        ),
        children: (
          <div className="tab-content-wrapper">
            <div className="ai-interpretation-container">
              <div className="ai-interpretation-content">
                <div className="interpretation-title-and-icon-container">
                  <span className="interpretation-title">
                    <CustomImage
                      name={customIconNames.AIICONSTAR}
                      style={{ height: '18px', marginBottom: '5px', marginRight: '3px' }}
                    />
                    {dictionary.AI_INTERPRETATION}
                  </span>
                  {aiInterpGenerated && (
                    <CopyOutlined
                      style={{ cursor: 'pointer' }}
                      onClick={handleCopy(aiInterpDetail)}
                    />
                  )}
                </div>
                <button
                  onClick={handleGenInterpClick}
                  disabled={
                    allButtonsDisabled ||
                    aiInterpGenerating ||
                    analysisAccessType === AnalysisType.PUBLIC
                  }
                  className={`${
                    aiInterpGenerated ? style.regenerateButton : style.generateButton
                  } ${
                    allButtonsDisabled ||
                    aiInterpGenerating ||
                    analysisAccessType === AnalysisType.PUBLIC
                      ? style.disabledButton
                      : ''
                  }`}
                >
                  {aiInterpGenerated ? dictionary.REGENERATE : dictionary.GENERATE}
                </button>
              </div>
              {!aiInterpGenerated && !aiInterpGenerating && !isAiInterpDetailLoading && (
                <p className="no-interpretation-message">No interpretation has been generated</p>
              )}
              <div className="aiMessageContainer">
                {aiInterpGenerating ? (
                  <p>
                    Generating AI interpretation. Usually takes one minute... <LoadingOutlined />
                  </p>
                ) : isAiInterpDetailLoading ? (
                  <p>
                    <LoadingOutlined /> {dictionary.LOADING}...
                  </p>
                ) : aiInterpGenerated ? (
                  <Markdown className="interpretation-detail">{aiInterpDetail}</Markdown>
                ) : (
                  <></>
                )}
              </div>
            </div>
          </div>
        ),
      });
    }

    // Add Visualization tab if node has finished and has figure
    if (
      (nodeId &&
        nodeInfo.state === NodeState.FINISHED &&
        currentSelectedNodes.length === 1 &&
        !isAiRepoGenSelected &&
        nodeInfo.type === NodeType.COMPUTATION_NODE) ||
      nodeInfo.type === NodeType.COMPUTATION_NODE_V2
    ) {
      tabItems.push({
        key: 'visualization',
        label: dictionary.VISUALIZATION_PANEL || 'Visualization',
        children: (
          <div className="tab-content-wrapper">
            <div className="visual-panel-container">
              <div className="visual-panel-content">
                <div className="visual-panel-title-and-icon-container">
                  <span className="visual-panel-title">{dictionary.VISUALIZATION_PANEL}</span>
                </div>
                {!plotOnly && nodeInfo.fbId === VISUAL_FBID && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      (() => (isNodeHasFigure ? jumpToVisualPanel() : linkNewVpPage()))();
                    }}
                    disabled={allButtonsDisabled}
                    className={`${style.openButton} ${
                      allButtonsDisabled ? style.disabledButton : ''
                    }`}
                  >
                    {dictionary.OPEN}
                  </button>
                )}
              </div>
            </div>

            {isFigureLoading ? (
              <div style={{ textAlign: 'center' }}>
                <LoadingOutlined /> {dictionary.LOADING}...
              </div>
            ) : (
              <>
                {!isNodeHasFigure && (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="No plots generated yet"
                  />
                )}
                {!!isNodeHasFigure && (
                  <div style={{ marginLeft: '10px' }}>
                    <Image
                      className="visual-panel-figure"
                      src={currentFigureUrl}
                      alt="Visualization.png"
                    />
                    <div className="figure-nav">
                      <SwapLeftOutlined onClick={prevFigure} className="prev-button" />
                      <span className="figure-index">
                        {currentFigureIndex + 1}/{figureList.length}
                      </span>
                      <SwapRightOutlined onClick={nextFigure} className="next-button" />
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        ),
      });
    }

    // Add Data Field tab if applicable
    if (
      (nodeId || dataId) &&
      (nodeInfo.type === NodeType.DATA_NODE ||
        nodeInfo.type === NodeType.DATA_NODE_V2 ||
        nodeInfo.state === NodeState.FINISHED) &&
      currentSelectedNodes.length === 1 &&
      !isAiRepoGenSelected
    ) {
      tabItems.push({
        key: 'data-field',
        label: dictionary.DATA_FIELD || 'Data Field',
        children: (
          <div className="tab-content-wrapper">
            <div className="data-field-container">
              <div
                className={
                  nodeInfo.type === NodeType.DATA_NODE || nodeInfo.type === NodeType.DATA_NODE_V2
                    ? 'data-node-data-field-content'
                    : 'data-field-content'
                }
                onClick={toggleDataFieldCollapse}
              >
                <div className="data-field-title-and-icon-container">
                  <span className="data-field-title">{dictionary.DATA_FIELD}</span>
                  {isDataFieldCollapsed ? (
                    <RightOutlined style={{ cursor: 'pointer', color: 'rgb(0,0,0,0.45)' }} />
                  ) : (
                    <DownOutlined style={{ cursor: 'pointer', color: 'rgb(0,0,0,0.45)' }} />
                  )}
                </div>
                <DownloadOutlined
                  title="Download data field"
                  style={{ cursor: 'pointer', margin: '0 10px' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    prepareDataStructureForDownload();
                  }}
                />
              </div>
              {/* Data field detailed content */}
              {allButtonsDisabled && !isDataFieldCollapsed ? (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No data generated yet" />
              ) : (
                <>
                  {isDataFieldLoading && !isDataFieldCollapsed ? (
                    <div style={{ textAlign: 'center' }}>
                      <LoadingOutlined /> {dictionary.LOADING}...
                    </div>
                  ) : (
                    !isDataFieldCollapsed && (
                      <>
                        <div className="layers-container">
                          <div className="layers-title">
                            {' '}
                            Layers{' '}
                            <Tooltip
                              title="A dictionary-like object where the values have the same dimensions as a data matrix with a shape of [number of observations] x [number of variables]."
                              trigger={['click']}
                              placement="right"
                              cursor="pointer"
                            >
                              <QuestionCircleOutlined />
                            </Tooltip>
                          </div>
                          <span className="layers-content">
                            {layersNames && layersNames.length > 0 ? (
                              layersNames.map((name, index) => (
                                <div className="layer-item" key={index}>
                                  <div className="layer-name">{name}</div>
                                  <div className="layer-content">
                                    {JSON.stringify(layersData[index])}
                                  </div>
                                </div>
                              ))
                            ) : (
                              <Empty
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                                description="No layers data"
                              />
                            )}
                          </span>
                        </div>

                        <div className="obs-container">
                          <div className="obs-title">
                            {' '}
                            Obs{' '}
                            <Tooltip
                              title="A one-dimensional annotation for observations."
                              trigger={['click']}
                              placement="right"
                              cursor="pointer"
                            >
                              <QuestionCircleOutlined />
                            </Tooltip>
                          </div>
                          <span className="obs-content">
                            {obsData && obsData.length > 0 ? (
                              <div className="obs-item" key="0">
                                <div className="obs-key-title"> key </div>
                                <div className="obs-dtype-title"> dtype </div>
                              </div>
                            ) : null}
                            {obsData && obsData.length > 0 ? (
                              obsData.map(
                                (
                                  item: { key: string; dtype: string; categories: string[] },
                                  index,
                                ) => (
                                  <div className="obs-item" key={index}>
                                    <div className="obs-key">{item.key}</div>
                                    <div className="obs-dtype">
                                      {item.dtype === 'category' ? (
                                        <Tooltip title="View category">
                                          <InfoCircleOutlined
                                            onClick={() => showObsModal(item.categories)}
                                          />
                                        </Tooltip>
                                      ) : null}{' '}
                                      {item.dtype}
                                    </div>
                                  </div>
                                ),
                              )
                            ) : (
                              <Empty
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                                description="No obs data"
                              />
                            )}
                          </span>
                        </div>

                        <div className="obsm-container">
                          <div className="obsm-title">
                            {' '}
                            Obsm{' '}
                            <Tooltip
                              title="A multi-dimensional annotation for observations."
                              trigger={['click']}
                              placement="right"
                              cursor="pointer"
                            >
                              <QuestionCircleOutlined />
                            </Tooltip>
                          </div>
                          <span className="obsm-content">
                            {obsmNames && obsmNames.length > 0 ? (
                              obsmNames.map((name, index) => (
                                <div className="obsm-item" key={index}>
                                  <div className="obsm-name">{name}</div>
                                  <div className="obsm-content">
                                    {JSON.stringify(obsmData[index])}
                                  </div>
                                </div>
                              ))
                            ) : (
                              <Empty
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                                description="No obsm data"
                              />
                            )}
                          </span>
                        </div>

                        <div className="var-container">
                          <div className="var-title">
                            {' '}
                            Var{' '}
                            <Tooltip
                              title="A one-dimensional annotation for variables."
                              trigger={['click']}
                              placement="right"
                              cursor="pointer"
                            >
                              <QuestionCircleOutlined />
                            </Tooltip>
                          </div>
                          <span className="var-content">
                            {varData && varData.length > 0 ? (
                              <div className="var-item" key="0">
                                <div className="var-key-title"> key </div>
                                <div className="var-dtype-title"> dtype </div>
                              </div>
                            ) : null}
                            {varData && varData.length > 0 ? (
                              varData.map(
                                (
                                  item: { key: string; dtype: string; categories: string[] },
                                  index,
                                ) => (
                                  <div className="var-item" key={index}>
                                    <div className="var-key">{item.key}</div>
                                    <div className="var-dtype">
                                      {item.dtype === 'category' ? (
                                        <Tooltip title="View category">
                                          <InfoCircleOutlined
                                            onClick={() => showVarModal(item.categories)}
                                          />
                                        </Tooltip>
                                      ) : null}{' '}
                                      {item.dtype}
                                    </div>
                                  </div>
                                ),
                              )
                            ) : (
                              <Empty
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                                description="No var data"
                              />
                            )}
                          </span>
                        </div>

                        <div className="varm-container">
                          <div className="varm-title">
                            {' '}
                            Varm{' '}
                            <Tooltip
                              title="A multi-dimensional annotation for variables."
                              trigger={['click']}
                              placement="right"
                              cursor="pointer"
                            >
                              <QuestionCircleOutlined />
                            </Tooltip>
                          </div>
                          <span className="varm-content">
                            {varmNames && varmNames.length > 0 ? (
                              varmNames.map((name, index) => (
                                <div className="varm-item" key={index}>
                                  <div className="varm-name">{name}</div>
                                  <div className="varm-content">
                                    {JSON.stringify(varmData[index])}
                                  </div>
                                </div>
                              ))
                            ) : (
                              <Empty
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                                description="No varm data"
                              />
                            )}
                          </span>
                        </div>
                      </>
                    )
                  )}
                </>
              )}
            </div>
          </div>
        ),
      });
    }

    // Add Spatial tab if applicable
    if (
      nodeId &&
      nodeInfo.state === NodeState.FINISHED &&
      !isAiRepoGenSelected &&
      currentSelectedNodes.length === 1
    ) {
      tabItems.push({
        key: 'spatial',
        label: 'Vitessce Spatial',
        children: (
          <div className="tab-content-wrapper">
            <div className="spatial-container">
              <div className="spatial-content" onClick={toggleSpatialCollapse}>
                <div className="spatial-title-and-icon-container">
                  <span className="spatial-title">Vitessce spatial</span>
                  {isSpatialCollapsed ? (
                    <RightOutlined style={{ cursor: 'pointer', color: 'rgb(0,0,0,0.45)' }} />
                  ) : (
                    <DownOutlined style={{ cursor: 'pointer', color: 'rgb(0,0,0,0.45)' }} />
                  )}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    openVitessceDetail();
                  }}
                  disabled={allButtonsDisabled || analysisAccessType === AnalysisType.PUBLIC}
                  className={`${style.prehandleButton} ${
                    allButtonsDisabled || analysisAccessType === AnalysisType.PUBLIC
                      ? style.disabledButton
                      : ''
                  }`}
                >
                  {status === 'FAILED'
                    ? 'Retry'
                    : status === 'SUCCESS'
                    ? dictionary.OPEN
                    : dictionary.PREHANDLE}
                </button>
              </div>
              {!isSpatialCollapsed && (
                <>
                  <div className="status-message">
                    <div>{dictionary.STATUS}: </div>
                    <span className="status">{status === undefined ? '---' : status}</span>
                  </div>
                  <div className="status-reason">
                    <div>{dictionary.STATUS_REASON}: </div>
                    <span className="reason">{status === undefined ? '---' : statusReason}</span>
                  </div>
                  <div className="created-time">
                    <div>{dictionary.CREATED_AT}: </div>
                    <span className="time">{status === undefined ? '---' : createdTime}</span>
                  </div>
                </>
              )}
            </div>
          </div>
        ),
      });
    }

    return tabItems;
  };

  return (
    <div className={style.rightSider}>
      <div
        style={{
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      />

      {/* Show report generation interface when AI report generation is selected */}
      {currentSelectedNodes.length === 1 &&
      currentSelectedNodes[0].type === NodeType.REPORT_NODE ? (
        <div className="report-generation-container">
          <div className="sider-bar-title-container">
            <span className="sider-bar-title">
              <FileTextOutlined style={{ marginRight: '6px' }} />
              Report Generation
            </span>
          </div>

          {nodeInfo.state === NodeState.RUNNING && (
            <div className="report-progress-container">
              <div className="progress-step">
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginTop: '16px',
                    marginBottom: '16px',
                    marginLeft: '15px',
                    marginRight: '15px',
                  }}
                >
                  <LoadingOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                  <span style={{ fontWeight: 'bold' }}>Report processing...</span>
                </div>
              </div>
            </div>
          )}

          {nodeInfo.state === NodeState.FINISHED && (
            <div className="report-success-container">
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginTop: '16px',
                  marginBottom: '16px',
                  marginLeft: '15px',
                  marginRight: '15px',
                }}
              >
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                <span style={{ fontWeight: 'bold' }}>Report Generated Successfully!</span>
              </div>

              <div className="report-buttons-container">
                <button
                  className={`${style.openButton} ${isViewingReport ? style.disabledButton : ''}`}
                  onClick={handleViewReport}
                  disabled={isViewingReport}
                  style={{ marginRight: '8px', width: '80px' }}
                >
                  {isViewingReport ? <LoadingOutlined /> : 'View'}
                </button>
                <button
                  className={`${style.openButton} ${
                    isDownloadingReport ? style.disabledButton : ''
                  }`}
                  onClick={handleDownloadReport}
                  disabled={isDownloadingReport}
                  style={{ width: '80px' }}
                >
                  {isDownloadingReport ? <LoadingOutlined /> : 'Download'}
                </button>
              </div>
            </div>
          )}

          {nodeInfo.state === NodeState.FAILED && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                marginLeft: '15px',
                marginRight: '15px',
                marginBottom: '16px',
              }}
            >
              <CloseCircleOutlined style={{ color: '#ff4d4f', marginRight: '8px' }} />
              <span>Report generation failed. Please try again.</span>
            </div>
          )}
        </div>
      ) : (
        /* Show tab interface for all other cases */
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
          }}
        >
          {!(currentSelectedNodes.length === 0) && (
            <div
              style={{
                position: 'sticky',
                top: 0,
                zIndex: 10,
                backgroundColor: 'white',
                borderBottom: '1px solid #f0f0f0',
              }}
            >
              <div className="sider-bar-title-container">
                <span className="sider-bar-title">Analysis Sider</span>
              </div>
            </div>
          )}

          <div className="tabs-container">
            {/* Show welcome message when no node is selected */}
            {nodeInfo.state === null ||
            (nodeInfo.state === NodeState.ORIGINAL && !dataId) ||
            nodeInfo.state === NodeState.CANCELLED ||
            currentSelectedNodes.length === 0 ||
            currentSelectedNodes.length > 1 ||
            (!dataId && !nodeId) ? (
              <div className="no-data-container">
                <div className="welcome-message">{dictionary.analysisGuide.title}</div>
                <div className="start-analysis-tip">{dictionary.analysisGuide.subTitle}</div>
                <div className="steps-container">
                  {dictionary.analysisGuide.steps.map((step: string, index: number) => (
                    <div key={step} className="step">
                      {index + 1}. {step}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* Show tabs interface */
              <Tabs
                activeKey={activeTabKey}
                onChange={setActiveTabKey}
                items={buildTabItems()}
                size="small"
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                }}
                tabBarStyle={{
                  margin: 0,
                  padding: '0 16px',
                  flexShrink: 0,
                }}
              />
            )}
          </div>
        </div>
      )}

      {/* Modals that are always available */}
      <Modal
        centered
        title="Report a Problem"
        open={!!errMessageReportNodeId}
        onOk={onReportConfirm}
        onCancel={onCancelReport}
      >
        <Spin spinning={isErrorReporting}>
          <Form
            form={errorMessageReportForm}
            labelAlign="left"
            labelCol={{ span: 5 }}
            onFinish={onReportSubmit}
            autoComplete="off"
          >
            <p>
              Let the team know if your problem is not solved. Reports are stored on this server
              to help improve the system.
            </p>
            <Form.Item name="nodeId" label="NodeId" rules={[{ required: true }]}>
              <InputNumber readOnly />
            </Form.Item>
            <Form.Item name="summary" label="Summary" rules={[{ required: true }]}>
              <Input.TextArea />
            </Form.Item>
            <Form.Item name="description" label="Description" rules={[{ required: true }]}>
              <Input.TextArea name="summary" />
            </Form.Item>
          </Form>
        </Spin>
      </Modal>

      <Modal
        title={null}
        open={showDataFieldDownloadModal}
        onCancel={closeDataFieldDownloadModal}
        footer={null}
      >
        <div style={{ textAlign: 'center' }}>
          <h3 style={{ alignItems: 'center' }}>
            <ExclamationCircleOutlined style={{ color: 'blue', marginRight: '5px' }} />
            Your data field contains categories with over 50 entries.
          </h3>
          <p>Would you like to download the original data field or a trimmed version?</p>
          <Button
            type="default"
            onClick={() => {
              downloadDataField();
              closeDataFieldDownloadModal();
            }}
            style={{ marginRight: '10px' }}
          >
            Download original data field
          </Button>
          <Button
            type="default"
            onClick={() => {
              downloadJsonText(trimmedDataFieldContent, 'data_field');
              closeDataFieldDownloadModal();
            }}
          >
            Download trimmed data field
          </Button>
        </div>
      </Modal>

      <Modal
        title="Categories"
        open={isObsDataCatModalVisible}
        onOk={handleObsModalOk}
        onCancel={handleObsModalOk}
      >
        <ul>
          {obsModalContent.map((category, index) => (
            <li key={index}>{category}</li>
          ))}
        </ul>
      </Modal>

      <Modal
        title="Categories"
        open={isVarDataCatModalVisible}
        onOk={handleVarModalOk}
        onCancel={handleVarModalOk}
      >
        <ul>
          {varModalContent.map((category, index) => (
            <li key={index}>{category}</li>
          ))}
        </ul>
      </Modal>
      <Modal
        title="Report Viewer"
        open={isReportViewModalVisible}
        onCancel={handleCloseReportViewModal}
        footer={null}
        width={800}
        className="report-viewer-modal"
      >
        <div className="report-content-container">
          {reportContentSections.length > 0 ? (
            (() => {
              let figureCount = 0;
              return reportContentSections.map((section, index) => (
                <div key={index}>
                  {section.type === 'markdown' ? (
                    <ReactMarkdown className="report-markdown-viewer">
                      {section.content}
                    </ReactMarkdown>
                  ) : (
                    <div style={{ textAlign: 'center', margin: '20px 0' }}>
                      <img
                        src={section.content}
                        alt={
                          section.alt ||
                          (section.nodeName
                            ? `Figure for Node ${section.nodeId} (${section.nodeName})`
                            : `Figure for Node ${section.nodeId}`)
                        }
                        style={{
                          maxWidth: '100%',
                          height: 'auto',
                          borderRadius: '8px',
                          padding: '8px',
                          boxShadow: '0 4px 12px rgba(0, 123, 255, 0.15)',
                        }}
                      />
                      <div
                        style={{
                          marginTop: '8px',
                          fontSize: '14px',
                          color: '#666',
                          fontStyle: 'italic',
                        }}
                      >
                        Figure {++figureCount}:{' '}
                        {section.alt ||
                          (section.nodeName
                            ? `Figure for Node ${section.nodeId} (${section.nodeName})`
                            : `Figure for Node ${section.nodeId}`)}
                      </div>
                    </div>
                  )}
                </div>
              ));
            })()
          ) : reportMarkdownContent ? (
            <ReactMarkdown className="report-markdown-viewer">
              {reportMarkdownContent}
            </ReactMarkdown>
          ) : (
            <div className="loading-container">
              <LoadingOutlined /> Loading report content...
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}
