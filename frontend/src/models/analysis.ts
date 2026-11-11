import { FlowMode } from '@/constants/flow';
import { NodeState, NodeType } from '@/constants/node';
import { requestCreateEdge, requestEdgeListOfAnalysis } from '@/request/edge';
import {
  requestCopyNode,
  requestDeleteNode,
  requestDeleteNodeList,
  requestEditNodeName,
  requestEditNodeParams,
  requestEditNodeTag,
  requestNodeListOfAnalysis,
  requestNodePreviteStateDict,
  requestUpdateNodePositionList,
} from '@/request/node';
import { requestDispatchTask, requestExtendTask } from '@/request/task';
import { FlowTool } from '@/util/flowTool';
import { getLocationParams } from '@/util/getUrl';
import { message, Form } from 'antd';
import { useEffect, useState } from 'react';
import { addEdge, getConnectedEdges, useEdgesState, useNodesState } from 'reactflow';
import { requestPublicFBGroupList, requestPrivateFBGroupList } from '@/request/functionBlock';
import { AdobePagemaker } from '@/util/adobePagemaker';
import { analysisMonitor } from '@/util/analysisMonitor';
import promiseConfirm from '@/components/common/promiseConfirm';
import type { DataType } from '@/interfaces/data';
import { requestDataSourceList } from '@/request/data';
import { DataListFetchMode } from '@/constants/data';
import { DefaultComputationResourceConfig } from '@/constants/computationResource';
import { requestAnalysisDetail, requestEditAnalysis } from '@/request/analysis';

interface NodeStatistic {
  total: number;
  running: number;
  failed: number;
  success: number;
  pending: number;
  debugging: number;
}

