import { NODE_FONT_FAMILY } from '@/constants/font';
import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { AnalysisType } from '@/constants/analysis';
import { NodeState } from '@/constants/node';
import { cutString } from '@/util/stringHelpers';
import {
  CopyOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  EditOutlined,
  HistoryOutlined,
  LockOutlined,
  OrderedListOutlined,
  PaperClipOutlined,
  PlaySquareOutlined,
  QuestionCircleOutlined,
  SisternodeOutlined,
  SubnodeOutlined,
  ThunderboltOutlined,
  ToolOutlined,
} from '@ant-design/icons';
import { Checkbox, Divider, Dropdown, Menu, message, Popconfirm, Popover, Space } from 'antd';
import { useMemo, useState } from 'react';
import { Handle, Position, useViewport } from 'reactflow';
import { useModel } from 'umi';
// import 'antd/dist/antd.css';
import './CustomCheckbox.css';
import styles from './overview.less';
import GeneralInputsList from '../../globalDialog/generalInputsList';
import ExtraFilesDialog from './ExtraFilesDialog';

const DataSourceNodeV2 = (node: any) => {
  const { data, id } = node;
  const { locked, plotOnly } = data;
  const {
    shiftKey,
    instance,
    runSubTree,
    copyNode,
    openRenameNode,
    findSubCompleteNodeId,
    currentSelectedNodes,
    setCurrentSelectedNodes,
    temporaryCenteredNodeId,
    analysisAccessType,
    compactMode,
    setAutoGenieInspectedNodeId,
    setAgentHistoryInspectedNodeId,
    setBugFixerInspectedNodeId,
    setBeautifierInspectedNodeId,
  } = useModel('analysis');
  const {
    dataId,
    setDataId,
    reportSelectedNodeIds,
    setReportSelectedNodeIds,
    isAiRepoGenSelected,
    chatbotState,
    setChatbotState,
  } = useModel('visualPanelControl');
  const { dictionary } = useModel('localization');
  const { isGuest } = useModel('user');
  const isGuestUser = isGuest();
  const [isNodeDeleting, setIsNodeDeleting] = useState(false);
  const [isFileListVisible, setIsFileListVisible] = useState(false);
  const [extraFilesDialogConfig, setExtraFilesDialogConfig] = useState<{
    visible: boolean;
    nodeId: string;
  }>({
    visible: false,
    nodeId: '',
  });

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
    () => (data.label ? cutString(data.label, 20) : ''),
    [data.label],
  );

  const renameNode = () => {
    openRenameNode(id);
  };
  const removeNode = async () => {
    setIsNodeDeleting(true);
    const hideLoadingMessage = message.loading('Deletion in progress...', 0);

    try {
      const { remove } = data;
      const edges = instance.toObject().edges;
      if (currentSelectedNodes.some((node) => node.id === id)) {
        setCurrentSelectedNodes(currentSelectedNodes.filter((node) => node.id !== id));
      }
      if (reportSelectedNodeIds.includes(id)) {
        setReportSelectedNodeIds(reportSelectedNodeIds.filter((nodeId) => nodeId !== id));
      }
      await remove(id, node, edges);
      if (id === dataId) {
        setDataId(null);
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

  const handleCheckboxChange = (e, nodeId) => {
    const subCompleteNodeList = findSubCompleteNodeId(nodeId, instance);

    if (e.target.checked) {
      setReportSelectedNodeIds([
        ...reportSelectedNodeIds,
        nodeId,
        ...subCompleteNodeList.filter((id) => !reportSelectedNodeIds.includes(id)),
      ]);
    } else {
      setReportSelectedNodeIds(
        reportSelectedNodeIds.filter((id) => id !== nodeId && !subCompleteNodeList.includes(id)),
      );
    }
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
              setBeautifierInspectedNodeId(id);
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
              setBugFixerInspectedNodeId(id);
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
            <span className="gradient-text">Chat</span>
          </Menu.Item>
        </Menu.ItemGroup>
      </Menu>
    </div>
  );

  return (
    <>
      {compactMode && currentSelectedNodes.some((node) => node.id === id) ? (
        <div
          style={{
            position: 'absolute',
            top: -45,
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
              {!locked && (
                <div style={{ flex: 1, textAlign: 'center' }}>
                  <Popover
                    content={<span style={{ color: '#fff' }}>{dictionary.RUN_TREE}</span>}
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
                          runSubTree(id, instance);
                        }
                      }}
                    />
                  </Popover>
                </div>
              )}
              {!locked && (
                <div style={{ flex: 1, textAlign: 'center' }}>
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
                </div>
              )}
              {!locked && (
                <div style={{ flex: 1, textAlign: 'center' }}>
                  {analysisAccessType !== AnalysisType.PUBLIC && !isNodeDeleting ? (
                    <Popconfirm
                      title={dictionary.DELETE + '?'}
                      content="Are you sure to delete this data node?"
                      icon={
                        <QuestionCircleOutlined
                          style={{
                            color: 'red',
                          }}
                        />
                      }
                      okText={dictionary.CONFIRM}
                      cancelText={dictionary.CANCEL}
                      onCancel={(e) => {
                        e.stopPropagation();
                      }}
                      onConfirm={(e) => {
                        e.stopPropagation();
                        removeNode();
                      }}
                    >
                      <DeleteOutlined
                        style={{
                          cursor: isNodeDeleting ? 'not-allowed' : 'pointer',
                          marginLeft: '0.5vw',
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                        }}
                      />
                    </Popconfirm>
                  ) : (
                    <DeleteOutlined
                      style={{ cursor: 'not-allowed' }}
                      onClick={(e) => {
                        e.stopPropagation();
                      }}
                    />
                  )}
                </div>
              )}
              {/* {!locked && (
                <div style={{ flex: 1, textAlign: 'center' }}>
                  <Popover content={<span>{dictionary.DOWNLOAD_DATA}</span>}>
                    <DownloadOutlined
                      style={{
                        cursor: 'pointer',
                        fontSize: '16px',
                        width: '16px',
                        height: '16px',
                      }}
                      onClick={async (e) => {
                        e.stopPropagation();
                        try {
                          const sourceNodeDataId = data.dataId;
                          const { data: downloadUrl } = await requestDownloadDataSource(
                            sourceNodeDataId,
                          );
                          await downloadFile(downloadUrl, '');
                        } catch {
                          message.error('download failed');
                        }
                      }}
                    />
                  </Popover>
                </div>
              )} */}
              {locked && (
                <div style={{ color: '#000', flex: 1, textAlign: 'center' }}>
                  <LockOutlined style={{ marginRight: '8px' }} />
                  {dictionary.LOCKED}
                </div>
              )}
              <Divider
                type="vertical"
                style={{
                  backgroundColor: 'rgba(191, 191, 191, 1)',
                  height: '15px',
                  margin: '0 2px 0 5px',
                }}
              />
              <div style={{ flex: 1, textAlign: 'center' }}>
                <Dropdown overlay={aiActionsMenu} trigger={['hover']}>
                  <div style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <CustomImage
                      name={customIconNames.AIICONSTAR}
                      style={{
                        height: '15px',
                        marginRight: '10px',
                        marginBottom: '4px',
                      }}
                    />
                    <span className={styles.askAITitle}>{dictionary.ASK_AI}</span>
                  </div>
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
            backgroundColor: '#9098f1ff',
            borderBottom: '1px solid #E2E4EC',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingLeft: '15px',
            paddingRight: '15px',
          }}
        >
          {!compactMode ? (
            <div
              style={{
                fontFamily: NODE_FONT_FAMILY,
                fontSize: '13px',
                fontWeight: 300,
                color: '#fff',
                lineHeight: '16px',
              }}
            >
              <DatabaseOutlined /> Data Source
            </div>
          ) : null}
          {!compactMode ? (
            <div>
              {
                <div>
                  <CustomImage
                    name={customIconNames.AIICONSTARWHITE}
                    style={{
                      height: '15px',
                      marginBottom: '4px',
                      cursor: 'pointer',
                    }}
                    dropdownMenu={aiActionsMenu}
                  />
                  {/* <Popover
                    content={<span style={{ color: '#fff' }}>{dictionary.DOWNLOAD_DATA}</span>}
                    color="#000"
                  >
                    <DownloadOutlined
                      style={{
                        marginTop: '5px',
                        cursor: 'pointer',
                        fontSize: '16px',
                        width: '16px',
                        height: '16px',
                        color: '#fff',
                      }}
                      onClick={async (e) => {
                        e.stopPropagation();
                        try {
                          const sourceNodeDataId = data.dataId;
                          const { data: downloadUrl } = await requestDownloadDataSource(
                            sourceNodeDataId,
                          );
                          await downloadFile(downloadUrl, '');
                        } catch {
                          message.error('download failed');
                        }
                      }}
                    />
                  </Popover> */}
                  {isAiRepoGenSelected && (
                    <Checkbox
                      className="data-source-custom-checkbox"
                      style={{
                        cursor: 'pointer',
                        color: '#fff',
                        marginLeft: '8px',
                      }}
                      onChange={(e) => handleCheckboxChange(e, id)}
                      checked={reportSelectedNodeIds.includes(node.id)}
                    />
                  )}
                </div>
              }
            </div>
          ) : null}
        </div>

        {/* {data.label} */}
        <div
          style={{
            width: '100%',
            height: compactMode ? '48px' : '80px',
            display: 'flex',
            flexDirection: 'column',
            color: '#fff',
            backgroundColor: '#9098f1ff',
            paddingLeft: '14px',
            paddingRight: '15px',
          }}
        >
          <div
            style={{
              width: '100%',
              height: '40px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            {' '}
            {!compactMode ? (
              <div
                style={{
                  width: '85%',
                  fontFamily: NODE_FONT_FAMILY,
                  fontSize: '16px',
                  fontWeight: 500,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: '10px',
                  whiteSpace: 'nowrap',
                }}
              >
                {cutString(data.label, 20)}
              </div>
            ) : (
              <div style={zoomResistantLabelStyle}>{cutStringMemoized}</div>
            )}
            {!compactMode ? (
              <Popover
                content={<span style={{ color: '#fff' }}>{dictionary.RENAME}</span>}
                color="#000"
              >
                <EditOutlined
                  style={{
                    cursor: analysisAccessType === AnalysisType.PUBLIC ? 'not-allowed' : 'pointer',
                    fontSize: '16px',
                    marginTop: '12px',
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (analysisAccessType !== AnalysisType.PUBLIC) {
                      renameNode();
                    }
                  }}
                />
              </Popover>
            ) : null}
          </div>
        </div>
        {!compactMode ? (
          <div style={{ height: '37px', width: '100%', backgroundColor: '#fff' }}>
            {' '}
            <div
              style={{
                width: '100%',
                height: '37px',
                backgroundColor: '#FFF',
                color: '#5971C0',
                display: 'flex',
                justifyContent: 'flex-start',
                paddingLeft: '10px',
                paddingRight: '15px',
                alignItems: 'center',
              }}
            >
              <div
                style={{
                  fontStyle: 'italic',
                  width: '66px',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {data.label}
              </div>
              <div style={{ flex: 1 }} />

              <Popover content={<span style={{ color: '#fff' }}>Extra Files</span>} color="#000">
                <PaperClipOutlined
                  style={{ cursor: 'pointer' }}
                  onClick={async () => {
                    setExtraFilesDialogConfig({
                      visible: true,
                      nodeId: id,
                    });
                  }}
                />
              </Popover>
              <Popover content={<span style={{ color: '#fff' }}>Show Files</span>} color="#000">
                <OrderedListOutlined
                  style={
                    analysisAccessType === AnalysisType.PUBLIC
                      ? { cursor: 'not-allowed', marginLeft: '0.5vw' }
                      : { cursor: 'pointer', marginLeft: '0.5vw' }
                  }
                  onClick={(e) => {
                    e.stopPropagation();
                    if (analysisAccessType !== AnalysisType.PUBLIC) {
                      setIsFileListVisible(true);
                    }
                  }}
                />
              </Popover>
              {!locked && (
                <div>
                  {' '}
                  <Popover
                    content={<span style={{ color: '#fff' }}>{dictionary.RUN_TREE}</span>}
                    color="#000"
                  >
                    <PlaySquareOutlined
                      style={
                        analysisAccessType === AnalysisType.PUBLIC
                          ? { cursor: 'not-allowed', marginLeft: '0.5vw' }
                          : { cursor: 'pointer', marginLeft: '0.5vw' }
                      }
                      onClick={(e) => {
                        e.stopPropagation();
                        if (analysisAccessType !== AnalysisType.PUBLIC) {
                          runSubTree(id, instance);
                        }
                      }}
                    />
                  </Popover>
                  <CopyOutlined
                    style={
                      analysisAccessType === AnalysisType.PUBLIC
                        ? { cursor: 'not-allowed', marginLeft: '0.5vw' }
                        : { cursor: 'pointer', marginLeft: '0.5vw' }
                    }
                    onClick={(e) => {
                      e.stopPropagation();
                      if (analysisAccessType !== AnalysisType.PUBLIC) {
                        copyNode(id);
                      }
                    }}
                  />
                  {analysisAccessType !== AnalysisType.PUBLIC && !isNodeDeleting ? (
                    <Popconfirm
                      title={dictionary.DELETE + '?'}
                      content="Are you sure to delete this data node?"
                      icon={
                        <QuestionCircleOutlined
                          style={{
                            color: 'red',
                          }}
                        />
                      }
                      okText={dictionary.CONFIRM}
                      cancelText={dictionary.CANCEL}
                      onCancel={(e) => {
                        e.stopPropagation();
                      }}
                      onConfirm={(e) => {
                        e.stopPropagation();
                        removeNode();
                      }}
                    >
                      <DeleteOutlined
                        style={{
                          cursor: isNodeDeleting ? 'not-allowed' : 'pointer',
                          marginLeft: '0.5vw',
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                        }}
                      />
                    </Popconfirm>
                  ) : (
                    <DeleteOutlined
                      style={{ cursor: 'not-allowed', marginLeft: '0.5vw' }}
                      onClick={(e) => {
                        e.stopPropagation();
                      }}
                    />
                  )}
                </div>
              )}
              {locked && (
                <div style={{ color: '#000' }}>
                  <LockOutlined style={{ marginLeft: '8px' }} />
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
      {!compactMode ? (
        <Handle
          style={{
            top: '50%',
            right: -6,
            width: 15,
            height: 60,
            backgroundColor: '#979797',
            border: '1px solid #979797',
            borderRadius: 5,
          }}
          type="source"
          position={Position.Right}
        />
      ) : (
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
      <GeneralInputsList
        nodeId={id}
        open={isFileListVisible}
        onClose={() => setIsFileListVisible(false)}
      />
      <ExtraFilesDialog
        visible={extraFilesDialogConfig.visible}
        onCancel={() => setExtraFilesDialogConfig({ ...extraFilesDialogConfig, visible: false })}
        nodeId={extraFilesDialogConfig.nodeId}
        onOk={() => {
          // Handle OK action
          setExtraFilesDialogConfig({ ...extraFilesDialogConfig, visible: false });
        }}
      />
    </>
  );
};

export default DataSourceNodeV2;
