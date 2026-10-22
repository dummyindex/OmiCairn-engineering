import { NodeState } from '@/constants/node';
import { AnalysisType } from '@/constants/analysis';
import { requestPublicAnalysisList, requestRecordAnalysisOpened } from '@/request/analysis';
import { requestCancelAllTask } from '@/request/task';
import { history, useModel } from 'umi';
import {
  AimOutlined,
  AlertOutlined,
  AppstoreOutlined,
  EyeInvisibleOutlined,
  EyeOutlined,
  InfoCircleOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MinusOutlined,
  PauseOutlined,
  PlusOutlined,
  SettingOutlined,
  ZoomInOutlined,
} from '@ant-design/icons';
import {
  Badge,
  Button,
  message,
  Checkbox,
  Divider,
  InputNumber,
  Dropdown,
  Menu,
  Tooltip,
  Switch,
} from 'antd';
import { useEffect, useState, useRef } from 'react';
import { useViewport } from 'reactflow';
import style from './flowToolBar.less';
import { getLocationParams } from '@/util/getUrl';
import { requestAnalysisUserRelation } from '@/request/analysis';
import { UserRelationTool } from '@/util/userRelationTool';
import { requestStopBugFixerComputation } from '@/request/computation';
import { analysisMonitor } from '@/util/analysisMonitor';
import MinimapComponent from '@/components/special/analysisPanel/graph/Minimap';
import styles from './DropdownMenu.module.css';

