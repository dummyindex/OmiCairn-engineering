import type { DataType } from '@/interfaces/data';
import {
  requestAnalysisCreate,
  requestAnalysisList,
  requestAnalysisUserRelation,
  requestCopyAnalysis,
  requestDeleteAnalysis,
  requestEditAnalysis,
  requestPublicAnalysisList,
  requestToggleAnalysisPublishState,
} from '@/request/analysis';
import { formatTimeTool } from '@/util/formatTimeTool';
import { writeToClipboard } from '@/util/operationTools';
import { UserRelationTool } from '@/util/userRelationTool';
import {
  CloseCircleOutlined,
  CopyOutlined,
  CrownOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  FormOutlined,
  PlusOutlined,
  QuestionCircleOutlined,
  ShareAltOutlined,
  UsergroupAddOutlined,
} from '@ant-design/icons';
import {
  Button,
  Checkbox,
  Divider,
  Form,
  Input,
  message,
  Modal,
  Popconfirm,
  Popover,
  Space,
  Switch,
  Tag,
  Tooltip,
} from 'antd';
import { useEffect, useState } from 'react';
import { history, useModel } from 'umi';
import CollaborativeUserListModal from './collaborativeUserListModal';
import style from './index.less';

interface EditFormProps {
  item: DataType;
  onSubmit: (id: string, values: any) => Promise<void>;
}

const { Search } = Input;

type PermissionType = 'admin' | 'write' | 'read';

const PermissionIcon = ({ permission }: { permission: PermissionType | null }) => {
  if (!permission) return null;

  const iconStyle = { fontSize: '14px', marginLeft: '8px' };

  switch (permission) {
    case 'admin':
      return (
        <Tooltip title="Permission Level: Owner">
          <CrownOutlined style={{ ...iconStyle, color: '#f39c12' }} />
        </Tooltip>
      );
    case 'write':
      return (
        <Tooltip title="Permission Level: Editor">
          <EditOutlined style={{ ...iconStyle, color: '#27ae60' }} />
        </Tooltip>
      );
    case 'read':
      return (
        <Tooltip title="Permission Level: Read Only">
          <EyeOutlined style={{ ...iconStyle, color: '#3498db' }} />
        </Tooltip>
      );
    default:
      return null;
  }
};

const CreateAnalysisForm = (props: any) => {
  const { dictionary } = useModel('localization');
  const { form } = props;
  return (
    <Form
      form={form}
      labelAlign="left"
      labelCol={{ span: 7 }}
      wrapperCol={{ span: 17 }}
      autoComplete="off"
    >
      <Form.Item label={dictionary.NAME} required key="name" name="name">
        <Input />
      </Form.Item>
      <Form.Item
        label={dictionary.DESCRIPTION}
        required={false}
        key="description"
        name="description"
      >
        <Input multiple />
      </Form.Item>
      <Form.Item
        label={dictionary.GUIDANCE}
        required={false}
        key="withGuidance"
        name="withGuidance"
      >
        <Switch />
      </Form.Item>
    </Form>
  );
};

const EditForm = (props: EditFormProps) => {
  const { item, onSubmit } = props;
  const { dictionary } = useModel('localization');
  const onFinish = async (values: any) => {
    await onSubmit(item.id, values);
  };
  return (
    <Form
      name="basic"
      labelCol={{ span: 8 }}
      wrapperCol={{ span: 16 }}
      style={{ maxWidth: 600 }}
      initialValues={{ remember: true }}
      onFinish={onFinish}
      autoComplete="off"
    >
      <Form.Item label="name" name="name" initialValue={item.name}>
        <Input />
      </Form.Item>
      <Form.Item label="description" name="description" initialValue={item.description}>
        <Input
          allowClear={{
            clearIcon: <CloseCircleOutlined />,
          }}
        />
      </Form.Item>
      <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
        <Button type="primary" htmlType="submit">
          {dictionary.SUBMIT}
        </Button>
      </Form.Item>
    </Form>
  );
};

const CopyAnalysisForm = (props: any) => {
  const { form } = props;
  return (
    <Form
      form={form}
      labelAlign="right"
      labelCol={{ span: 4 }}
      wrapperCol={{ span: 20 }}
      autoComplete="off"
    >
      <Form.Item label="name" required key="name" name="name">
        <Input />
      </Form.Item>
      <Form.Item label="description" required={false} key="description" name="description">
        <Input multiple />
      </Form.Item>
    </Form>
  );
};