const useAnalysis = () => {
  const [pollInterval] = useState<number>(10000);

  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [analysisDetail, setAnalysisDetail] = useState<any>({});
  const [analysisAccessType, setAnalysisAccessType] = useState<string | null>(null);
  const [analysisUpdatedTime, setAnalysisUpdatedTime] = useState<any>(null);
  const [instance, setInstance] = useState<any>(null);
  const [panelMode, setPanelMode] = useState<string>(FlowMode.COMPUTATION_FLOW);
  const [autoState, setAutoState] = useState<boolean>(true);
  const [compactMode, setCompactMode] = useState<boolean>(false);
  const [positionDif, setPositionDif] = useState<any>({});

  const [shiftKey, setShiftKey] = useState<boolean>(false);
  const [isClickBlank, setIsClickBlank] = useState<boolean>(false);
  const [nodeBorder, setNodeBorder] = useState(false);
  const [isFbClick, setIsFbClick] = useState(false);

  const [currentSelectedNodes, setCurrentSelectedNodes] = useState<any[]>([]);
  const [temporaryCenteredNodeId, setTemporaryCenteredNodeId] = useState<string | null>(null);
  // Nodes and edges are both maintained via elements
  const [nodes, setNodes] = useNodesState([]);
  const [edges, setEdges] = useEdgesState([]);
  const [importedDataSourceList, setImportedDataSourceList] = useState<DataType[]>([]);

  // State holding the node count for each status
  const [nodeStatistic, setNodeStatistic] = useState<NodeStatistic>({
    total: 0,
    running: 0,
    failed: 0,
    success: 0,
    pending: 0,
    debugging: 0,
  } as NodeStatistic);
  const [nodeList, setNodeList] = useState<any[]>([]);
  const [edgeList, setEdgeList] = useState<any[]>([]);
  const [errorNodeList, setErrorNodeList] = useState<any[]>([]);

  const [calcuLogInspectedNodeId, setCalcuLogInspectedNodeId] = useState<string | number | null>(
    null,
  );
  const [jobInfoInspectedNodeId, setJobInfoInspectedNodeId] = useState<string | number | null>(
    null,
  );
  const [jobDetailsInspectedNodeId, setJobDetailsInspectedNodeId] = useState<
    string | number | null
  >(null);

  const [autoGenieInspectedNodeId, setAutoGenieInspectedNodeId] = useState<string | null>(null);
  const [bugFixerInspectedNodeId, setBugFixerInspectedNodeId] = useState<string | null>(null);
  const [agentHistoryInspectedNodeId, setAgentHistoryInspectedNodeId] = useState<string | null>(
    null,
  );
  const [beautifierInspectedNodeId, setBeautifierInspectedNodeId] = useState<string | null>(null);

  const [selectedBlocks, setSelectedBlocks] = useState<number[]>([]);
  const [isSelectFbModalOpen, setIsSelectFbModalOpen] = useState<boolean>(false);
  const [dataCollectedNodeId, setDataCollectedNodeId] = useState<string | number | null>(null);
  const [outputsListInspectedNodeId, setOutputsListInspectedNodeId] = useState<
    string | number | null
  >(null);
  const [bugFixerHistoryInspectedNodeId, setBugFixerHistoryInspectedNodeId] = useState<
    string | null
  >(null);
  const [autoGenieContextInspectedNodeId, setAutoGenieContextInspectedNodeId] = useState<
    string | null
  >(null);
  // Tool dialog
  //// Rename node
  const [renamedNodeId, setRenamedNodeId] = useState<string | null>(null);
  const [renamedNodeForm] = Form.useForm();

  const [showError, setShowError] = useState(false);
  const [activeErrorKey, setActiveErrorKey] = useState<string | number | null>(null);
  const [changeNode, setChangeNode] = useState<boolean>(false);

  //// Edit node label
  const [retagNodeId, setRetagNodeId] = useState<string | null>(null);
  const [retagNodeForm] = Form.useForm();

  const [computationResourceChangingNodeId, setComputationResourceChangingNodeId] = useState<
    string | null
  >(null);
  const [computationResourceChangingInfo, setComputationResourceChangingInfo] = useState<any>(
    DefaultComputationResourceConfig,
  );
  const [isViewOnlyMode, setIsViewOnlyMode] = useState<boolean>(false);

  const [previteStateDict, setPreviteStateDict] = useState<any>({});

  const [paramEditedNodeId, setParamEditedNodeId] = useState<string | null>(null);
  const [paramEditedFbId, setParamEditedFbId] = useState<string | null>(null);

  const [isCloseBtnClicked, setIsCloseBtnClicked] = useState<boolean>(false);

  const [fixedNodeId, setFixedNodeId] = useState<string | null>(null);

  const getAnalysisDetail = async (analysisId) => {
    const { data: detail } = await requestAnalysisDetail(analysisId);
    setAnalysisDetail(detail);
  };

  const updateAnalysisInfo = async (postData: any) => {
    if (!analysisId) {
      message.error('analysisId is null');
      return;
    }
    await requestEditAnalysis(analysisId, postData);
  };

  useEffect(() => {
    if (analysisId) {
      getAnalysisDetail(analysisId);
    }
  }, [analysisId]);

  const openRenameNode = (id: string) => {
    setRenamedNodeId(id);
  };

  const closeRenameNode = () => {
    setRenamedNodeId(null);
    renamedNodeForm.resetFields();
  };

  const openRetagNode = (id: string) => {
    setRetagNodeId(id);
  };

  const closeRetagNode = () => {
    setRetagNodeId(null);
    retagNodeForm.resetFields();
  };

  const deleteNode = async (id: string, node: any, edges: any) => {
    await requestDeleteNode(id);
    const connectedEdgeIds = getConnectedEdges([node], edges).map((item) => {
      return item.id;
    });
    setNodes((nds) => nds.filter((node) => node.id !== id));
    setEdges((eds) => {
      return eds.filter((e) => !connectedEdgeIds.includes(e.id));
    });
  };

  const deleteNodeBatch = async (idList: string[], nodes: any, edges: any) => {
    await requestDeleteNodeList(idList);
    const connectedEdgeIds = getConnectedEdges(nodes, edges).map((item) => {
      return item.id;
    });
    const idSet = new Set(idList);
    setNodes((nds) => nds.filter((node) => !idSet.has(node.id + '')));
    setEdges((eds) => {
      return eds.filter((e) => !connectedEdgeIds.includes(e.id));
    });
  };

  const renameNode = async (id: string, nodeName: string) => {
    await requestEditNodeName(id, nodeName);
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === id) {
          node.data = {
            ...node.data,
            label: nodeName,
          };
        }
        return node;
      }),
    );
  };

  // Async function that updates node positions
  const updateNodePosition = (movedList: any[]) => {
    const targetNodeId2XyMap = new Map();
    movedList.forEach((item) => {
      targetNodeId2XyMap.set(item.node_id, { x: item.x, y: item.y });
    });

    setNodes((nds) =>
      nds.map((item) => {
        if (targetNodeId2XyMap.has(item.id)) {
          item.position = targetNodeId2XyMap.get(item.id);
        }
        return item;
      }),
    );
  };

  const globalLayout = async () => {
    if (!instance) return;

    const getSpaceHeight = (compactMode: boolean, figureVisible: boolean): number => {
      if (compactMode) {
        return figureVisible ? 400 : 200;
      }
      return figureVisible ? 400 : 200;
    };

    const spaceHeight = getSpaceHeight(compactMode, analysisDetail?.figureVisible);

    let instanceData = instance;
    if (analysisDetail?.errorNodeHidden) {
      instanceData = instance.toObject();
      const { edges: originalEdges, nodes: originalNodes } = instanceData;

      const visibleNodes = originalNodes.filter((node: any) => node.state !== NodeState.FAILED);
      const visibleNodeIds = new Set(visibleNodes.map((node: any) => node.id));

      const visibleEdges = originalEdges.filter(
        (edge: any) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target),
      );

      instanceData = {
        toObject: () => ({
          edges: visibleEdges,
          nodes: visibleNodes,
        }),
      };
    }

    const nodeInformation = new AdobePagemaker(instanceData);
    const { branchMapList, singleNodeList } = nodeInformation.getBranchListAndSingleList();
    let treeHeight: number = 0;

    const singleMapList = singleNodeList.map((item) => {
      return new Map([[item, []]]);
    });
    branchMapList.push(...singleMapList);
    branchMapList.sort((item1, item2) => {
      const rootNodeId1 = item1.keys().next().value;
      const rootNodeId2 = item2.keys().next().value;
      const { y: y1 } = nodeInformation.getNodePosition(rootNodeId1);
      const { y: y2 } = nodeInformation.getNodePosition(rootNodeId2);
      return y1 - y2;
    });
    // Branch layout
    const newNodePositionList: any[] = [];
    for (const item of branchMapList) {
      const itemArray = [...item.keys()];
      const treeData = nodeInformation.buildTree(itemArray[0]);

      const [nodePositionList, yDifference]: [any[], number] =
        await nodeInformation.branchSearchTraversal(treeData, treeHeight, 400, spaceHeight);
      // const paths = nodeInformation.depthFirstTraversalWithPaths(treeData);
      // console.log('paths', paths);
      newNodePositionList.push(...nodePositionList);
      treeHeight = yDifference + spaceHeight;
    }
    updateNodePosition(newNodePositionList);
    await requestUpdateNodePositionList(newNodePositionList);
  };

  const retagNode = async (id: string, tag: string) => {
    await requestEditNodeTag(id, tag);
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === id) {
          node.data = {
            ...node.data,
            tag,
          };
        }
        return node;
      }),
    );
  };

  const changeNodeState = (id: string, newState: string) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === id) {
          node.data = {
            ...node.data,
            state: newState,
          };
        }
        return node;
      }),
    );
  };

  const runSubTree = async (nodeId: string, instance: any) => {
    const [analysisId] = getLocationParams(['analysis-id']);
    const flowTool = new FlowTool(instance);
    const node = flowTool.getNode(nodeId);
    const resultSub = flowTool.findComputableSubtree(nodeId);
    const { nodeIdList: nodeSufIdList, edgeIdList: edgeSufIdList } = flowTool.getIdList(resultSub);
    if (node.type === NodeType.DATA_NODE || node.type === NodeType.DATA_NODE_V2) {
      const confirmed = await promiseConfirm({
        title: 'Confirm to run the sub tree',
        content: 'The node is a data node, do you want to run the sub tree?',
        centered: true,
        okText: 'Compute',
        okType: 'primary',
        cancelText: 'No',
      });
      if (!confirmed) {
        message.info('cancel the task');
        return;
      }
      await requestDispatchTask(analysisId, nodeSufIdList, edgeSufIdList);
      return;
    } else if (
      node.type === NodeType.COMPUTATION_NODE ||
      node.type === NodeType.COMPUTATION_NODE_V2
    ) {
      try {
        const result = flowTool.checkPreComputable(nodeId);
        const { isTaskRunning, nodeList } = result;
        const existsPreviousUncomputedNodes = nodeList.length > 0;
        const promptText = existsPreviousUncomputedNodes
          ? 'Prior uncomputed nodes will be computed first'
          : 'Continue to launch the task';
        const confirmed = await promiseConfirm({
          title: 'Do you want to run the nodes?',
          content: promptText,
          okText: 'Compute',
          okType: 'primary',
          cancelText: 'No',
        });
        if (!confirmed) {
          message.info('cancel the task');
          return;
        }
        if (existsPreviousUncomputedNodes) {
          const { nodeIdList: nodePreIdList, edgeIdList: edgePreIdList } =
            flowTool.getIdList(result);
          nodeSufIdList.push(...nodePreIdList);
          edgeSufIdList.push(...edgePreIdList);
        }
        if (!isTaskRunning) {
          const dispatchResult = await requestDispatchTask(
            analysisId,
            nodeSufIdList,
            edgeSufIdList,
          );
          if (dispatchResult.code === 200) {
            message.success('The task has been dispatched');
          } else {
            throw new Error(dispatchResult.message);
          }
        } else {
          const extendResult = await requestExtendTask(nodeSufIdList, edgeSufIdList);
          if (extendResult.code === 200) {
            message.success('The task has been extended');
          } else {
            throw new Error(extendResult.message);
          }
        }
      } catch (e: any) {
        message.error(e.message);
      }
    }
  };

  const findNodeSource = (instance, nodeId) => {
    const flowTool = new FlowTool(instance);
    const result = flowTool.checkNodeSource(nodeId);
    return result;
  };

  const runNode = async (nodeId: string, instance: any) => {
    const [analysisId] = getLocationParams(['analysis-id']);
    const flowTool = new FlowTool(instance);
    try {
      const result = flowTool.checkPreComputable(nodeId);
      const { isTaskRunning } = result;
      const { nodeIdList, edgeIdList } = flowTool.getIdList(result);
      const existsPreviousUncomputedNodes = nodeIdList.length > 0;
      nodeIdList.push(nodeId);

      const promptText = existsPreviousUncomputedNodes
        ? 'Prior uncomputed nodes will be computed first'
        : 'Continue to launch the task';
      const confirmed = await promiseConfirm({
        title: 'Confirm to run the single node',
        content: promptText,
        okText: 'Compute',
        okType: 'primary',
        cancelText: 'No',
        centered: true,
      });
      if (!confirmed) {
        message.info('cancel the task');
        return;
      }

      if (!isTaskRunning) {
        // No upstream task is running
        // Call the task dispatch API
        const dispatchResult = await requestDispatchTask(analysisId, nodeIdList, edgeIdList);
        if (dispatchResult.code === 200) {
          message.success('The task has been dispatched');
        } else {
          throw new Error(dispatchResult.message);
        }
      } else {
        // An upstream task is running
        // Call the task extension API
        // const dispatchResult = await xxx(analysisId, nodeIdList, edgeIdList)
        const extendResult = await requestExtendTask(nodeIdList, edgeIdList);
        if (extendResult.code === 200) {
          message.success('The task has been extended');
        } else {
          throw new Error(extendResult.message);
        }
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const findSubCompleteNode = (nodeId: string, instance: any) => {
    const flowTool = new FlowTool(instance);
    const resultSub = flowTool.findComputableSubtree(nodeId);
    const nodeList = resultSub.nodeList;
    return nodeList;
  };

  const findSubCompleteNodeId = (nodeId: string, instance: any) => {
    const flowTool = new FlowTool(instance);
    const resultSub = flowTool.findComputableSubtree(nodeId);
    const nodeList = resultSub.nodeList;
    const finishedNodeIdList = nodeList
      .filter((item) => item.data.state === NodeState.FINISHED)
      .map((item) => item.id);
    return finishedNodeIdList;
  };

  const copyNode = async (id: string) => {
    const copyResult = await requestCopyNode(id);
    const { data: newNodeEntity } = copyResult;

    const newX: number = newNodeEntity.x + 50;
    const newY: number = newNodeEntity.y + 50;

    const position = {
      x: newX,
      y: newY,
    };

    const [{ data: result }, { data: privateResult }] = await Promise.all([
      requestPublicFBGroupList(),
      requestPrivateFBGroupList(),
    ]);

    const fbListMap = new Map();
    for (const i of result) {
      i.functionBlockList.map((item) => {
        return fbListMap.set(item.id, item.name);
      });
    }
    for (const i of privateResult) {
      i.functionBlockList.map((item) => {
        return fbListMap.set(item.id, item.name);
      });
    }

    const newNode = {
      id: `${newNodeEntity.id}`,
      type: newNodeEntity.type,
      position: position,
      width: 260,
      height: 150,
      data: {
        label: newNodeEntity.name,
        tag: newNodeEntity.tag,
        remove: deleteNode,
        locked: newNodeEntity.locked || newNodeEntity.dynamic_generation_locked,
        state: newNodeEntity.state,
        changeNodeState: changeNodeState,
        dataId: newNodeEntity.dataId,
        fbId: newNodeEntity.functionBlockId,
        fbName: fbListMap.get(newNodeEntity.functionBlockId),
        computationResourceConfigure: newNodeEntity.computationResourceConfigure,
        findNodeSource,
        annotated: newNodeEntity.annotated,
        avgDuration: newNodeEntity.avgDuration,
        dynamicGenerationId: newNodeEntity.dynamicGenerationId,
        reportUuid: newNodeEntity.reportUuid,
      },
    };
    setNodes((nds) => nds.concat([newNode]));

    return newNode.id;
  };

  const createNode = (newNodeEntity: any) => {
    const newNode = {
      id: `${newNodeEntity.id}`,
      type: newNodeEntity.type,
      position: { x: newNodeEntity.x, y: newNodeEntity.y },
      width: 260,
      height: 150,
      data: {
        label: newNodeEntity.name,
        tag: newNodeEntity.tag,
        remove: deleteNode,
        locked:
          newNodeEntity.locked ||
          newNodeEntity.dynamicGenerationLocked ||
          newNodeEntity.visualizerLocked,
        state: newNodeEntity.state,
        changeNodeState: changeNodeState,
        dataId: newNodeEntity.dataId,
        fbId: newNodeEntity.functionBlockId,
        fbVersionId: newNodeEntity.functionBlockVersionId,
        fbName: newNodeEntity.functionBlockName,
        plotOnly: !!newNodeEntity.functionBlockVersionPlotOnly,
        computationResourceConfigure: newNodeEntity.computationResourceConfigure,
        systemEnv: newNodeEntity.systemEnv,
        findNodeSource,
        annotated: newNodeEntity.annotated,
        avgDuration: newNodeEntity.avgDuration,
        dynamicGenerationId: newNodeEntity.dynamicGenerationId,
        reportUuid: newNodeEntity.reportUuid,
        isReviewError: newNodeEntity.isReviewError || false,
        type: newNodeEntity.type,
      },
    };
    return newNode;
  };

  const createNodeAndEdge = async (
    newNodeEntity: any,
    nodeId: any,
    analysisId: any,
    formParameters: any = [] || null,
  ) => {
    const newNode = createNode(newNodeEntity);
    const { data: edgeEntity } = await requestCreateEdge(nodeId, newNodeEntity.id, analysisId);

    const params = {
      id: edgeEntity.id.toString(),
      animated: true,
      source: nodeId,
      target: newNodeEntity.id.toString(),
    };
    setNodes((els: any[]) => els.concat(newNode));
    setEdges((els: any[]) => els.concat(params));
    if (Object.keys(formParameters).length > 0) {
      await requestEditNodeParams(newNodeEntity.id.toString(), formParameters);
      runNode(newNodeEntity.id.toString(), instance);
    }
  };

  const loadNodes = async () => {
    try {
      const [{ data: nodeList = [] }, { data: previteStateDict = {} }] = await Promise.all([
        requestNodeListOfAnalysis(analysisId),
        requestNodePreviteStateDict(analysisId),
      ]);
      if (!Array.isArray(nodeList)) {
        console.error('Invalid nodeList data format');
        return;
      }

      let visibleNodeList;
      if (analysisDetail?.errorNodeHidden) {
        visibleNodeList = nodeList.filter((node) => node.state !== NodeState.FAILED);
      } else {
        visibleNodeList = nodeList;
      }

      // Sort by node position; when nodes overlap, the downstream node is on top
      const compareNodesLocation = (a, b) => {
        if (a.x !== b.x) {
          return a.x - b.x;
        }
        return a.y - b.y;
      };

      visibleNodeList.sort(compareNodesLocation);

      const newNodes = visibleNodeList.map((node: any) => {
        return createNode(node);
      });
      setNodes(() => newNodes);
      const statistic = {
        total: visibleNodeList.length,
        running: 0,
        failed: 0,
        success: 0,
        pending: 0,
        debugging: 0,
      } as NodeStatistic;
      const errorList: any[] = [];
      for (const node of visibleNodeList) {
        if (node.state === NodeState.FAILED) {
          errorList.push(node);
          statistic.failed++;
        } else if (node.state === NodeState.RUNNING) {
          statistic.running++;
        } else if (node.state === NodeState.FINISHED) {
          statistic.success++;
        } else if (node.state === NodeState.PENDING) {
          statistic.pending++;
        } else if (node.state === NodeState.DEBUGGING) {
          statistic.debugging++;
        }
      }
      setNodeStatistic(statistic);
      setNodeList(visibleNodeList);
      setErrorNodeList(errorList);
      if (typeof previteStateDict === 'object' && previteStateDict !== null) {
        setPreviteStateDict(previteStateDict);
      } else {
        console.error('Invalid previteStateDict data format');
      }
    } catch (error) {
      console.error('Error loading nodes:', error);
    }
  };

  const loadEdges = async () => {
    const { data: edgeList } = await requestEdgeListOfAnalysis(analysisId);
    const newEdges = edgeList.map((edge: any) => {
      return {
        id: String(edge.id),
        source: String(edge.sourceNodeId),
        target: String(edge.targetNodeId),
        animated: true,
      };
    });
    setEdges(() => newEdges);
    setEdgeList(edgeList);
  };

  const loadImportedDataSourceList = async () => {
    try {
      const { data: dataSourceList } = await requestDataSourceList(
        DataListFetchMode.IMPORTED,
        analysisId,
        null,
      );
      setImportedDataSourceList(dataSourceList);
    } catch (error) {
      console.error('Error loading data source list:', error);
    }
  };

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (analysisId) {
      loadImportedDataSourceList();
      intervalId = setInterval(() => {
        loadImportedDataSourceList();
      }, pollInterval);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [analysisId, pollInterval]);

  const onConnect = async (params: any) => {
    const nodeAdobePagemaker = new AdobePagemaker(instance);
    const { source, target } = params;
    const resultSub = nodeAdobePagemaker.findNextComputable(target);
    if (autoState) {
      if (instance && source) {
        try {
          const { data: edgeEntity } = await requestCreateEdge(source, target, analysisId);
          if (resultSub.length == 0) {
            const sourcePosition = nodeAdobePagemaker.getNodePosition(source);
            const targetPosition = nodeAdobePagemaker.getNodePosition(target);
            await nodeAdobePagemaker.moveLocationOnConnectSingleNode(
              source,
              target,
              sourcePosition,
              targetPosition,
              updateNodePosition,
            );
          }
          if (resultSub.length > 0) {
            await nodeAdobePagemaker.moveLocationOnConnectMultipleNode(
              source,
              target,
              updateNodePosition,
            );
          }
          params.id = `${edgeEntity.id}`;
          params.deletable = true;
          params.animated = true;
          // setNodes((els: any[]) => els.concat(newNode));
          setEdges((els) => addEdge(params, els));
        } catch (e: any) {
          console.log(e.message);
        }
      }
    } else {
      const { data: edgeEntity } = await requestCreateEdge(source, target, analysisId);
      params.id = `${edgeEntity.id}`;
      params.deletable = true;
      params.animated = true;
      // setNodes((els: any[]) => els.concat(newNode));
      setEdges((els) => addEdge(params, els));
    }
  };

  const updatePositionByAutoAdd = async (currentNode, nodeid, currentNodePosition, position) => {
    const nodeAdobePagemaker = new AdobePagemaker(instance);
    const coordinate = await nodeAdobePagemaker.moveLocationOnConnectSingleNode(
      currentNode,
      nodeid,
      currentNodePosition,
      position,
      updateNodePosition,
    );
    return coordinate;
  };

  const updatePositionListByAutoAdd = async (
    currentNode,
    nodeid,
    currentNodePosition,
    position,
    findNextComputableList,
    findNextComputableNodePositionList,
  ) => {
    const nodeAdobePagemaker = new AdobePagemaker(instance);
    const coordinate = await nodeAdobePagemaker.moveLocationOnVisualpanel(
      currentNode,
      nodeid,
      currentNodePosition,
      position,
      findNextComputableList,
      findNextComputableNodePositionList,
      updateNodePosition,
    );
    return coordinate;
  };

  const openEditParamterModal = (nodeId: string, fbId: string) => {
    setParamEditedNodeId(nodeId);
    setParamEditedFbId(fbId);
  };

  const closeEditParameterModal = () => {
    setParamEditedNodeId(null);
    setParamEditedFbId(null);
  };

  useEffect(() => {
    if (instance && analysisId) {
      analysisMonitor.setAnalysisId(analysisId);
      analysisMonitor.start({
        analysisId: analysisId,
        setAnalysisUpdatedTime,
      });
    } else {
      analysisMonitor.pause();
    }
  }, [instance, analysisId]);

  useEffect(() => {
    if (analysisId && instance) {
      loadNodes();
      loadEdges();
      loadImportedDataSourceList();
    } else {
      setNodes([]);
      setEdges([]);
    }
  }, [analysisId, instance, analysisUpdatedTime]);

  useEffect(() => {
    if (!instance) return;
    globalLayout();
  }, [analysisDetail?.figureVisible, compactMode]);

  return {
    analysisId,
    setAnalysisId,

    analysisDetail,
    setAnalysisDetail,

    analysisAccessType,
    setAnalysisAccessType,

    updateAnalysisInfo,

    analysisUpdatedTime,

    instance,
    setInstance,

    panelMode,
    setPanelMode,

    shiftKey,
    setShiftKey,

    positionDif,
    setPositionDif,
    isClickBlank,
    setIsClickBlank,

    nodeBorder,
    setNodeBorder,

    isFbClick,
    setIsFbClick,

    currentSelectedNodes,
    setCurrentSelectedNodes,
    temporaryCenteredNodeId,
    setTemporaryCenteredNodeId,

    nodes,
    setNodes,
    // onNodesChange,
    edges,
    setEdges,

    fixedNodeId,
    setFixedNodeId,

    importedDataSourceList,

    autoState,
    setAutoState,
    compactMode,
    setCompactMode,

    deleteNode,
    deleteNodeBatch,
    copyNode,
    runSubTree,
    runNode,
    findSubCompleteNode,
    findSubCompleteNodeId,
    createNode,
    onConnect,

    createNodeAndEdge,

    nodeList,
    setNodeList,
    edgeList,
    setEdgeList,
    errorNodeList,
    setErrorNodeList,

    nodeStatistic,
    setNodeStatistic,

    globalLayout,

    // handleTransform,
    updateNodePosition,
    updatePositionByAutoAdd,
    updatePositionListByAutoAdd,

    openRenameNode,
    renamedNodeId,
    renameNode,
    renamedNodeForm,
    closeRenameNode,

    computationResourceChangingNodeId,
    setComputationResourceChangingNodeId,

    computationResourceChangingInfo,
    setComputationResourceChangingInfo,
    isViewOnlyMode,
    setIsViewOnlyMode,

    openRetagNode,
    retagNodeId,
    retagNode,
    retagNodeForm,
    closeRetagNode,

    previteStateDict,
    setPreviteStateDict,

    calcuLogInspectedNodeId,
    setCalcuLogInspectedNodeId,

    jobInfoInspectedNodeId,
    setJobInfoInspectedNodeId,

    jobDetailsInspectedNodeId,
    setJobDetailsInspectedNodeId,

    autoGenieInspectedNodeId,
    setAutoGenieInspectedNodeId,
    bugFixerInspectedNodeId,
    setBugFixerInspectedNodeId,
    agentHistoryInspectedNodeId,
    setAgentHistoryInspectedNodeId,
    beautifierInspectedNodeId,
    setBeautifierInspectedNodeId,

    selectedBlocks,
    setSelectedBlocks,
    isSelectFbModalOpen,
    setIsSelectFbModalOpen,

    dataCollectedNodeId,
    setDataCollectedNodeId,

    outputsListInspectedNodeId,
    setOutputsListInspectedNodeId,

    bugFixerHistoryInspectedNodeId,
    setBugFixerHistoryInspectedNodeId,

    autoGenieContextInspectedNodeId,
    setAutoGenieContextInspectedNodeId,

    showError,
    setShowError,
    activeErrorKey,
    setActiveErrorKey,
    changeNode,
    setChangeNode,

    paramEditedFbId,
    paramEditedNodeId,

    openEditParamterModal,
    closeEditParameterModal,

    isCloseBtnClicked,
    setIsCloseBtnClicked,
  };
};

export default useAnalysis;