export const FlowToolBar = (props: any) => {
  const {
    showMenu,
    setIsShowMenu,
    showVisual,
    setIsShowAIDashboard,
    showError,
    setShowError,
    isShowMenu,
    isShowVisual,
    isShowAIDashboard,
  } = props;
  const { isFiguresLoaded, setIsFiguresLoaded, isToolbarCollapsed, setIsToolbarCollapsed } =
    useModel('visualPanelControl');
  const {
    instance,
    nodeStatistic,
    nodes,
    errorNodeList,
    autoState,
    setAutoState,
    compactMode,
    setCompactMode,
    analysisDetail,
    setAnalysisDetail,
    analysisAccessType,
    setAnalysisAccessType,
    globalLayout,
    updateAnalysisInfo,
  } = useModel('analysis');
  const { openModal } = useModel('workflowHelper');
  const { dictionary } = useModel('localization');
  const { userInfo, isGuest } = useModel('user');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const { setActiveErrorKey } = useModel('analysis');
  const [isMinimapVisible, setIsMinimapVisible] = useState(false);
  const [inputStatus, setInputStatus] = useState('');
  const [stopping, setStopping] = useState(false);
  const isGuestUser = isGuest();

  const { zoom } = useViewport();

  const getUserRelations = async () => {
    const [analysisId] = getLocationParams(['analysis-id']);

    if (!analysisId) {
      return;
    }

    try {
      const publicAnalysisList = await requestPublicAnalysisList();
      const isPublic = publicAnalysisList.data.some((item) => item.id == analysisId);
      setAnalysisAccessType(
        isPublic && userInfo?.id + '' !== '0' ? AnalysisType.PUBLIC : AnalysisType.PRIVATE,
      );

      const { data: userRelations } = await requestAnalysisUserRelation(analysisId);
      const userRelationTool = new UserRelationTool(userInfo?.id ?? '', userRelations);

      if (!userRelationTool.isReadable()) {
        sessionStorage.setItem('returnUrl', window.location.pathname);
        history.push('/login/byPassword');
        return;
      }

      return {
        canRead: userRelationTool.isReadable(),
        canWrite: userRelationTool.isWritable(),
      };
    } catch (error) {
      console.error('Error fetching user relations:', error);
      message.error('Failed to check access permissions');
    }
  };

  const openOrNotWorkflowGuide = () => {
    const [analysisId, withGuidance] = getLocationParams(['analysis-id', 'with-guidance']);
    if (withGuidance === 'T' && !!analysisId) {
      openModal(analysisId);
    }
  };

  const recordAnalysisOpened = async () => {
    const [analysisId] = getLocationParams(['analysis-id']);
    if (analysisId) {
      try {
        await requestRecordAnalysisOpened(analysisId);
      } catch (error) {
        console.error('Failed to record analysis open time:', error);
      }
    }
  };

  useEffect(() => {
    getUserRelations();
    openOrNotWorkflowGuide();
    recordAnalysisOpened();

    return () => {
      analysisMonitor.pause();
    };
  }, []);

  const handleTransform = () => {
    if (!instance) {
      throw Error('instance is null');
    }
    instance.fitView({ duration: 0 });
  };

  const cancelAllTask = async () => {
    const temData = new URLSearchParams(window.location.search);
    const currentAnalysisId = temData.get('analysis-id');
    if (!currentAnalysisId) {
      message.error('State Exception!');
      return;
    }
    setStopping(true);
    try {
      await requestCancelAllTask(currentAnalysisId);
    } catch (error) {
      message.error('Failed to stop all tasks', error);
    }
    try {
      await requestStopBugFixerComputation(currentAnalysisId);
    } catch (error) {
      message.error('Failed to stop bug fixer computation', error);
    }
    setStopping(false);
  };

  const isFiguresLoadedRef = useRef(isFiguresLoaded);

  useEffect(() => {
    isFiguresLoadedRef.current = isFiguresLoaded;
  }, [isFiguresLoaded]);

  const handleShowPlotChange = async (visible: boolean) => {
    await updateAnalysisInfo({
      figure_visible: visible,
    });
    setAnalysisDetail({ ...analysisDetail, figureVisible: visible });

    if (visible) {
      handleTransform();
      const loadingKey = 'loading';
      message.loading({ content: 'Initializing show plot mode...', key: loadingKey, duration: 0 });

      const loadingTimeout = setTimeout(() => {
        message.destroy(loadingKey);
      }, 5000);

      while (!isFiguresLoadedRef.current) {
        await new Promise((resolve) => setTimeout(resolve, 100));
      }

      clearTimeout(loadingTimeout);
      message.destroy(loadingKey);
    } else {
      const quittingKey = 'quitting';
      message.loading({ content: 'Quitting show plot mode...', key: quittingKey });

      await new Promise((resolve) => setTimeout(resolve, 300));
      message.destroy(quittingKey);
      setIsFiguresLoaded(false);

      handleTransform();
    }
  };

  const handleShowErrorChange = async (hidden: boolean) => {
    const loadingKey = 'hideErrorNode';
    message.loading({
      content: hidden ? 'Hiding error nodes...' : 'Showing error nodes...',
      key: loadingKey,
      duration: 0,
    });

    try {
      await updateAnalysisInfo({
        error_node_hidden: hidden,
      });
      setAnalysisDetail({ ...analysisDetail, errorNodeHidden: hidden });
      message.destroy(loadingKey);
    } catch (error) {
      message.destroy(loadingKey);
      message.error('Failed to update error node visibility');
      console.error('Error updating error node visibility:', error);
    }
  };

  const handleBugFixerCheckboxChange = async (enabled: boolean) => {
    if (!analysisDetail?.maxRetry && enabled) {
      setInputStatus('warning');
      message.warning(
        'Please set a valid maximum number of retries before enabling the bug fixer.',
      );
      return;
    } else {
      setInputStatus('');
      await updateAnalysisInfo({
        bug_fixer_enabled: enabled,
      });
      setAnalysisDetail({ ...analysisDetail, bugFixerEnabled: enabled });
    }
  };

  const updateMaxRetry = async (value: number) => {
    if (value) {
      setInputStatus('');
    } else {
      return;
    }
    const oldValue = analysisDetail?.maxRetry;
    const hide = message.loading('Updating max retry...', 0);
    setAnalysisDetail({ ...analysisDetail, maxRetry: value });
    try {
      await updateAnalysisInfo({
        max_retry: value,
      });
    } catch (error) {
      message.error('Failed to update max retry', error);
      setAnalysisDetail({ ...analysisDetail, maxRetry: oldValue });
    } finally {
      setTimeout(hide, 2);
    }
  };

  const toggleToolbarCollapse = () => {
    setIsToolbarCollapsed(!isToolbarCollapsed);
  };

  const settingOptionsMenu = (
    <Menu>
      <Menu.Item key="showBlockPanel">
        <Checkbox
          checked={isShowMenu}
          style={{
            margin: '5px 5px',
          }}
          onChange={showMenu}
        >
          <span>{dictionary.SHOW_BLOCK_PANEL}</span>
        </Checkbox>
      </Menu.Item>
      <Menu.Item key="showConsolePanel">
        <Checkbox
          checked={isShowVisual}
          style={{
            margin: '5px 5px',
          }}
          onChange={showVisual}
        >
          <span>{dictionary.SHOW_CONSOLE_PANEL}</span>
        </Checkbox>
      </Menu.Item>
      <Menu.Item
        key="autoLayout"
        disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC}
      >
        <Switch
          checked={autoState}
          onChange={() => {
            setAutoState(!autoState);
          }}
          size="small"
          style={{
            margin: '10px 0',
          }}
          disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC}
        />
        <span style={{ marginLeft: 10 }}>{dictionary.AUTO_LAYOUT}</span>
      </Menu.Item>
      <Menu.Item key="showPlot">
        <Switch
          checked={analysisDetail?.figureVisible}
          onChange={() => {
            handleShowPlotChange(!analysisDetail?.figureVisible);
          }}
          size="small"
          style={{
            margin: '10px 0',
          }}
        />
        <span style={{ marginLeft: 10 }}>{dictionary.SHOW_PLOT}</span>
      </Menu.Item>
      <Menu.Item key="hideErrorNode">
        <Switch
          checked={analysisDetail?.errorNodeHidden}
          onChange={() => {
            handleShowErrorChange(!analysisDetail?.errorNodeHidden);
          }}
          size="small"
          style={{
            margin: '10px 0',
          }}
        />
        <span style={{ marginLeft: 10 }}>{dictionary.HIDE_ERROR_NODE}</span>
      </Menu.Item>
      <Menu.Item key="autoFix" disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Switch
            checked={analysisDetail?.bugFixerEnabled}
            onChange={() => {
              handleBugFixerCheckboxChange(!analysisDetail?.bugFixerEnabled);
            }}
            size="small"
            style={{
              margin: '10px 0',
            }}
            disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC}
          />
          <span style={{ marginLeft: 10 }}>{dictionary.AUTO_FIX}</span>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Tooltip title="Set the maximum number of retries for the bug fixer.">
              <InfoCircleOutlined style={{ marginLeft: 10 }} />
            </Tooltip>
            <InputNumber
              size="small"
              min={1}
              max={20}
              value={analysisDetail?.maxRetry}
              onChange={updateMaxRetry}
              status={inputStatus}
              style={{
                width: '50px',
                marginLeft: 10,
              }}
              disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC}
            />
          </div>
        </div>
      </Menu.Item>
      <Menu.Item key="compactMode">
        <Switch
          checked={compactMode}
          onChange={() => {
            setCompactMode(!compactMode);
          }}
          size="small"
          style={{
            margin: '10px 0',
          }}
        />
        <span style={{ marginLeft: 10 }}>{dictionary.COMPACT_MODE}</span>
        <span>
          <Tooltip title="In compact mode, function block nodes take up less screen space.">
            <InfoCircleOutlined style={{ marginLeft: 10 }} />
          </Tooltip>
        </span>
      </Menu.Item>
    </Menu>
  );

  return (
    <div className={`${style.footerContent} ${isToolbarCollapsed ? style.footerCollapsed : ''}`}>
      <div className={style.collapseButton}>
        {isToolbarCollapsed ? (
          <MenuUnfoldOutlined
            className={style.footerIcon}
            onClick={toggleToolbarCollapse}
            title="Expand Toolbar"
          />
        ) : (
          <MenuFoldOutlined
            className={style.footerIcon}
            onClick={toggleToolbarCollapse}
            title="Collapse Toolbar"
          />
        )}
      </div>
      {isToolbarCollapsed ? null : (
        <>
          <div className={style.footerSection}>
            <Badge
              count={errorNodeList.length}
              size="small"
              style={{
                cursor: 'pointer',
                marginRight: '10px',
                fontSize: '1.2vh',
              }}
            >
              <AlertOutlined
                style={{
                  cursor: 'pointer',
                  color: '#262626',
                  padding: '0 8px',
                  fontSize: '1.5vh',
                }}
                onClick={() => {
                  const failed: any[] = [];
                  for (const node of nodes) {
                    if (node.data.state === NodeState.FAILED) {
                      failed.push(node);
                    }
                  }
                  const failedName = failed.map((item) => item.data.label);
                  const errorNodeListName = errorNodeList.map((item) => item.name);
                  if (
                    JSON.stringify(failedName) === JSON.stringify(errorNodeListName) &&
                    failed.length > 0
                  ) {
                    setShowError(!showError);
                    setActiveErrorKey(failed[0].id);
                  }
                }}
              />
            </Badge>
            <Dropdown
              overlay={settingOptionsMenu}
              trigger={['click']}
              open={dropdownOpen}
              onOpenChange={setDropdownOpen}
              placement="bottom"
              overlayClassName={styles.settingMenu}
            >
              <SettingOutlined
                style={{
                  cursor: 'pointer',
                  color: '#262626',
                  padding: '0 8px',
                  fontSize: '1.5vh',
                }}
              />
            </Dropdown>
            <ZoomInOutlined
              style={{
                cursor: 'pointer',
                color: '#262626',
                padding: '0 8px',
                fontSize: '1.5vh',
              }}
              onClick={() => setIsMinimapVisible(!isMinimapVisible)}
            />
            <MinimapComponent nodes={nodes} isMinimapVisible={isMinimapVisible} />
            <AimOutlined
              style={{
                cursor: 'pointer',
                color: '#262626',
                padding: '0 8px',
                fontSize: '1.5vh',
              }}
              onClick={() => {
                handleTransform();
              }}
            />
            <AppstoreOutlined
              className={
                analysisAccessType === AnalysisType.PUBLIC
                  ? style.footerIconDisabled
                  : style.footerIcon
              }
              onClick={() => {
                if (analysisAccessType !== AnalysisType.PUBLIC) {
                  globalLayout();
                }
              }}
            />
            <MinusOutlined
              className={style.footerIcon}
              onClick={(e) => {
                e.stopPropagation();
                instance.zoomOut({ duration: 800 });
              }}
            >
              zoom out
            </MinusOutlined>
            <div style={{ fontSize: '1.5vh', color: '#262626', margin: '0 8px' }}>
              <span>{(zoom * 100).toFixed(0) + '%'}</span>
            </div>
            <PlusOutlined
              className={style.footerIcon}
              onClick={(e) => {
                e.stopPropagation();
                instance.zoomIn({ duration: 800 });
              }}
            >
              zoom in
            </PlusOutlined>
          </div>
          <Divider
            type="vertical"
            style={{
              backgroundColor: '#DEDEDE',
              height: '15px',
              marginRight: '15px',
            }}
          />
          <div className={style.footerSection}>
            <div style={{ fontSize: '1.5vh', whiteSpace: 'nowrap' }}>
              <span
                onClick={() => {
                  setIsShowMenu(!isShowMenu);
                  setIsShowAIDashboard(!isShowAIDashboard);
                }}
              >
                <span>
                  {dictionary.TASK}:{' '}
                  <span
                    style={{
                      textDecoration: isShowAIDashboard ? 'underline' : 'none',
                      color: 'rgba(47, 84, 235, 1)',
                      cursor: 'pointer',
                    }}
                  >
                    {nodeStatistic.total}
                  </span>
                  <span
                    style={{
                      color: 'rgba(47, 84, 235, 1)',
                      cursor: 'pointer',
                    }}
                  >
                    {isShowAIDashboard ? <EyeInvisibleOutlined /> : <EyeOutlined />}
                  </span>
                </span>
              </span>
            </div>
          </div>
          <div className={style.statusContainer}>
            <span className={style.footerStatus}>
              {dictionary.RUNNING}: {nodeStatistic.running}
            </span>
            <span className={style.footerStatus}>
              {dictionary.FAILED}: {nodeStatistic.failed}
            </span>
            <span className={style.footerStatus}>
              {dictionary.SUCCESS}: {nodeStatistic.success}
            </span>
            <span className={style.footerStatus}>
              {dictionary.PENDING}: {nodeStatistic.pending}
            </span>
            <span className={style.footerStatus}>
              {dictionary.DEBUGGING}: {nodeStatistic.debugging}
            </span>

            <div style={{ fontSize: '1.5vh', color: '#5971C0', marginLeft: '10px' }}>
              <Button
                disabled={analysisAccessType === AnalysisType.PUBLIC || stopping}
                icon={<PauseOutlined />}
                type="primary"
                size="small"
                onClick={cancelAllTask}
                style={{
                  fontSize: '1.5vh',
                  height: '3vh',
                }}
              >
                {dictionary.STOP_ALL}
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default FlowToolBar;