const ShareModal = (props: any) => {
  const { shareAnalysisId, setShareAnalysisId } = props;
  const [isPublic, setIsPublic] = useState<boolean>(false);
  const [isShareStateLoading, setIsShareStateLoading] = useState<boolean>(false);

  const { userInfo } = useModel('user');
  const { dictionary } = useModel('localization');

  const getDefaultPublic = async () => {
    if (shareAnalysisId && !!userInfo) {
      setIsShareStateLoading(true);
      const { data: result } = await requestAnalysisUserRelation(shareAnalysisId);
      if (!result) {
        throw Error('Fail to fetch relation list');
      }

      const userRelationTool = new UserRelationTool(userInfo.id, result);

      setIsShareStateLoading(false);
      setIsPublic(userRelationTool.isPublished());
    }
  };

  useEffect(() => {
    if (shareAnalysisId && !!userInfo) {
      getDefaultPublic();
    }
  }, [shareAnalysisId, userInfo]);

  const publicDatasetChange = async (checked: boolean) => {
    setIsShareStateLoading(true);
    await requestToggleAnalysisPublishState(shareAnalysisId, checked);
    setIsShareStateLoading(false);
    setIsPublic(checked);
  };
  return (
    <Modal
      centered
      title={dictionary.SHARE}
      open={!!shareAnalysisId}
      footer={null}
      onCancel={() => setShareAnalysisId(null)}
    >
      <div style={{ marginBottom: '20px' }}>
        {dictionary.PUBLIC} :{' '}
        <Switch checked={isPublic} onChange={publicDatasetChange} loading={isShareStateLoading} />
      </div>
      <Button
        size="small"
        onClick={() => {
          const host = window.location.host;

          const protocol = window.location.protocol;

          writeToClipboard(
            `${protocol}//${host}/analysisPanel/flowPanel?analysis-id=${shareAnalysisId}`,
          )
            .then(() => {
              message.success('Link copied');
            })
            .catch(() => {
              console.error('Link cannot be copied');
            });
        }}
        style={{ fontSize: '12px' }}
      >
        <CopyOutlined />
        {dictionary.COPY_LINK}
      </Button>
    </Modal>
  );
};

