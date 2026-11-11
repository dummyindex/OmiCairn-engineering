import { NODE_FONT_FAMILY } from '@/constants/font';
import { NodeState } from '@/constants/node';
import * as customIconNames from '@/assets/customIconNames';
import { requestLatestComputation } from '@/request/computation';
import { getLocationParams } from '@/util/getUrl';
import { writeToClipboard } from '@/util/operationTools';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  EllipsisOutlined,
  FolderOpenOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  RobotOutlined,
  ShareAltOutlined,
  SubnodeOutlined,
} from '@ant-design/icons';
import { Divider, Dropdown, Menu, message, Modal, Popover, Space, Tag, Typography } from 'antd';
import promiseConfirm from '@/components/common/promiseConfirm';
import { requestCancelSubtreeComputations, requestDynamicGenerationPlanGet } from '@/request/node';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Handle, Position } from 'reactflow';
import { useModel } from 'umi';
import { FlowTool } from '@/util/flowTool';
import ClaudeCodeOutputsModal from './ClaudeCodeOutputsModal';
import CustomImage from '@/components/common/customImage';
import { AnalysisType } from '@/constants/analysis';

const { Paragraph } = Typography;

const bgColorMap: any = {
  [NodeState.ORIGINAL]: '#FFFFFF',
  [NodeState.RUNNING]: '#96989A',
  [NodeState.FINISHED]: '#019002',
  [NodeState.FAILED]: '#DA0001',
  [NodeState.PENDING]: '#96989A',
  [NodeState.DEBUGGING]: '#96989A',
  [NodeState.GENERATING]: '#96989A',
  [NodeState.BEAUTIFYING]: '#96989A',
  [NodeState.CANCELLED]: '#FFFFFF',
};

const stateFontColorMap: any = {
  [NodeState.ORIGINAL]: '#000',
  [NodeState.RUNNING]: '#fff',
  [NodeState.FINISHED]: '#fff',
  [NodeState.FAILED]: '#fff',
  [NodeState.PENDING]: '#fff',
  [NodeState.DEBUGGING]: '#fff',
  [NodeState.GENERATING]: '#fff',
  [NodeState.BEAUTIFYING]: '#fff',
  [NodeState.CANCELLED]: '#000',
};

interface ClaudeCodeNodeProps {
  id: string;
  data: any;
  selected?: boolean;
}

