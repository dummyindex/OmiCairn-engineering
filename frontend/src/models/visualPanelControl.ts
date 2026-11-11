import { VitessceStatus, type VitessceState } from '@/interfaces/visualPanel';
import {
  requestGetDataStructure,
  requestGetGenesetList,
  requestGetTagList,
} from '@/request/attachedData';
import { requestStartVitesscePrehandle, requestVitessceState } from '@/request/data';
import { waitForVitesscePrehandle } from '@/util/vitesscePrehandleMonitor';
import { message } from 'antd';
import React, { useEffect, useRef } from 'react';

export type ClippingRangeItem = {
  key: string;
  min: number;
  max: number;
};

const useVisualPanelControl = () => {
  const [open, setOpen] = React.useState(false);
  // Download image
  const chartRef = React.useRef(null as null | string);

  // which node is selected
  const [nodeId, setNodeId] = React.useState<string | null>(null);

  type NodeInfo = {
    type: string | null;
    tag: string | null;
    state: string | null;
    fbId: number | null;
  };

  const [nodeInfo, setNodeInfo] = React.useState<NodeInfo>({
    type: null,
    tag: null,
    state: null,
    fbId: null,
  });

  // which data is selected
  const [dataId, setDataId] = React.useState<string | null>(null);

  const [dataStructure, setDataStructure] = React.useState<any>(null);

  const currentDataIdRef = useRef<string | null>(null);

  const [plotOnly, setPlotOnly] = React.useState(false);

  const [isAiRepoGenSelected, setIsAiRepoGenSelected] = React.useState(false);

  const [generatedRepoCNT, setGeneratedRepoCNT] = React.useState(0);

  const [reportSelectedNodeIds, setReportSelectedNodeIds] = React.useState<any[]>([]);

  // is panel loading
  const [loading, setLoading] = React.useState(false);

  // is panel loaded error
  const [error, setError] = React.useState(false);

  // dynamic tag
  const [tagList, setTagList] = React.useState<any[]>([]);

  const [genesetList, setGenesetList] = React.useState<any[]>([]);

  // vitessce related
  const [vitessceState, setVitessceState] = React.useState<VitessceState | null>(null);
  const [startingPrehandleVitessce, setStartingPrehandleVitessce] = React.useState(false);

  const [vitessceDetailVisible, setVitessceDetailVisible] = React.useState(false);

  const [currentFigureIndex, setCurrentFigureIndex] = React.useState(0);
  const [isFiguresLoaded, setIsFiguresLoaded] = React.useState(false);
  const [fbVersionId, setFbVersionId] = React.useState<string | null>(null);
  const [isToolbarCollapsed, setIsToolbarCollapsed] = React.useState(false);

  const [isShowMenu, setIsShowMenu] = React.useState<boolean>(true);
  const [isShowVisual, setIsShowVisual] = React.useState<boolean>(true);
  const [isShowAIDashboard, setIsShowAIDashboard] = React.useState<boolean>(false);
  const [leftSiderWidth, setLeftSiderWidth] = React.useState<number>(18);
  const [rightSiderWidth, setRightSiderWidth] = React.useState<number>(21);
  const [dashboardSiderWidth, setDashboardSiderWidth] = React.useState<number>(52);

  type ChatbotMode = 'minimized' | 'expanded' | 'maximized';

  const [chatbotState, setChatbotState] = React.useState<{
    isVisible: boolean;
    isLoading: boolean;
    mode: ChatbotMode;
  }>({
    isVisible: false,
    isLoading: false,
    mode: 'expanded',
  });

  type ChatContextType = 'analysis' | 'pipeline' | 'node' | 'multinodes';
  const [chatContext, setChatContext] = React.useState<ChatContextType>('analysis');

  // Error and Process Tabs state
  const [errorAndProcessActiveTab, setErrorAndProcessActiveTab] = React.useState<string>('error');
  const [targetGenerationId, setTargetGenerationId] = React.useState<number | null>(null);

  const initVitessceState = async () => {
    if (!dataId) {
      return;
    }
    const vitessceState = await requestVitessceState(dataId);
    setVitessceState(vitessceState);
    if (!vitessceState) {
      return;
    }

    if ([VitessceStatus.PENDING, VitessceStatus.RUNNING].includes(vitessceState.status)) {
      const { dispatchSuccess, vitessceState: doneVitessceeState } = await waitForVitesscePrehandle(
        dataId,
      );
      if (
        !dispatchSuccess ||
        !doneVitessceeState ||
        doneVitessceeState.dataId !== currentDataIdRef.current
      ) {
        return;
      }
      setVitessceState(doneVitessceeState);
    }
  };

  const startPrehandleVitessce = async (options: any) => {
    setStartingPrehandleVitessce(true);
    try {
      if (!dataId) {
        throw new Error('dataId is null');
      }
      if (!nodeId) {
        throw new Error('nodeId is null');
      }
      const newVitessceState = await requestStartVitesscePrehandle(dataId, nodeId, options);
      setVitessceState(newVitessceState);
      message.success('Successfully started prehandle for vitessce');
      setStartingPrehandleVitessce(false);
      const { dispatchSuccess, vitessceState: doneVitessceeState } = await waitForVitesscePrehandle(
        dataId,
      );
      if (
        !dispatchSuccess ||
        !doneVitessceeState ||
        doneVitessceeState.dataId !== currentDataIdRef.current
      ) {
        return;
      }
      setVitessceState(doneVitessceeState);
    } catch (e) {
      message.error('Failed to start prehandle for vitessce');
      setStartingPrehandleVitessce(false);
    }
  };

  const openVitessceDetail = () => {
    setVitessceDetailVisible(true);
  };

  const closeVitessceDetail = () => {
    setVitessceDetailVisible(false);
  };

  const initVisualPanel = async (dataId: string, nodeId: string, plotOnly: boolean) => {
    setDataId(dataId);
    setNodeId(nodeId);
    setPlotOnly(plotOnly);
    if (!dataId) {
      setTagList([]);
      setDataStructure(null);
      setGenesetList([]);
      return;
    }
    setLoading(true);
    try {
      if (plotOnly) {
        const tagList = await requestGetTagList(dataId);
        setTagList(tagList);
        setDataStructure(null);
        setGenesetList([]);
      } else {
        const [newDataStructure, newTagList, newGenesetList] = await Promise.all([
          requestGetDataStructure(dataId),
          requestGetTagList(dataId),
          requestGetGenesetList(dataId),
        ]);
        setTagList(newTagList);
        setDataStructure(newDataStructure);
        setGenesetList(newGenesetList);
      }
    } catch (e: any) {
      console.error(e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    currentDataIdRef.current = dataId;
    initVitessceState();
  }, [dataId]);

  return {
    open,
    setOpen,
    nodeId,
    setNodeId,
    nodeInfo,
    setNodeInfo,
    dataId,
    setDataId,
    plotOnly,
    isAiRepoGenSelected,
    setIsAiRepoGenSelected,
    generatedRepoCNT,
    setGeneratedRepoCNT,
    reportSelectedNodeIds,
    setReportSelectedNodeIds,
    initVisualPanel,
    loading,
    error,
    tagList,
    setTagList,
    chartRef,
    dataStructure,
    genesetList,
    vitessceState,
    startingPrehandleVitessce,
    startPrehandleVitessce,
    openVitessceDetail,
    closeVitessceDetail,
    vitessceDetailVisible,
    currentFigureIndex,
    setCurrentFigureIndex,
    isFiguresLoaded,
    setIsFiguresLoaded,
    fbVersionId,
    setFbVersionId,
    isToolbarCollapsed,
    setIsToolbarCollapsed,
    isShowMenu,
    setIsShowMenu,
    isShowVisual,
    setIsShowVisual,
    isShowAIDashboard,
    setIsShowAIDashboard,
    leftSiderWidth,
    setLeftSiderWidth,
    rightSiderWidth,
    setRightSiderWidth,
    dashboardSiderWidth,
    setDashboardSiderWidth,
    chatbotState,
    setChatbotState,
    chatContext,
    setChatContext,
    errorAndProcessActiveTab,
    setErrorAndProcessActiveTab,
    targetGenerationId,
    setTargetGenerationId,
  };
};

export default useVisualPanelControl;
