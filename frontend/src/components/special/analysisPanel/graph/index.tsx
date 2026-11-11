import { AnalysisType } from '@/constants/analysis';
import { NodeState, NodeType } from '@/constants/node';
import { requestLatestComputation, requestRunBugFixer } from '@/request/computation';
import { requestCreateEdge, requestDeleteEdge } from '@/request/edge';
import {
  requestCreateNode,
  requestDeleteNodeList,
  requestNodeInfo,
  requestUpdateNodePosition,
  requestUpdateNodePositionList,
} from '@/request/node';
import { requestSubmitReport } from '@/request/report';
import { FlowTool } from '@/util/flowTool';
import { getLocationParams } from '@/util/getUrl';
import { tempStorage } from '@/util/tempStorage';
import {
  CopyOutlined,
  DeleteOutlined,
  ExclamationCircleFilled,
  GroupOutlined,
  LeftOutlined,
  QuestionCircleOutlined,
  RightOutlined,
  StarOutlined,
} from '@ant-design/icons';
import {
  AutoComplete,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Popconfirm,
  Popover,
  Spin,
} from 'antd';
import React, { memo, useRef, useState } from 'react';
import ReactFlow, { Background, BackgroundVariant, Panel, useReactFlow } from 'reactflow';
import 'reactflow/dist/style.css';
import { useModel } from 'umi';
import ComputationNodeV2 from './computationNodeV2';
import CreatePipLine from './createPipeline';
import CustomEdge from './customEdge';
import DataSourceNode from './dataSourceNode';
import DataSourceNodeV2 from './dataSourceNodeV2';
import FunctionBlockNode from './functionBlockNode';
import styles from './overview.less';
import ReportNode from './reportNode';
import NotebookNode from './notebookNode';
import ClaudeCodeNode from './claudeCodeNode';
const { confirm } = Modal;

const { TextArea } = Input;

const nodeTypes2NodeComponentMap = {
  [NodeType.COMPUTATION_NODE]: memo(FunctionBlockNode),
  [NodeType.DATA_NODE]: memo(DataSourceNode),
  [NodeType.REPORT_NODE]: memo(ReportNode),
  [NodeType.COMPUTATION_NODE_V2]: memo(ComputationNodeV2),
  [NodeType.NOTEBOOK_NODE]: memo(NotebookNode),
  [NodeType.DATA_NODE_V2]: memo(DataSourceNodeV2),
  [NodeType.CLAUDE_CODE_NODE]: memo(ClaudeCodeNode),
};

