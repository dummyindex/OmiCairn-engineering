import Graph from '@/components/special/analysisPanel/graph';
import SiderBox from '@/components/special/analysisPanel/side';
import VisualSider from '@/components/special/analysisPanel/visualSide';
import AiAnalysisSider from '@/components/special/analysisPanel/aiAnalysisSider';
import ChatbotPanel from '@/components/special/analysisPanel/aiAssistant/chatbotPanel';
import Overlays from '@/components/special/globalDialog/overlays';
import { Layout } from 'antd';
import { useEffect, useState } from 'react';
import { ReactFlowProvider } from 'reactflow';
import { useModel } from 'umi';
import FlowToolBar from '@/components/special/analysisPanel/flowToolBar';
import UpdateParameterModal from '@/components/special/analysisPanel/editParameters';
import PreviousParameter from '@/components/special/analysisPanel/previousParameter';
import NodeComputationResourceConfig from '@/components/special/globalDialog/nodeComputationResourceConfig';
import './textSelection.css';
const { Footer, Sider, Content } = Layout;
import { FigureCacheProvider } from '@/contexts/FigureCache';

export default function FlowPanel() {
  const {
    paramEditedNodeId,
    paramEditedFbId,
    closeEditParameterModal,
    setShiftKey,
    shiftKey,
    currentSelectedNodes,
    setCurrentSelectedNodes,
    setNodeBorder,
    setErrorNodeList,
    showError,
    setShowError,
    runNode,
    instance,
    isCloseBtnClicked,
    setIsCloseBtnClicked,
  } = useModel('analysis');
  const { chatbotVisible } = useModel('aiUI');
  const {
    isToolbarCollapsed,
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
  } = useModel('visualPanelControl');

  const [previousParameterVisible, setPreviousParameterVisible] = useState<boolean>(false);
  const [previousParameterDict, setPreviousParameterDict] = useState<any>({});
  const [previousParameterMaximized, setPreviousParameterMaximized] = useState<boolean>(false);
  const { chatbotMaximized, setChatbotMaximized } = useModel('aiUI');

  const [isDraggingLeft, setIsDraggingLeft] = useState<boolean>(false);
  const [isDraggingRight, setIsDraggingRight] = useState<boolean>(false);

  const contentStyle: React.CSSProperties = {
    textAlign: 'center',
    color: '#000',
    height: 'calc(95vh)',
    backgroundColor: '#F3F3F2',
  };

  const footerStyle: React.CSSProperties = {
    position: 'fixed',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    textAlign: 'center',
    color: '#000',
    padding: '9px 12px',
    backgroundColor: '#FFFFFF',
    bottom: '16px',
    left: '49%',
    transform: 'translateX(-50%)',
    maxWidth: isToolbarCollapsed ? '60px' : '100%',
    boxShadow: '0px 2px 18px 0px #0000000B',
    border: '1px solid rgba(226, 228, 236, 1)',
    borderRadius: '4px',
    zIndex: 1000,
    transition: 'all 1s ease',
    overflow: 'hidden',
  };

  const leftSiderStyle: React.CSSProperties = {
    height: '95vh',
    color: '#000',
    backgroundColor: '#FFFFFF',
    boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.04)',
    borderRight: '0.5px solid rgb(151,151,151,0.5)',
    width: `${leftSiderWidth}vw`,
    position: 'relative',
    zIndex: 1,
  };

  const rightSiderStyle: React.CSSProperties = {
    height: '95vh',
    color: '#000',
    backgroundColor: '#FFFFFF',
    boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.04)',
    borderLeft: '0.5px solid rgb(151,151,151,0.5)',
    width: `${rightSiderWidth}vw`,
    position: 'relative',
    zIndex: 1,
  };

  const dashboardSiderStyle: React.CSSProperties = {
    height: '95vh',
    color: '#000',
    backgroundColor: '#FFFFFF',
    boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.04)',
    borderLeft: '0.5px solid rgb(151,151,151,0.5)',
    width: `${dashboardSiderWidth}vw`,
    position: 'relative',
    zIndex: 1,
  };

  const chatbotSiderStyle: React.CSSProperties = {
    width: '21vw',
    color: '#000',
    backgroundColor: '#FFFFFF',
    boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.04)',
    borderLeft: '0.5px solid rgb(151,151,151,0.5)',
    position: 'fixed',
    right: 0,
    bottom: 0,
    zIndex: 1000,
  };

  const leftDragHandleStyle: React.CSSProperties = {
    position: 'absolute',
    right: 0,
    top: 0,
    width: '2px',
    height: '100%',
    cursor: 'ew-resize',
    backgroundColor: isDraggingLeft ? 'rgba(89, 126, 247, 1)' : 'transparent',
  };

  const rightDragHandleStyle: React.CSSProperties = {
    position: 'absolute',
    left: 0,
    top: 0,
    width: '2px',
    height: '100%',
    cursor: 'ew-resize',
    backgroundColor: isDraggingRight ? 'rgba(89, 126, 247, 1)' : 'transparent',
  };

  const dashboardHandleStyle: React.CSSProperties = {
    position: 'absolute',
    left: 0,
    top: 0,
    width: '2px',
    height: '100%',
    cursor: 'ew-resize',
    backgroundColor: isDraggingRight ? 'rgba(89, 126, 247, 1)' : 'transparent',
  };

  const openPreviousParameter = (previousParamDict: any) => {
    if (!!previousParamDict) {
      setPreviousParameterDict(previousParamDict);
    } else {
      setPreviousParameterDict({});
    }
    setPreviousParameterVisible(true);
  };

  const onPreviousParameterClose = () => {
    setPreviousParameterVisible(false);
    setPreviousParameterMaximized(false);
  };

  const showMenu = () => {
    setIsShowMenu(!isShowMenu);
  };
  const showVisual = () => {
    setIsShowVisual(!isShowVisual);
  };
  const showAIDashboard = () => {
    setIsShowAIDashboard(!isShowAIDashboard);
  };

  useEffect(() => {
    if (isCloseBtnClicked) {
      setIsShowAIDashboard(!isShowAIDashboard);
      setIsShowMenu(!isShowMenu);
      setIsCloseBtnClicked(false);
    }
  }, [isCloseBtnClicked]);

  useEffect(() => {
    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.key === 'Shift') {
        setShiftKey(false);
        document.body.classList.remove('no-select');
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Shift') {
        setShiftKey(true);
        setNodeBorder(true);
        document.body.classList.add('no-select');
      }
    };
    window.addEventListener('keyup', handleKeyUp);
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      // Remove keyboard listeners
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);
  const handleClick = () => {
    if (shiftKey == false && currentSelectedNodes.length > 1) {
      setCurrentSelectedNodes([]);
    }
  };

  const handleMouseDownLeft = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDraggingLeft(true);
    document.body.style.userSelect = 'none';
  };

  const handleMouseDownRight = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDraggingRight(true);
    document.body.style.userSelect = 'none';
  };

  const handleMouseUp = () => {
    setIsDraggingLeft(false);
    setIsDraggingRight(false);
    document.body.style.userSelect = '';
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (isDraggingLeft) {
      const newWidth = (e.clientX / window.innerWidth) * 100;
      if (newWidth >= 11 && newWidth <= 40) {
        setLeftSiderWidth(newWidth);
      }
    } else if (isDraggingRight) {
      if (isShowAIDashboard) {
        const newWidth = ((window.innerWidth - e.clientX) / window.innerWidth) * 100;
        if (newWidth >= 20 && newWidth <= 70) {
          setDashboardSiderWidth(newWidth);
        }
      }
      if (isShowVisual) {
        const newWidth = ((window.innerWidth - e.clientX) / window.innerWidth) * 100;
        if (newWidth >= 15 && newWidth <= 60) {
          setRightSiderWidth(newWidth);
        }
      }
    }
  };

  useEffect(() => {
    if (isDraggingLeft || isDraggingRight) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    } else {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDraggingLeft, isDraggingRight]);

  return (
    <FigureCacheProvider>
      <ReactFlowProvider>
        <Layout>
          {isShowMenu ? (
            <Sider width={`${leftSiderWidth}vw`} style={leftSiderStyle}>
              <SiderBox />
              <div style={leftDragHandleStyle} onMouseDown={handleMouseDownLeft} />
            </Sider>
          ) : (
            ''
          )}
          <Content style={contentStyle} onClick={handleClick}>
            <Graph />
          </Content>
          {isShowVisual && !isShowAIDashboard ? (
            <Sider width={`${rightSiderWidth}vw`} style={rightSiderStyle}>
              <VisualSider />
              <div style={rightDragHandleStyle} onMouseDown={handleMouseDownRight} />
            </Sider>
          ) : (
            ''
          )}
          {isShowAIDashboard ? (
            <Sider width={`${dashboardSiderWidth}vw`} style={dashboardSiderStyle}>
              <AiAnalysisSider isShowAIDashboard={isShowAIDashboard} />
              <div style={dashboardHandleStyle} onMouseDown={handleMouseDownRight} />
            </Sider>
          ) : (
            ''
          )}
          <Sider width="21vw" style={chatbotSiderStyle}>
            <ChatbotPanel />
          </Sider>
        </Layout>
        <Overlays />
        <Footer style={footerStyle}>
          <FlowToolBar
            showMenu={showMenu}
            setIsShowMenu={setIsShowMenu}
            showVisual={showVisual}
            showAIDashboard={showAIDashboard}
            setIsShowAIDashboard={setIsShowAIDashboard}
            setShowError={setShowError}
            isShowMenu={isShowMenu}
            isShowVisual={isShowVisual}
            isShowAIDashboard={isShowAIDashboard}
            showError={showError}
            setErrorNodeList={setErrorNodeList}
          />
        </Footer>
        <UpdateParameterModal
          style={
            previousParameterVisible || chatbotVisible
              ? {
                  position: 'fixed',
                  left: '8vw',
                  top: '15vh',
                }
              : {}
          }
          runNode={runNode}
          instance={instance}
          paramEditedNodeId={paramEditedNodeId}
          paramEditedFbId={paramEditedFbId}
          onClose={closeEditParameterModal}
          openPreviousParameter={openPreviousParameter}
        />
        <NodeComputationResourceConfig />

        {!!paramEditedNodeId && (chatbotVisible || previousParameterVisible) && (
          <div
            style={{
              width: '30vw',
              height: '70vh',
              position: 'fixed',
              top: '15vh',
              right: '10vw',
              zIndex: 1000,
            }}
          >
            {previousParameterVisible && (
              <div
                style={{
                  height: !chatbotVisible
                    ? '70vh'
                    : previousParameterMaximized
                    ? '65vh'
                    : chatbotMaximized
                    ? '5vh'
                    : '35vh',
                }}
              >
                <PreviousParameter
                  previousParamDict={previousParameterDict}
                  onClose={onPreviousParameterClose}
                  maximized={previousParameterMaximized}
                  setMaximized={(newMaximized: boolean) => {
                    if (newMaximized) {
                      setPreviousParameterMaximized(true);
                      setChatbotMaximized(false);
                    } else {
                      setPreviousParameterMaximized(false);
                    }
                  }}
                />
              </div>
            )}

            {previousParameterVisible && chatbotVisible && (
              <div
                style={{
                  height: '1em',
                }}
              />
            )}
          </div>
        )}
      </ReactFlowProvider>
    </FigureCacheProvider>
  );
}