const AnalysisList = (props: any) => {
  const { dictionary } = useModel('localization');
  const { isGuest } = useModel('user');
  const isGuestUser = isGuest();

  const {
    onCreateNewTask,
    analysisList,
    onJump,
    onEditCooperator,
    onEdit,
    onStartCopy,
    onStartShare,
    onDelete,
    latestVisitTimeVisible,
    showSort,
    isSortedByAccessTime,
    onSortChange,
    showPermissionIcon,
  } = props;

  return (
    <div className={style.contentBox}>
      <div className={style.titleContainer}>
        <div className={style.miniTitle}>{props.miniTitle}</div>
        {showSort && (
          <div className={style.sortControl}>
            {dictionary.SORT_BY_LAST_ACCESSED_TIME}{' '}
            <Checkbox
              checked={isSortedByAccessTime}
              onChange={onSortChange}
              disabled={isGuestUser}
            />
          </div>
        )}
      </div>
      <Space size={[8, 16]} wrap>
        {onCreateNewTask && (
          <div
            className={`${style.createNewTask} ${isGuestUser ? style.disabledCreateTask : ''}`}
            onClick={isGuestUser ? undefined : onCreateNewTask}
            style={{
              display: 'flex',
              flexDirection: 'column',
              position: 'relative',
              cursor: isGuestUser ? 'not-allowed' : 'pointer',
            }}
          >
            <div style={{ marginBottom: '3vh' }} />
            <PlusOutlined
              style={{
                fontSize: '40px',
                marginBottom: '4vh',
              }}
            />
            <span>{dictionary.CREATE_NEW_ANALYSIS_TASK}</span>
          </div>
        )}

        {analysisList.map((item: any) => {
          const permission = item.permission as PermissionType | null;

          return (
            <div key={item.id}>
              <div className={style.listSubitems}>
                <div className={style.subitemsManage} style={{ position: 'relative' }}>
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '0',
                      left: '1vw',
                    }}
                  >
                    <div
                      className={style.subitemsDescribeBox}
                      style={{
                        fontSize: '14px',
                        fontWeight: '600',
                        color: '#000',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      {item.name}
                      {showPermissionIcon && <PermissionIcon permission={permission} />}
                      {item.creationSource === 'chatbot' && (
                        <Tag
                          color="blue"
                          style={{
                            marginLeft: '8px',
                            fontSize: '10px',
                            height: '18px',
                            lineHeight: '16px',
                          }}
                        >
                          Chatbot generated
                        </Tag>
                      )}
                    </div>
                    {!latestVisitTimeVisible && (
                      <div
                        className={style.subitemsDescribeBox}
                        style={{
                          fontWeight: '300',
                          fontSize: '12px',
                          color: '#838588',
                        }}
                      >
                        {/* Last accessed time */}
                        {dictionary.CREATED_AT}: {formatTimeTool(item.createdTime)}
                      </div>
                    )}
                    {latestVisitTimeVisible && (
                      <div
                        className={style.subitemsDescribeBox}
                        style={{
                          fontWeight: '300',
                          fontSize: '12px',
                          color: '#838588',
                        }}
                      >
                        {/* Last accessed time */}
                        {dictionary.LAST_VISITED_AT}: {item.latestVisitTime}
                      </div>
                    )}
                  </div>
                </div>
                <div className={style.subitemsButton}>
                  <div className={style.optionButton} onClick={() => onJump(item.id)}>
                    {dictionary.OPEN}
                  </div>
                  <div style={{ flex: 2 }} />
                  {onEditCooperator && (
                    <UsergroupAddOutlined
                      onClick={() => onEditCooperator(item.id)}
                      className={style.iconButton}
                    />
                  )}

                  {onEdit && (
                    <Popover content={<EditForm item={item} onSubmit={onEdit} />}>
                      <FormOutlined className={style.iconButton} />
                    </Popover>
                  )}

                  <CopyOutlined
                    onClick={(e: any) => {
                      if (isGuestUser) return;
                      e.stopPropagation();
                      onStartCopy(item.id);
                    }}
                    className={`${style.iconButton} ${isGuestUser ? style.disabledIcon : ''}`}
                    style={{ cursor: isGuestUser ? 'not-allowed' : 'pointer' }}
                  />

                  {onDelete && (
                    <Popconfirm
                      title="Delete the analysis"
                      description="Are you sure to delete this analysis?"
                      icon={
                        <QuestionCircleOutlined
                          style={{
                            color: 'red',
                          }}
                        />
                      }
                      onConfirm={() => onDelete(item.id)}
                    >
                      <DeleteOutlined
                        onClick={(e) => {
                          e.stopPropagation();
                        }}
                        className={style.iconButton}
                      />
                    </Popconfirm>
                  )}
                  <ShareAltOutlined
                    onClick={(e: any) => {
                      if (isGuestUser) return;
                      e.stopPropagation();
                      onStartShare(item.id);
                    }}
                    className={`${style.iconButton} ${isGuestUser ? style.disabledIcon : ''}`}
                    style={{ cursor: isGuestUser ? 'not-allowed' : 'pointer' }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </Space>
    </div>
  );
};

export default function Home() {
  const [publicAnalysisList, setPublicAnalysisList] = useState<any[]>([]);
  const [isSortedByAccessTime, setIsSortedByAccessTime] = useState<boolean>(false);
  const [analysisList, setAnalysisList] = useState<any[]>([]);
  const {
    setNodeId,
    setDataId,
    setNodeInfo,
    setIsAiRepoGenSelected,
    setIsShowAIDashboard,
    setIsShowMenu,
    setIsShowVisual,
  } = useModel('visualPanelControl');
  const { dictionary } = useModel('localization');
  const { setShiftKey, setCurrentSelectedNodes } = useModel('analysis');
  const [filteredPublicList, setFilteredPublicList] = useState<any[]>([]);
  const [filteredPrivateList, setFilteredPrivateList] = useState<any[]>([]);

  const onSearch = (value: string) => {
    const filteredPublic = publicAnalysisList.filter((analysis) =>
      analysis.name.toLowerCase().includes(value.toLowerCase()),
    );
    setFilteredPublicList(filteredPublic);

    const filteredPrivate = analysisList.filter((analysis) =>
      analysis.name.toLowerCase().includes(value.toLowerCase()),
    );
    setFilteredPrivateList(filteredPrivate);
  };

  const refreshPublicAnalysisList = async () => {
    const { data } = await requestPublicAnalysisList();
    setPublicAnalysisList(data);
  };

  const refreshAnalysisList = async () => {
    let { data: newAnalysisList } = await requestAnalysisList();
    if (isSortedByAccessTime) {
      newAnalysisList = newAnalysisList.sort((a, b) => {
        return new Date(b.latestVisitTime).getTime() - new Date(a.latestVisitTime).getTime();
      });
    }
    setAnalysisList(newAnalysisList);
  };

  useEffect(() => {
    refreshPublicAnalysisList();
    refreshAnalysisList();
  }, [isSortedByAccessTime]);

  useEffect(() => {
    setFilteredPublicList(publicAnalysisList);
    setFilteredPrivateList(analysisList);
  }, [publicAnalysisList, analysisList]);

  const [form] = Form.useForm();
  const [copyAnalysisForm] = Form.useForm();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [copiedAnalysisId, setCopiedAnalysisId] = useState<string | number | null>(null);
  const [shareAnalysisId, setShareAnalysisId] = useState<string | number | null>(null);
  const [copying, setCopying] = useState(false);
  const [cooperatorEditAnalysisId, setCooperatorEditAnalysisId] = useState<string | number | null>(
    null,
  );

  const createNewTaskCancel = () => {
    setIsCreateModalOpen(false);
  };

  const createNewTask = () => {
    setIsCreateModalOpen(true);
  };

  const confirmCreation = async () => {
    const { name, description, withGuidance } = form.getFieldsValue();
    const { code, data: newAnalysis } = await requestAnalysisCreate(name, description, 'manual');
    if (code === 200) {
      history.push(
        `/analysisPanel/flowPanel?with-guidance=${withGuidance ? 'T' : 'F'}&analysis-id=${
          newAnalysis.id
        }`,
      );
      return;
    }
  };

  const goAnalysisPanel = (item: string) => {
    setIsAiRepoGenSelected(false);
    setDataId('');
    setNodeId('');
    setIsShowAIDashboard(false);
    setIsShowMenu(true);
    setIsShowVisual(true);
    setShiftKey(false);
    setCurrentSelectedNodes([]);
    setNodeInfo({ type: null, tag: null, state: null, fbId: null });
    history.push(`/analysisPanel/flowPanel?analysis-id=${item}`);
  };

  const editAnalysis = async (id: string, values: any) => {
    await requestEditAnalysis(id, values);
    refreshAnalysisList();
  };

  const deleteAnalysis = async (id: string) => {
    await requestDeleteAnalysis(id);
    refreshAnalysisList();
  };

  const confirmCopy = async () => {
    if (!copiedAnalysisId) {
      message.error('No analysis to copy');
      return;
    }
    setCopying(true);
    try {
      const { name, description } = copyAnalysisForm.getFieldsValue();
      await requestCopyAnalysis(copiedAnalysisId + '', name, description);
    } catch (e) {
      console.error(e);
    }
    setCopying(false);
    // TODO: submit
    setCopiedAnalysisId(null);
    await refreshAnalysisList();
  };

  return (
    <div className={style.homeMain}>
      <Search
        placeholder={dictionary.SEARCH}
        allowClear
        onSearch={onSearch}
        onChange={(e) => onSearch(e.target.value)}
        size="large"
        style={{
          width: '40vw',
          height: '60px',
        }}
      />
      <div className={style.listName}>
        <div className={style.analysis}>{dictionary.ANALYSIS_TASK}</div>
      </div>
      <div className={style.content}>
        <Divider />
        <AnalysisList
          miniTitle={dictionary.PUBLIC}
          analysisList={filteredPublicList}
          onJump={goAnalysisPanel}
          onStartCopy={setCopiedAnalysisId}
          onStartShare={setShareAnalysisId}
          showPermissionIcon={false}
        />
        <Divider />
        <AnalysisList
          miniTitle={dictionary.PRIVATE}
          showSort={true}
          isSortedByAccessTime={isSortedByAccessTime}
          onSortChange={() => setIsSortedByAccessTime(!isSortedByAccessTime)}
          onCreateNewTask={createNewTask}
          analysisList={filteredPrivateList}
          latestVisitTimeVisible
          onJump={goAnalysisPanel}
          onEditCooperator={setCooperatorEditAnalysisId}
          onEdit={editAnalysis}
          onStartCopy={setCopiedAnalysisId}
          onStartShare={setShareAnalysisId}
          onDelete={deleteAnalysis}
          showPermissionIcon={true}
        />
        <Divider />
      </div>
      <Modal
        centered
        title={dictionary.CREATE_NEW_ANALYSIS_TASK}
        open={isCreateModalOpen}
        okText={dictionary.CREATE}
        cancelText={dictionary.CANCEL}
        onOk={confirmCreation}
        onCancel={createNewTaskCancel}
      >
        <CreateAnalysisForm form={form} />
      </Modal>
      <ShareModal shareAnalysisId={shareAnalysisId} setShareAnalysisId={setShareAnalysisId} />
      <Modal
        centered
        title={dictionary.COPY}
        open={copiedAnalysisId}
        confirmLoading={copying}
        okText={dictionary.COPY}
        cancelText={dictionary.CANCEL}
        onOk={() => {
          confirmCopy();
        }}
        onCancel={() => setCopiedAnalysisId(null)}
      >
        <CopyAnalysisForm form={copyAnalysisForm} />
      </Modal>
      <CollaborativeUserListModal
        cooperatorEditAnalysisId={cooperatorEditAnalysisId}
        setCooperatorEditAnalysisId={setCooperatorEditAnalysisId}
      />
    </div>
  );
}