export default function Graph() {
  const {
    analysisId,
    analysisAccessType,
    instance,
    setInstance,
    currentSelectedNodes,
    setCurrentSelectedNodes,
    setTemporaryCenteredNodeId,
    nodes,
    setNodes,
    edges,
    setEdges,
    copyNode,
    createNode,
    shiftKey,
    onConnect,
    updateNodePosition,
    fixedNodeId,
    setFixedNodeId,
  } = useModel('analysis');
  const { changeNode, setChangeNode } = useModel('analysis');
  const { setActiveErrorKey } = useModel('analysis');
  const { setSelectedNodeId } = useModel('aiUI');
  const { openModal } = useModel('workflowHelper');
  const { initVisualPanel, setDataId, setNodeInfo, setTargetGenerationId } =
    useModel('visualPanelControl');

  const graphWrapper = useRef<HTMLInputElement>(null!);
  const [createPipelineShow, setCreatePipelineShow] = useState(false);
  const edgeUpdateSuccessful = useRef(true);
  const [reportedNodeId, setReportedNodeId] = useState(null);
  const [isReporting, setIsReporting] = useState(false);
  const [reportForm] = Form.useForm();
  const [isUpperLeftToolbarExpanded, setIsUpperLeftToolbarExpanded] = useState(true);
  // const { isAiRepoGenSelected, setIsAiRepoGenSelected, setReportSelectedNodeIds } =
  //   useModel('visualPanelControl');
  const [autoCompleteOptions, setAutoCompleteOptions] = useState<any[]>([]);
  const [autoCompleteValue, setAutoCompleteValue] = useState('');

  const [bugFixerPrompt, setBugFixerPrompt] = useState('');
  const { setCenter } = useReactFlow();

  const { isGuest, userInfo } = useModel('user');
  const isGuestUser = isGuest();

  const handleError = (error: any, customMessage: string) => {
    console.error(error);
    message.error(customMessage || 'An error occurred');
  };

  // const handleAiReportGeneratorClick = () => {
  //   if (!analysisId) {
  //     message.error('Please select a pipeline first!');
  //     return;
  //   }
  //   if (isAiRepoGenSelected) {
  //     setIsAiRepoGenSelected(false);
  //     setReportSelectedNodeIds([]);
  //   } else {
  //     setIsAiRepoGenSelected(true);
  //     setReportSelectedNodeIds([]);
  //   }
  // };
  const autoFocus = async (nodeId: string, instance) => {
    if (!nodeId || !instance) {
      console.error('Invalid nodeId or instance');
      return;
    }
    const nodeData = await requestNodeInfo(nodeId);
    instance.setCenter(nodeData.x + 130, nodeData.y + 75, {
      duration: 500,
      zoom: 1,
    });
  };

  const onInit = (reactFlowInstance: any) => {
    try {
      reactFlowInstance.setCenter(0, 0, { zoom: 1 });
      setInstance(reactFlowInstance);
      const [nodeId] = getLocationParams(['nodeId']);
      if (nodeId) {
        autoFocus(nodeId, reactFlowInstance);
      }
    } catch (error) {
      handleError(error, 'Failed to initialize flow');
    }
  };

  // we are using a bit of a shortcut here to adjust the edge type
  // this could also be done with a custom edge for example
  const onDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    try {
      event.preventDefault();
      const reactFlowBounds = graphWrapper.current?.getBoundingClientRect();

      // Get the node type
      const type = event.dataTransfer.getData('node-type');
      const label = event.dataTransfer.getData('label');
      const fbId = event.dataTransfer.getData('fb-id');
      const dataId = event.dataTransfer.getData('data-id');
      const fbName = event.dataTransfer.getData('fb-name');

      // Use project to convert pixel coordinates into the internal ReactFlow coordinate system
      const position = instance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });
      let newX: number = 0;
      let newY: number = 0;
      if (position.x > 0) {
        if (Math.abs(position.x) % 100 > 50 || Math.abs(position.x) % 100 === 50) {
          newX = position.x + 100 - (Math.abs(position.x) % 100);
        } else if (Math.abs(position.x) % 100 < 50) {
          newX = position.x - (Math.abs(position.x) % 100);
        }
      } else if (position.x < 0) {
        if (Math.abs(position.x) % 100 > 50 || Math.abs(position.x) % 100 === 50) {
          newX = position.x - 100 + (Math.abs(position.x) % 100);
        } else if (Math.abs(position.x) % 100 < 50) {
          newX = position.x + (Math.abs(position.x) % 100);
        }
      }
      if (position.y > 0) {
        if (Math.abs(position.y) % 100 > 50 || Math.abs(position.y) % 100 === 50) {
          newY = position.y + 100 - (Math.abs(position.y) % 100);
        } else if (Math.abs(position.y) % 100 < 50) {
          newY = position.y - (Math.abs(position.y) % 100);
        }
      } else if (position.y < 0) {
        if (Math.abs(position.y) % 100 > 50 || Math.abs(position.y) % 100 === 50) {
          newY = position.y - 100 + (Math.abs(position.y) % 100);
        } else if (Math.abs(position.y) % 100 < 50) {
          newY = position.y + (Math.abs(position.y) % 100);
        }
      }

      const newPosition = {
        x: Math.round(newX),
        y: Math.round(newY),
      };

      // Create the new node here; continue if creation succeeds, otherwise report an error and stop

      const creationResult = await requestCreateNode(
        type,
        newPosition.x,
        newPosition.y,
        analysisId,
        dataId,
        fbId,
        label,
      );
      const { data: newNodeEntity } = creationResult;
      newNodeEntity.functionBlockName = fbName;
      const newNode = createNode(newNodeEntity);

      setNodes((els: any[]) => els.concat(newNode));
    } catch (error) {
      handleError(error, 'Failed to create new node');
    }
  };

  const onNodeDrag = (event, node) => {
    try {
      if (!node || typeof node.id === 'undefined') {
        return;
      }
      const positionX = node.position.x;
      const positionY = node.position.y;
      let newX: number = 0;
      let newY: number = 0;
      if (positionX > 0) {
        if (Math.abs(positionX) % 100 > 50 || Math.abs(positionX) % 100 === 50) {
          newX = positionX + 100 - (Math.abs(positionX) % 100);
        } else if (Math.abs(positionX) % 100 < 50) {
          newX = positionX - (Math.abs(positionX) % 100);
        }
      } else if (positionX < 0) {
        if (Math.abs(positionX) % 100 > 50 || Math.abs(positionX) % 100 === 50) {
          newX = positionX - 100 + (Math.abs(positionX) % 100);
        } else if (Math.abs(positionX) % 100 < 50) {
          newX = positionX + (Math.abs(positionX) % 100);
        }
      }
      if (positionY > 0) {
        if (Math.abs(positionY) % 100 > 50 || Math.abs(positionY) % 100 === 50) {
          newY = positionY + 100 - (Math.abs(positionY) % 100);
        } else if (Math.abs(positionY) % 100 < 50) {
          newY = positionY - (Math.abs(positionY) % 100);
        }
      } else if (positionY < 0) {
        if (Math.abs(positionY) % 100 > 50 || Math.abs(positionY) % 100 === 50) {
          newY = positionY - 100 + (Math.abs(positionY) % 100);
        } else if (Math.abs(positionY) % 100 < 50) {
          newY = positionY + (Math.abs(positionY) % 100);
        }
      }

      setNodes((nds) =>
        nds.map((item) => {
          if (item.id === node.id) {
            item.position = { x: Math.round(newX), y: Math.round(newY) };
          }
          return item;
        }),
      );
    } catch (error) {
      handleError(error, 'Failed to drag node');
    }
  };

  // const onNodeDrag = (event, node) => {
  //   const positionX = node.position.x;
  //   const positionY = node.position.y;

  //   setNodes((nds) =>
  //     nds.map((item) => {
  //       if (item.id === node.id) {
  //         item.position = { x: positionX, y: positionY };
  //       }
  //       return item;
  //     }),
  //   );
  // };

  const onNodeDragStart = (
    event: React.MouseEvent,
    node: any,
    // nodes: Node[]
  ) => {
    tempStorage.set('previous node position', node?.position);
  };

  const onNodeDragStop = async (event: React.MouseEvent, node: any) => {
    try {
      if (!node || typeof node.id === 'undefined') {
        return;
      }
      const previousPosition = tempStorage.get('previous node position');
      if (analysisAccessType === AnalysisType.PUBLIC && userInfo?.id + '' !== '0') {
        setNodes((nds) =>
          nds.map((item) => {
            if (item.id === node.id) {
              if (item.position !== previousPosition) {
                item.position = previousPosition;
                message.error('You are not allowed to move node in public analysis.');
              }
            }
            return item;
          }),
        );
        return;
      }

      const positionX = node.position.x;
      const positionY = node.position.y;
      let newX: number = 0;
      let newY: number = 0;
      if (positionX > 0) {
        if (Math.abs(positionX) % 100 > 50 || Math.abs(positionX) % 100 === 50) {
          newX = positionX + 100 - (Math.abs(positionX) % 100);
        } else if (Math.abs(positionX) % 100 < 50) {
          newX = positionX - (Math.abs(positionX) % 100);
        }
      } else if (positionX < 0) {
        if (Math.abs(positionX) % 100 > 50 || Math.abs(positionX) % 100 === 50) {
          newX = positionX - 100 + (Math.abs(positionX) % 100);
        } else if (Math.abs(positionX) % 100 < 50) {
          newX = positionX + (Math.abs(positionX) % 100);
        }
      }
      if (positionY > 0) {
        if (Math.abs(positionY) % 100 > 50 || Math.abs(positionY) % 100 === 50) {
          newY = positionY + 100 - (Math.abs(positionY) % 100);
        } else if (Math.abs(positionY) % 100 < 50) {
          newY = positionY - (Math.abs(positionY) % 100);
        }
      } else if (positionY < 0) {
        if (Math.abs(positionY) % 100 > 50 || Math.abs(positionY) % 100 === 50) {
          newY = positionY - 100 + (Math.abs(positionY) % 100);
        } else if (Math.abs(positionY) % 100 < 50) {
          newY = positionY + (Math.abs(positionY) % 100);
        }
      }
      const newPosition: any = {
        x: Math.round(newX),
        y: Math.round(newY),
      };

      if (previousPosition.x === newPosition.x && previousPosition.y === newPosition.y) {
        return;
      }
      await requestUpdateNodePosition(node.id, newPosition.x, newPosition.y);
    } catch (error) {
      handleError(error, 'Failed to update node position');
      // Restore previous position on error
      setNodes((nds) =>
        nds.map((item) => {
          if (item.id === node.id) {
            item.position = tempStorage.get('previous node position');
          }
          return item;
        }),
      );
    }
    // No need to continue on success
  };

  const onEdgeUpdateStart = () => {
    edgeUpdateSuccessful.current = false;
  };

  const onEdgeUpdate = () => {
    edgeUpdateSuccessful.current = true;
    // setEdges((els) => updateEdge(oldEdge, newConnection, els));
  };

  const onEdgeUpdateEnd = async (_: any, edge: any) => {
    if (!edgeUpdateSuccessful.current && analysisAccessType !== AnalysisType.PUBLIC) {
      const targetNode = nodes.find((node) => node.id === edge.target);
      const isReportNodeTarget = targetNode?.type === NodeType.REPORT_NODE;

      if (isReportNodeTarget) {
        edgeUpdateSuccessful.current = true;
        return;
      }

      confirm({
        title: 'Are you sure delete this edge?',
        icon: <ExclamationCircleFilled />,
        // content: 'Some descriptions',
        okText: 'Yes',
        okType: 'danger',
        cancelText: 'No',
        async onOk() {
          if (!edgeUpdateSuccessful.current) {
            await requestDeleteEdge(edge.id);
            setEdges((eds) => eds.filter((e) => e.id !== edge.id));
          }
          edgeUpdateSuccessful.current = true;
        },
        onCancel() {
          edgeUpdateSuccessful.current = true;
        },
      });
    } else if (analysisAccessType === AnalysisType.PUBLIC && userInfo?.id + '' !== '0') {
      message.error('You are not allowed to delete edge in public analysis.');
    }
  };

  const onNodeClick = async (_: React.MouseEvent, node: any) => {
    setNodeInfo({
      type: node.type,
      tag: node.data.tag,
      state: node.data.state,
      fbId: node.data.fbId,
    });
    const { data } = node;
    setChangeNode(!changeNode);

    if (data.dynamicGenerationId) {
      setTargetGenerationId(data.dynamicGenerationId);
    } else {
      setTargetGenerationId(null);
    }

    if (shiftKey) {
      return;
    } else {
      if (node.type in [NodeType.DATA_NODE_V2, NodeType.COMPUTATION_NODE_V2]) {
        return;
      }

      if (node.type === NodeType.DATA_NODE) {
        setDataId(data.dataId);
        return;
      }

      if (node.type === NodeType.REPORT_NODE) {
        if (data.reportData) {
          initVisualPanel(data.reportData, node.id, false);
        }
        return;
      }

      if (node.data.state === NodeState.FAILED) {
        setActiveErrorKey(node.id);
      } else {
        setActiveErrorKey(null);
      }
      if (node.data.state !== NodeState.FINISHED) {
        initVisualPanel(null, node.id, data.plotOnly);
        return;
      }

      const { data: latestComputation } = await requestLatestComputation(node.id);
      if (!latestComputation) {
        message.error('No latest computation found');
        initVisualPanel(null, node.id, data.plotOnly);
        return;
      }
      initVisualPanel(latestComputation.resultDataId, node.id, data.plotOnly);
    }
  };

  const onDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  };

  const collectGroup = () => {
    // setPanelMode(FlowMode.COMPUTATION_FLOW);
  };

  const collectPipelineNode = () => {
    setCreatePipelineShow(true);
  };

  const copyPipeline = async () => {
    try {
      const flowTool = new FlowTool(instance);
      const nodeIdList = currentSelectedNodes.map((node) => node.id);
      const collectEdgeDict = flowTool.checkNodeConnectEdge(nodeIdList);
      const nodeMap = new Map();
      for (let i = 0; i < nodeIdList.length; i++) {
        const newNodeId = await copyNode(nodeIdList[i]);

        nodeMap.set(nodeIdList[i], newNodeId);
      }
      collectEdgeDict.forEach(async (item) => {
        const { data: edgeEntity } = await requestCreateEdge(
          nodeMap.get(item.source),
          nodeMap.get(item.target),
          analysisId,
        );
        const params = {
          id: edgeEntity.id.toString(),
          animated: true,
          source: nodeMap.get(item.source),
          target: nodeMap.get(item.target),
        };
        setEdges((els: any[]) => els.concat(params));
      });
    } catch (error) {
      handleError(error, 'Failed to copy pipeline');
    }
  };

  const removePipeline = async () => {
    try {
      const nodeIdList = currentSelectedNodes.map((node) => node.id);
      await requestDeleteNodeList(nodeIdList);
      nodeIdList.forEach((item) => {
        setNodes((nds) => nds.filter((node) => node.id !== item.id));
      });
      setCurrentSelectedNodes([]);
    } catch (error) {
      handleError(error, 'Failed to remove pipeline');
    }
  };

  const getNodeExtents = (nodes: any[]) => {
    if (nodes.length === 0) return { left: 0, top: 0, right: 0, bottom: 0 };

    let leftMostX = nodes[0].position.x;
    let rightMostX = nodes[0].position.x;
    let topMostY = nodes[0].position.y;
    let bottomMostY = nodes[0].position.y;

    nodes.forEach((node) => {
      if (node.position.x < leftMostX) {
        leftMostX = node.position.x;
      }
      if (node.position.x > rightMostX) {
        rightMostX = node.position.x;
      }
      if (node.position.y < topMostY) {
        topMostY = node.position.y;
      }
      if (node.position.y > bottomMostY) {
        bottomMostY = node.position.y;
      }
    });

    return { left: leftMostX, top: topMostY, right: rightMostX, bottom: bottomMostY };
  };

  const extents = getNodeExtents(nodes);

  const onSelectionDragStop = async (event, nodes) => {
    try {
      if (nodes.length > 0) {
        const nodeList: any = nodes.map((node) => {
          const positionX = node.position.x;
          const positionY = node.position.y;
          let newX: number = 0;
          let newY: number = 0;
          if (positionX > 0) {
            if (Math.abs(positionX) % 100 > 50 || Math.abs(positionX) % 100 === 50) {
              newX = positionX + 100 - (Math.abs(positionX) % 100);
            } else if (Math.abs(positionX) % 100 < 50) {
              newX = positionX - (Math.abs(positionX) % 100);
            }
          } else if (positionX < 0) {
            if (Math.abs(positionX) % 100 > 50 || Math.abs(positionX) % 100 === 50) {
              newX = positionX - 100 + (Math.abs(positionX) % 100);
            } else if (Math.abs(positionX) % 100 < 50) {
              newX = positionX + (Math.abs(positionX) % 100);
            }
          }
          if (positionY > 0) {
            if (Math.abs(positionY) % 100 > 50 || Math.abs(positionY) % 100 === 50) {
              newY = positionY + 100 - (Math.abs(positionY) % 100);
            } else if (Math.abs(positionY) % 100 < 50) {
              newY = positionY - (Math.abs(positionY) % 100);
            }
          } else if (positionY < 0) {
            if (Math.abs(positionY) % 100 > 50 || Math.abs(positionY) % 100 === 50) {
              newY = positionY - 100 + (Math.abs(positionY) % 100);
            } else if (Math.abs(positionY) % 100 < 50) {
              newY = positionY + (Math.abs(positionY) % 100);
            }
          }
          return {
            node_id: node.id,
            x: Math.round(newX),
            y: Math.round(newY),
          };
        });
        updateNodePosition(nodeList);
        await requestUpdateNodePositionList(nodeList);
      }
    } catch {
      message.warning('Failed to move nodes in bulk');
    }
  };

  const onPaneClick = () => {
    setSelectedNodeId(null);
  };
  const proOptions = { hideAttribution: false };

  const onReportConfirm = () => {
    reportForm.submit();
  };

  const onReportSubmit = async (values) => {
    try {
      setIsReporting(true);
      const { nodeId, summary, description } = values;
      await requestSubmitReport(nodeId, summary, description);
      setReportedNodeId(null);
      reportForm.resetFields();
      message.success('Report successfully.');
    } catch (e) {
      message.error('Report failed.');
    } finally {
      setIsReporting(false);
    }
  };

  const onCancelReport = () => {
    setReportedNodeId(null);
    // setIsReportSubmitting(false);
    reportForm.resetFields();
  };

  const onSelect = (value) => {
    const selectedNode = autoCompleteOptions.find((option) => option.value === value);
    if (selectedNode) {
      const selectedNodePosition = selectedNode.fb_position;

      if (setTemporaryCenteredNodeId) {
        setTemporaryCenteredNodeId(value.toString());

        setTimeout(() => {
          setTemporaryCenteredNodeId(null);
        }, 800);
      }

      setCenter(selectedNodePosition.x + 130, selectedNodePosition.y + 75, {
        duration: 0,
        zoom: 1,
      });
      setAutoCompleteOptions([]);
      setAutoCompleteValue(selectedNode.label);
    } else {
      console.error('Selected node not found');
    }
  };

  const onSearch = (value) => {
    setAutoCompleteValue(value);

    // Filter nodes based on the input value
    const filteredOptions = nodes
      .filter((node) => node.data.label.toLowerCase().includes(value.toLowerCase()))
      .map((node) => ({
        value: node.id,
        label: node.data.label,
        fb_position: node.position,
      }));

    setAutoCompleteOptions(filteredOptions);
  };

  const onClear = () => {
    setAutoCompleteOptions([]);
    setAutoCompleteValue('');
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }} ref={graphWrapper}>
      <div
        id="analysis-flow"
        style={{
          width: '100%',
          height: '100%',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: '10px',
            left: '10px',
            zIndex: 1,
            backgroundColor: 'white',
            borderRadius: 4,
            boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
          }}
        >
          {!isUpperLeftToolbarExpanded && (
            <button
              style={{
                backgroundColor: 'white',
                border: 'none',
                padding: '8px 12px',
                borderRadius: '4px',
                cursor: 'pointer',
                boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)',
              }}
              onClick={() => {
                setIsUpperLeftToolbarExpanded(true);
              }}
            >
              <RightOutlined />
            </button>
          )}
        </div>
        <div
          style={{
            width: '45%',
            // maxWidth: '340px',
            // minWidth: '200px',
            maxWidth: '150px',
            minWidth: '50px',
            position: 'absolute',
            top: '10px',
            left: '10px',
            zIndex: 1,
            backgroundColor: 'white',
            borderRadius: 4,
            boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
          }}
        >
          {isUpperLeftToolbarExpanded && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <button
                id="pipelineHelper"
                style={{
                  backgroundColor: 'white',
                  border: 'none',
                  padding: '8px 15px',
                  cursor: 'pointer',
                  borderRadius: '4px',
                  transition: 'background-color 0.3s',
                  display: 'flex',
                  alignItems: 'center',
                  overflow: 'hidden',
                  whiteSpace: 'nowrap',
                  textOverflow: 'ellipsis',
                  maxWidth: '250px',
                }}
                onClick={() => {
                  if (!analysisId) {
                    message.error('Please select a pipeline first!');
                    return;
                  }
                  openModal(analysisId);
                }}
              >
                <span
                  style={{ overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}
                >
                  Pipeline Helper
                </span>
              </button>
              {/* <Divider
                type="vertical"
                style={{
                  backgroundColor: '#D9D9D9',
                  height: '15px',
                  margin: '0 6px 0 2px',
                }}
              /> */}
              {/* <button
                id="aiReportGenerator"
                className={styles.aiReportGenerator}
                style={{
                  backgroundColor: isAiRepoGenSelected ? '#F0F2FF' : 'white',
                  borderRadius: '4px',
                  border: 'none',
                  padding: isAiRepoGenSelected ? '2px 8px' : '8px 8px',
                  display: 'flex',
                  alignItems: 'center',
                  overflow: 'hidden',
                  whiteSpace: 'nowrap',
                  textOverflow: 'ellipsis',
                  maxWidth: '300px',
                  boxShadow: isAiRepoGenSelected ? '0px 2px 4px rgba(0, 0, 0, 0.1)' : 'none',
                }}
                onClick={handleAiReportGeneratorClick}
                disabled={analysisAccessType === AnalysisType.PUBLIC}
              >
                <CustomImage
                  name={customIconNames.AIICONSTAR}
                  style={{ height: '16px', marginRight: '8px' }}
                />
                <span
                  className="gradient-text"
                  style={{ overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}
                >
                  AI Report Generator
                </span>
              </button> */}
              <button
                style={{
                  backgroundColor: 'white',
                  border: 'none',
                  padding: '2px 0',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
                onClick={() => setIsUpperLeftToolbarExpanded(false)}
              >
                <LeftOutlined />
              </button>
            </div>
          )}
        </div>
        <div
          style={{
            maxWidth: '340px',
            minWidth: '200px',
            position: 'absolute',
            padding: '5px 0',
            borderRadius: 4,
            top: '10px',
            right: '10px',
            zIndex: 1,
          }}
        >
          <AutoComplete
            dropdownMatchSelectWidth={false}
            onSelect={onSelect}
            onSearch={onSearch}
            onClear={onClear}
            value={autoCompleteValue}
            options={autoCompleteOptions.map((option) => ({
              value: option.value,
              label: option.label,
            }))}
          >
            <Input.Search placeholder="Search node" allowClear onSearch={onSelect} />
          </AutoComplete>
        </div>
        <ReactFlow
          id="work"
          nodes={nodes}
          edges={edges}
          onInit={onInit}
          nodeTypes={nodeTypes2NodeComponentMap}
          onlyRenderVisibleElements={true}
          minZoom={0.1}
          maxZoom={10}
          translateExtent={[
            [extents.left - 5000, extents.top - 5000],
            [extents.right + 5000, extents.bottom + 5000],
          ]}
          onSelectionDragStop={onSelectionDragStop}
          // onSelectionDrag={onSelectionDrag}
          onDrop={onDrop}
          onEdgeUpdate={onEdgeUpdate}
          onEdgeUpdateStart={onEdgeUpdateStart}
          onEdgeUpdateEnd={onEdgeUpdateEnd}
          onNodeClick={onNodeClick}
          onNodeDragStart={onNodeDragStart}
          onNodeDrag={onNodeDrag}
          onNodeDragStop={onNodeDragStop}
          onDragOver={onDragOver}
          onConnect={onConnect}
          onPaneClick={onPaneClick}
          // edgeTypes={{ customEdge: CustomEdge }}
          connectionLineComponent={CustomEdge}
          proOptions={proOptions}
        >
          <Background variant={BackgroundVariant.Dots} />
          {currentSelectedNodes.length > 1 && !isGuestUser && (
            <div>
              <Panel position="bottom-center" className={styles.collectionTool}>
                <Popover content={<span style={{ color: '#fff' }}>Group</span>} color="#000">
                  <GroupOutlined style={{ cursor: 'pointer' }} onClick={collectGroup} />
                </Popover>
                <div className={styles.border} />
                <Popover
                  color="#000"
                  title={<span style={{ color: '#fff' }}>Collect pipeline</span>}
                  content={
                    <span style={{ color: '#fff' }}>
                      Enable when nodes be selected in same branch.
                    </span>
                  }
                >
                  <StarOutlined
                    style={{ cursor: 'pointer' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      collectPipelineNode();
                    }}
                  />
                </Popover>

                <div className={styles.border} />
                <CopyOutlined style={{ cursor: 'pointer' }} onClick={copyPipeline} />
                <div className={styles.border} />
                <Popconfirm
                  title="Delete the task"
                  description="Are you sure to delete this task?"
                  icon={
                    <QuestionCircleOutlined
                      style={{
                        color: 'red',
                      }}
                    />
                  }
                  onConfirm={(e) => {
                    e?.stopPropagation();
                    removePipeline();
                  }}
                >
                  <DeleteOutlined
                    onClick={(e) => {
                      e.stopPropagation();
                    }}
                    style={{ cursor: 'pointer' }}
                  />
                </Popconfirm>
              </Panel>
              <CreatePipLine
                isModalOpen={createPipelineShow}
                onCancel={() => setCreatePipelineShow(false)}
              />
            </div>
          )}
        </ReactFlow>
      </div>

      <Modal
        centered
        title="Report a Problem"
        open={!!reportedNodeId}
        onOk={onReportConfirm}
        onCancel={onCancelReport}
      >
        <Spin spinning={isReporting}>
          <Form
            form={reportForm}
            labelAlign="left"
            labelCol={{ span: 5 }}
            onFinish={onReportSubmit}
            autoComplete="off"
          >
            <p>
              Let teams know if your problem is not solved. Your feedback helps us improve the
              system. By sending this report, you agree to allow us to use this information.
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
        open={fixedNodeId !== null}
        onCancel={() => setFixedNodeId(null)}
        onOk={async () => {
          await requestRunBugFixer(fixedNodeId, bugFixerPrompt);
          message.success('Bug fixer is running');
          setFixedNodeId(null);
          setBugFixerPrompt('');
        }}
        cancelText="Close"
        okText="Run"
        title="Run Bug Fixer"
        centered
      >
        <div style={{ height: '100%', position: 'relative' }}>Prompt:</div>
        <TextArea
          onChange={(event: any) => {
            setBugFixerPrompt(event.target.value);
          }}
        />
      </Modal>
    </div>
  );
}