const ClaudeCodeNode = ({ id, data, selected }: ClaudeCodeNodeProps) => {
  const { name, label, state, dynamicGenerationId, computationResourceConfigure } = data;
  const { dictionary } = useModel('localization');
  const {
    instance,
    currentSelectedNodes,
    setCurrentSelectedNodes,
    analysisAccessType,
    setAutoGenieInspectedNodeId,
    openRenameNode,
  } = useModel('analysis');
  const { nodeId, setNodeId, reportSelectedNodeIds, setReportSelectedNodeIds } =
    useModel('visualPanelControl');
  const { isGuest } = useModel('user');

  const isGuestUser = isGuest();

  const [planModalVisible, setPlanModalVisible] = useState(false);
  const [planData, setPlanData] = useState<{ name: string; steps: string } | null>(null);
  const [computationId, setComputationId] = useState<string | null>(null);
  const [isNodeDeleting, setIsNodeDeleting] = useState(false);
  const [outputsModalVisible, setOutputsModalVisible] = useState(false);
  const [loadingComputationId, setLoadingComputationId] = useState(false);
  const [descriptionModalVisible, setDescriptionModalVisible] = useState(false);

  const handleViewOutputs = useCallback(async () => {
    setOutputsModalVisible(true);
    setLoadingComputationId(true);
    setComputationId(null);
    try {
      const response = await requestLatestComputation(id);
      if (response?.data?.id) {
        setComputationId(response.data.id);
      } else {
        setComputationId(null);
      }
    } catch (error) {
      console.error('Failed to fetch computation:', error);
      setComputationId(null);
    } finally {
      setLoadingComputationId(false);
    }
  }, [id]);

  const fetchPlan = useCallback(async () => {
    if (!dynamicGenerationId) return;

    try {
      const response = await requestDynamicGenerationPlanGet(id, dynamicGenerationId);
      if (response?.data?.presigned_url) {
        const planResponse = await fetch(response.data.presigned_url);
        const plan = await planResponse.json();
        setPlanData(plan);
      }
    } catch (error) {
      console.error('Failed to fetch plan:', error);
    }
  }, [id, dynamicGenerationId]);

  useEffect(() => {
    if (dynamicGenerationId) {
      fetchPlan();
    }
  }, [dynamicGenerationId, fetchPlan]);

  const handleCancel = useCallback(async () => {
    await requestCancelSubtreeComputations(id);
  }, [id]);

  const handleDelete = useCallback(async () => {
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
  }, [
    id,
    data,
    instance,
    currentSelectedNodes,
    setCurrentSelectedNodes,
    reportSelectedNodeIds,
    setReportSelectedNodeIds,
    nodeId,
    setNodeId,
    dictionary,
  ]);

  const nodeStateIcon = () => {
    switch (state) {
      case NodeState.CANCELLED:
      case NodeState.ORIGINAL: {
        return dictionary.READY_TO_RUN || 'Ready to run';
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
              {dictionary.RUN_COMPLETED || 'Run completed'}
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
              {dictionary.RUNTIME_ERROR || 'Runtime error'}
            </div>
          </div>
        );
      }
      default:
        return null;
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

  const menuItems = useMemo(
    () => (
      <Menu>
        {(state === NodeState.RUNNING || state === NodeState.PENDING) && (
          <Menu.Item key="cancel" icon={<CloseCircleOutlined />} onClick={handleCancel}>
            Cancel Computation
          </Menu.Item>
        )}
        {planData && (
          <Menu.Item
            key="plan"
            icon={<InfoCircleOutlined />}
            onClick={() => setPlanModalVisible(true)}
          >
            View Plan
          </Menu.Item>
        )}
        <Menu.Item key="outputs" icon={<FolderOpenOutlined />} onClick={handleViewOutputs}>
          View Outputs
        </Menu.Item>
        <Menu.Item
          key="share"
          icon={<ShareAltOutlined />}
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
        <Menu.Divider />
        <Menu.Item
          key="delete"
          icon={<DeleteOutlined />}
          danger
          onClick={handleDelete}
          disabled={isNodeDeleting}
          style={isNodeDeleting ? { cursor: 'not-allowed' } : undefined}
        >
          Delete
        </Menu.Item>
      </Menu>
    ),
    [
      state,
      planData,
      handleCancel,
      handleDelete,
      isNodeDeleting,
      handleViewOutputs,
      dictionary,
      id,
    ],
  );

  return (
    <>
      <div
        style={{
          width: '280px',
          border: selected ? '1px solid rgba(89, 126, 247, 1)' : '1px solid rgba(217, 217, 217, 1)',
          boxShadow: selected ? '0 0 0 2px #b8c4fc' : 'none',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: '7px',
          overflow: 'hidden',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          transform: selected ? 'translateY(-1px) scale(1.02)' : 'translateY(0) scale(1)',
        }}
        title={name}
      >
        {/* Header - status bar */}
        <div
          style={{
            width: '279px',
            height: '32px',
            backgroundColor: getBgColor(),
            borderBottom: '1px solid #eaeaea',
            display: 'flex',
            gap: '8px',
            justifyContent: 'flex-start',
            alignItems: 'center',
            paddingLeft: '13px',
            paddingRight: '15px',
          }}
        >
          <div>{nodeStateIcon()}</div>
          <div style={{ flex: 1 }}></div>
          <CustomImage
            name={customIconNames.AIICONSTARWHITE}
            style={{
              height: '15px',
              marginBottom: '4px',
              cursor: 'pointer',
            }}
            dropdownMenu={
              <Menu>
                <Menu.ItemGroup title="Node">
                  <Menu.Item
                    key="2"
                    icon={<SubnodeOutlined />}
                    style={{ marginBottom: '5px' }}
                    disabled={
                      (data.state !== NodeState.FINISHED && data.dataId === null) ||
                      analysisAccessType === AnalysisType.PUBLIC ||
                      isGuestUser ||
                      (data.locked && data.state !== NodeState.FINISHED)
                    }
                    onClick={() => {
                      setAutoGenieInspectedNodeId(id);
                    }}
                  >
                    {dictionary.AUTO_GENIE}
                  </Menu.Item>
                </Menu.ItemGroup>
              </Menu>
            }
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <RobotOutlined
              style={{
                fontSize: '14px',
                color: stateFontColorMap[state],
              }}
            />
          </div>
        </div>

        {/* Body - label section */}
        <div
          style={{
            width: '100%',
            height: '69px',
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
            <div
              style={{
                width: '88%',
                color: '#000000',
                fontFamily: NODE_FONT_FAMILY,
                fontSize: '16px',
                fontWeight: 550,
                textAlign: 'left',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {label || 'Agent Node'}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Popover
                content={<span style={{ color: '#fff' }}>{dictionary.RENAME}</span>}
                color="#000"
              >
                <EditOutlined
                  style={{
                    cursor: analysisAccessType === AnalysisType.PUBLIC ? 'not-allowed' : 'pointer',
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
          </div>
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
              <Tag color="orange">Agent</Tag>
            </div>
          </div>
        </div>

        <div
          style={{
            flex: 1,
            paddingTop: '10px',
            backgroundColor: '#FFF',
          }}
        />

        {/* Footer - action bar */}
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
              width: '75%',
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
            Agent node
            <Popover content={<span style={{ color: '#fff' }}>Node Information</span>} color="#000">
              <InfoCircleOutlined
                style={{ cursor: 'pointer', marginLeft: '3px' }}
                onClick={(e) => {
                  e.stopPropagation();
                  setDescriptionModalVisible(true);
                }}
              />
            </Popover>
          </div>
          <Space>
            <Dropdown overlay={menuItems} trigger={['hover']}>
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
      </div>

      {/* Handles */}
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

      {/* Plan Modal */}
      <Modal
        title={
          <Space>
            <InfoCircleOutlined />
            Execution Plan
          </Space>
        }
        open={planModalVisible}
        onCancel={() => setPlanModalVisible(false)}
        footer={null}
        width={600}
      >
        {planData ? (
          <div>
            <h3>{planData.name}</h3>
            <Divider />
            <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{planData.steps}</Paragraph>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
            No plan data available
          </div>
        )}
      </Modal>

      {/* Outputs Modal */}
      <ClaudeCodeOutputsModal
        visible={outputsModalVisible}
        computationId={computationId}
        loadingComputationId={loadingComputationId}
        onClose={() => setOutputsModalVisible(false)}
      />

      {/* Description Modal */}
      <Modal
        title={<Space>Node Information</Space>}
        open={descriptionModalVisible}
        onCancel={() => setDescriptionModalVisible(false)}
        footer={null}
        width={550}
      >
        <div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '140px 1fr',
              gap: '8px 16px',
              fontSize: '13px',
            }}
          >
            {name && (
              <>
                <span style={{ color: '#666' }}>Name:</span>
                <span>{name}</span>
              </>
            )}
            {label && (
              <>
                <span style={{ color: '#666' }}>Task:</span>
                <span>{label}</span>
              </>
            )}
            {computationResourceConfigure && (
              <>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '140px 1fr',
                    gap: '8px 16px',
                    fontSize: '13px',
                  }}
                >
                  {(() => {
                    const config =
                      typeof computationResourceConfigure === 'string'
                        ? JSON.parse(computationResourceConfigure)
                        : computationResourceConfigure;
                    return (
                      <>
                        {config.vcpu !== undefined && (
                          <>
                            <span style={{ color: '#666' }}>vCPU:</span>
                            <span>{config.vcpu}</span>
                          </>
                        )}
                        {config.ram !== undefined && (
                          <>
                            <span style={{ color: '#666' }}>Memory (GB):</span>
                            <span>{config.ram}</span>
                          </>
                        )}
                        {config.gpu !== undefined && (
                          <>
                            <span style={{ color: '#666' }}>GPU:</span>
                            <span>{config.gpu}</span>
                          </>
                        )}
                        {config.timeout !== undefined && (
                          <>
                            <span style={{ color: '#666' }}>Timeout(s):</span>
                            <span>{config.timeout}</span>
                          </>
                        )}
                      </>
                    );
                  })()}
                </div>
              </>
            )}
          </div>
        </div>
      </Modal>
    </>
  );
};

export default ClaudeCodeNode;
