import { AnalysisType } from '@/constants/analysis';
import { NODE_FONT_FAMILY } from '@/constants/font';
import { NodeState } from '@/constants/node';
import { requestDeleteNode } from '@/request/node';
import { getLocationParams } from '@/util/getUrl';
import { writeToClipboard } from '@/util/operationTools';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  ExclamationCircleFilled,
  FileTextOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  ShareAltOutlined,
} from '@ant-design/icons';
import { message, Modal, Popover } from 'antd';
import { useState } from 'react';
import { Handle, Position } from 'reactflow';
import { useModel } from 'umi';

const { confirm } = Modal;

const ReportNode = (node: any) => {
  const { data, id } = node;
  const { state } = data;

  const { setNodeId } = useModel('visualPanelControl');
  const { showModal: showDetailModal } = useModel('nodeDetail');

  const {
    currentSelectedNodes,
    setCurrentSelectedNodes,
    analysisAccessType,
    instance,
    setNodes,
    setEdges,
    compactMode,
    openRenameNode,
  } = useModel('analysis');

  const [isDeleting, setIsDeleting] = useState(false);

  const handleClick = () => {
    if (currentSelectedNodes.some((node) => node.id === id)) {
      setCurrentSelectedNodes(currentSelectedNodes.filter((node) => node.id !== id));
    } else {
      setCurrentSelectedNodes([node]);
      setNodeId(id);
    }
  };

  const removeReportNode = async () => {
    if (analysisAccessType === AnalysisType.PUBLIC) {
      message.error('You are not allowed to delete nodes in public analysis.');
      return;
    }

    confirm({
      title: 'Delete Report Node',
      icon: <ExclamationCircleFilled />,
      content: 'Are you sure you want to delete this report node?',
      okText: 'Delete',
      okType: 'danger',
      cancelText: 'Cancel',
      centered: true,
      async onOk() {
        setIsDeleting(true);
        const hideLoadingMessage = message.loading('Deleting report node...', 0);

        try {
          const edges = instance.toObject().edges;

          if (currentSelectedNodes.some((node) => node.id === id)) {
            setCurrentSelectedNodes(currentSelectedNodes.filter((node) => node.id !== id));
          }

          await requestDeleteNode(id);

          const connectedEdges = edges.filter(
            (edge: any) => edge.source === id || edge.target === id,
          );

          setNodes((nds) => nds.filter((node) => node.id !== id));

          if (connectedEdges.length > 0) {
            setEdges((eds) => eds.filter((edge: any) => edge.source !== id && edge.target !== id));
          }

          hideLoadingMessage();
          message.success('Report node deleted successfully');
        } catch (error) {
          console.error('Error deleting report node:', error);
          hideLoadingMessage();
          message.error('Failed to delete report node');
        } finally {
          setIsDeleting(false);
        }
      },
      onCancel() {
        console.log('Delete cancelled');
      },
    });
  };

  const openRenameReportNode = () => {
    openRenameNode(id);
  };

  const handleShareReportNode = () => {
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
  };

  const getStateIcon = () => {
    switch (state) {
      case NodeState.RUNNING:
        return <LoadingOutlined style={{ color: '#fff' }} />;
      case NodeState.FINISHED:
        return <CheckCircleOutlined style={{ color: '#fff' }} />;
      case NodeState.FAILED:
        return <CloseCircleOutlined style={{ color: '#fff' }} />;
      default:
        return <FileTextOutlined style={{ color: '#fff' }} />;
    }
  };

  const getBgColor = () => {
    switch (state) {
      case NodeState.RUNNING:
        return '#96989A';
      case NodeState.FINISHED:
        return '#946ecaff';
      case NodeState.FAILED:
        return '#ff4d4f';
      default:
        return '#FFFFFF';
    }
  };

  return (
    <>
      <div
        style={{
          width: '280px',
          border: currentSelectedNodes.some((node) => node.id === id)
            ? '1px solid rgba(89, 126, 247, 1)'
            : '1px solid rgba(217, 217, 217, 1)',
          boxShadow: currentSelectedNodes.some((node) => node.id === id)
            ? '0 0 0 2px #b8c4fc'
            : 'none',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: '7px',
          overflow: 'hidden',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          transform: currentSelectedNodes.some((node) => node.id === id)
            ? 'translateY(-1px) scale(1.02)'
            : 'translateY(0) scale(1)',
        }}
        onClick={handleClick}
        title={data.label}
      >
        {/* Header with status */}
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
          {!compactMode ? (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              {getStateIcon()}
              <span style={{ marginLeft: '8px', color: '#fff', fontSize: '13px', fontWeight: 300 }}>
                {state === NodeState.RUNNING
                  ? 'Generating...'
                  : state === NodeState.FINISHED
                  ? 'Report Ready'
                  : state === NodeState.FAILED
                  ? 'Generation Failed'
                  : 'Report Node'}
              </span>
            </div>
          ) : null}

          {!compactMode ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Popover content={<span style={{ color: '#fff' }}>Share</span>} color="#000">
                <ShareAltOutlined
                  style={{
                    fontSize: '16px',
                    color: '#fff',
                    cursor: 'pointer',
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleShareReportNode();
                  }}
                />
              </Popover>
              <DeleteOutlined
                style={{
                  fontSize: '16px',
                  color: '#fff',
                  cursor:
                    isDeleting || analysisAccessType === AnalysisType.PUBLIC
                      ? 'not-allowed'
                      : 'pointer',
                  opacity: isDeleting ? 0.6 : 1,
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  if (!isDeleting && analysisAccessType !== AnalysisType.PUBLIC) {
                    removeReportNode();
                  }
                }}
              />
            </div>
          ) : null}
        </div>

        {/* Main content area with label */}
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
            {!compactMode ? (
              <div
                style={{
                  width: '90%',
                  color: '#000000',
                  fontFamily: NODE_FONT_FAMILY,
                  fontSize: '16px',
                  fontWeight: 550,
                  textAlign: 'left',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {data.label || 'Report'}
              </div>
            ) : (
              <div
                style={{
                  width: '90%',
                  color: '#000000',
                  fontFamily: NODE_FONT_FAMILY,
                  fontSize: '16px',
                  fontWeight: 550,
                  textAlign: 'left',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {data.label || 'Report'}
              </div>
            )}

            {!compactMode ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <Popover
                  content={<span style={{ color: '#fff' }}>Rename Report</span>}
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
                        openRenameReportNode();
                      }
                    }}
                  />
                </Popover>
              </div>
            ) : null}
          </div>
        </div>

        <div
          style={{
            flex: 1,
            paddingTop: '10px',
            backgroundColor: '#FFF',
          }}
        />

        {/* Bottom footer with action icons */}
        {!compactMode ? (
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
              Report Generation
              <Popover
                content={<span style={{ color: '#fff' }}>Report Node description</span>}
                color="#000"
              >
                <InfoCircleOutlined
                  style={{ cursor: 'pointer', marginLeft: '3px' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    showDetailModal(id);
                  }}
                />
              </Popover>
            </div>
          </div>
        ) : null}
      </div>

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
    </>
  );
};

export default ReportNode;
