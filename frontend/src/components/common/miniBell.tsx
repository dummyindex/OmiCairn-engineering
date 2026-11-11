import { Badge, Drawer, Empty, Button, message, Segmented, Pagination, Select, Spin } from 'antd';
import { BellOutlined, ReloadOutlined } from '@ant-design/icons';
import { type Announcement, InformCate, InformType, type Notice } from '@/interfaces/inform';
import { history } from 'umi';
import { requestReadAnnouncement, requestReadInform } from '@/request/inform';
import { requestNodeListByIdx } from '@/request/node';
import { useModel } from 'umi';
import { requestAcceptCollaboration, requestRejectCollaboration } from '@/request/analysis';
import { InvitationStatus } from '@/interfaces/invitation';
import { useState } from 'react';

type AnalysisCollaborationNoticeProps = {
  informId: number | string;
  createdTime: string;
  payload: any;
};

const AnalysisCollaborationNotice = (props: AnalysisCollaborationNoticeProps) => {
  const { dictionary } = useModel('localization');
  const { informId, createdTime, payload } = props;
  const { invitation_id: invitationId, invitation_status: invitationStatus } = payload;

  const [isOperating, setIsOperating] = useState(false);

  if (invitationStatus === InvitationStatus.Cancelled) {
    return null;
  }

  const readInform = async () => {
    if (!informId) return;
    await requestReadInform([informId]);
  };

  const acceptInvitation = async () => {
    try {
      setIsOperating(true);
      await requestAcceptCollaboration(invitationId);
    } catch (e) {
      message.error('Accept Invitation Failed');
    } finally {
      setIsOperating(false);
    }
  };

  const rejectInvitation = async () => {
    setIsOperating(true);
    try {
      await requestRejectCollaboration(invitationId);
    } catch (e) {
      message.error('Reject Invitation Failed');
    } finally {
      setIsOperating(false);
    }
  };

  return (
    <div
      style={{
        fontSize: '1em',
        margin: '10px',
        borderLeft: '1px solid #1890ff',
        padding: '3px 10px',
      }}
    >
      <div>You received a collaboration invitation#{invitationId}.</div>
      <div
        style={{
          height: '1em',
        }}
      />
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '0.5rem',
        }}
      >
        <Button
          size="small"
          type="default"
          style={{
            fontSize: '0.9em',
          }}
          onClick={() => {
            readInform();
            history.push(
              `/controlCenter/messageCenter/collaborationNotification?invitation-id=${invitationId}`,
            );
          }}
        >
          {dictionary.DETAILS}
        </Button>
        {[InvitationStatus.Accepted, InvitationStatus.Rejected].includes(invitationStatus) && (
          <Button disabled size="small" type="default">
            {invitationStatus === InvitationStatus.Accepted ? 'Accepted' : 'Rejected'}
          </Button>
        )}
        {![InvitationStatus.Accepted, InvitationStatus.Rejected].includes(invitationStatus) && (
          <>
            <Button
              size="small"
              type="primary"
              style={{
                fontSize: '0.9em',
              }}
              onClick={acceptInvitation}
              loading={isOperating}
            >
              {dictionary.ACCEPT}
            </Button>
            <Button
              size="small"
              type="primary"
              danger
              style={{
                fontSize: '0.9em',
              }}
              onClick={rejectInvitation}
              loading={isOperating}
            >
              {dictionary.REJECT}
            </Button>
          </>
        )}
        <div
          style={{
            flex: 1,
          }}
        />
        <div
          style={{
            fontSize: '0.9em',
            color: 'gray',
          }}
        >
          {createdTime}
        </div>
      </div>
    </div>
  );
};

type ComputationEndNoticeProps = {
  informId: number | string;
  createdTime: string;
  payload: {
    computation_id: number | string;
    node_id: number | string;
    success: boolean;
  };
};

const ComputationEndNotice = (props: ComputationEndNoticeProps) => {
  const { dictionary } = useModel('localization');
  const { informId, createdTime, payload } = props;
  const { node_id: nodeId, success } = payload;
  const leftBorderColor = success ? '#52c41a' : '#f5222d';

  const readInform = async () => {
    if (!informId) return;
    await requestReadInform([informId]);
  };

  const loadTargetInfo = async () => {
    try {
      const {
        data: [node],
      } = await requestNodeListByIdx([+nodeId]);

      if (!node || !node.analysisId) {
        console.error('Node or analysisId not found.');
        return;
      }

      const { analysisId } = node;
      history.push(`/analysisPanel/flowPanel?analysis-id=${analysisId}&nodeId=${nodeId}`);
    } catch (error) {
      console.error('Error fetching node information:', error);
      return;
    }
  };

  return (
    <div
      style={{
        fontSize: '1em',
        margin: '10px',
        borderLeft: `1px solid ${leftBorderColor}`,
        padding: '3px 10px',
      }}
    >
      <div>Your computation has been {success ? 'successful' : 'failed'}.</div>
      <div
        style={{
          height: '1em',
        }}
      />
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-start',
          alignItems: 'center',
          gap: '0.5rem',
        }}
      >
        <Button
          size="small"
          type="primary"
          style={{
            fontSize: '0.9em',
          }}
          onClick={() => {
            readInform();
            loadTargetInfo();
          }}
        >
          {dictionary.DETAILS}
        </Button>
        <Button
          size="small"
          type="default"
          style={{
            fontSize: '0.9em',
          }}
          onClick={() => {
            readInform();
            history.push('/controlCenter/messageCenter/analysisProgressNotification');
          }}
        >
          {dictionary.VIEW_ALL}
        </Button>
        <div
          style={{
            flex: 1,
          }}
        />
        <div
          style={{
            fontSize: '0.9em',
            color: 'gray',
          }}
        >
          {createdTime}
        </div>
      </div>
    </div>
  );
};

type InformationCompletionProps = {
  informId: number | string;
  createdTime: string;
  payload: {
    lack_of_info: string[];
  };
};

const InformationCompletion = (props: InformationCompletionProps) => {
  const { informId, createdTime, payload } = props;
  const { dictionary } = useModel('localization');
  const { lack_of_info: lackOfInfo } = payload;

  const readInform = async () => {
    if (!informId) return;
    await requestReadInform([informId]);
  };

  return (
    <div
      style={{
        fontSize: '1em',
        margin: '10px',
        borderLeft: '1px solid #faad14',
        padding: '3px 10px',
      }}
    >
      <div>
        Please complete the following information: {lackOfInfo.map((item) => `#${item}`).join(', ')}
      </div>
      <div
        style={{
          height: '1em',
        }}
      />
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Button
          size="small"
          type="primary"
          style={{
            fontSize: '0.9em',
          }}
          onClick={() => {
            readInform();
            history.push('/controlCenter/userCenter/nameSetting');
          }}
        >
          {dictionary.EDIT}
        </Button>
        <div
          style={{
            fontSize: '0.9em',
            color: 'gray',
          }}
        >
          {createdTime}
        </div>
      </div>
    </div>
  );
};

type SystemAnnouncementProps = {
  announcementId: number | string;
  createdTime: string;
  removeUnreadInform: (id: number | string, cate: string) => void;
  payload: {
    title: string;
    content: string;
  };
};

const SystemAnnouncement = (props: SystemAnnouncementProps) => {
  const { dictionary } = useModel('localization');
  const { announcementId, createdTime, payload, removeUnreadInform } = props;
  const { title } = payload;

  const readAnnouncement = async () => {
    if (!announcementId) return;
    await requestReadAnnouncement(announcementId);
    removeUnreadInform(announcementId, InformCate.Announcement);
  };

  return (
    <div
      style={{
        fontSize: '1em',
        margin: '10px',
        borderLeft: '1px solid grey',
        padding: '3px 10px',
      }}
    >
      <div>
        #{announcementId} {title}
      </div>
      <div
        style={{
          height: '1em',
        }}
      />
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Button
          size="small"
          type="primary"
          style={{
            fontSize: '0.9em',
          }}
          onClick={() => {
            readAnnouncement();
            history.push(
              `/controlCenter/messageCenter/serviceBulletin?announcement-id=${announcementId}`,
            );
          }}
        >
          {dictionary.VIEW}
        </Button>
        <div
          style={{
            fontSize: '0.9em',
            color: 'gray',
          }}
        >
          {createdTime}
        </div>
      </div>
    </div>
  );
};

type MiniBellProps = {
  color?: string;
};

const MiniBell = (props: MiniBellProps) => {
  const { color } = props;
  const iconColor = color || 'white';
  const {
    unreadCount,
    unreadAnnouncementList,
    unreadNoticeList,
    removeUnreadInform,
    loading,
    drawerVisible,
    setDrawerVisible,
    pagination,
    handlePaginationChange,
    refreshUnreadInformList,
    refreshUnreadAnnouncementList,
  } = useModel('inform');
  const { dictionary } = useModel('localization');
  const [activeSegment, setActiveSegment] = useState<string>('Notification');
  const [selectedType, setSelectedType] = useState<string | null>(null);

  const renderNoticeItems = () => {
    const filteredNotices = selectedType
      ? unreadNoticeList.filter((notice: Notice) => notice.type === selectedType)
      : unreadNoticeList;

    if (loading) {
      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <Spin size="small" />
        </div>
      );
    }

    if (!filteredNotices.length) {
      return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={dictionary.EMPTY_LIST} />;
    }

    return (
      <>
        {filteredNotices.map((notice: Notice) => {
          const { id, type, createdTime, payload } = notice;
          const payloadObj = JSON.parse(payload);
          switch (type) {
            case InformType.AnalysisCollaborationInvitation:
              return (
                <AnalysisCollaborationNotice
                  informId={id}
                  key={id}
                  createdTime={createdTime}
                  payload={payloadObj}
                />
              );
            case InformType.ComputationEndNotice:
              return (
                <ComputationEndNotice
                  informId={id}
                  key={id}
                  createdTime={createdTime}
                  payload={payloadObj}
                />
              );
            case InformType.InformationCompletionNotice:
              return (
                <InformationCompletion
                  informId={id}
                  key={id}
                  createdTime={createdTime}
                  payload={payloadObj}
                />
              );
            default:
              return null;
          }
        })}
      </>
    );
  };

  const renderAnnouncementItems = () => {
    if (loading) {
      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <Spin size="small" />
        </div>
      );
    }

    if (!unreadAnnouncementList?.length) {
      return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={dictionary.EMPTY_LIST} />;
    }

    return (
      <>
        {unreadAnnouncementList.map((announcement: Announcement) => {
          const { id, createdTime, content } = announcement;
          const payloadObj = JSON.parse(content);
          return (
            <SystemAnnouncement
              announcementId={id}
              key={id}
              createdTime={createdTime}
              payload={payloadObj}
              removeUnreadInform={removeUnreadInform}
            />
          );
        })}
      </>
    );
  };

  const handleManualRefresh = async () => {
    if (activeSegment === 'Notification') {
      await refreshUnreadInformList();
    }
    if (activeSegment === 'Announcement') {
      await refreshUnreadAnnouncementList();
    }
  };

  const notificationContent = (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '10px 5px' }}>
        <Segmented
          options={[
            { label: 'Notification', value: 'Notification' },
            { label: 'Announcement', value: 'Announcement' },
          ]}
          value={activeSegment}
          onChange={(value) => setActiveSegment(value as string)}
          block
        />
      </div>

      {activeSegment === 'Notification' && (
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '10px' }}>
          <Select
            placeholder="Filter by Type"
            style={{ width: '95%' }}
            onChange={(value) => setSelectedType(value)}
            allowClear
          >
            {Object.keys(InformType).map((key) => (
              <Select.Option key={key} value={InformType[key]}>
                {dictionary[key]}
              </Select.Option>
            ))}
          </Select>
        </div>
      )}

      {activeSegment === 'Notification' ? renderNoticeItems() : renderAnnouncementItems()}

      <div
        style={{
          padding: '10px 10px 15px 15px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        {activeSegment === 'Notification' &&
          pagination.total &&
          pagination.total > pagination.pageSize && (
            <Pagination
              size="small"
              current={pagination.current}
              pageSize={pagination.pageSize}
              total={pagination.total}
              onChange={handlePaginationChange}
              onShowSizeChange={(current, size) => handlePaginationChange(1, size)}
              showSizeChanger={true}
              pageSizeOptions={['5', '10', '20', '50']}
              showQuickJumper={false}
              disabled={loading}
              showTotal={(total) =>
                `${dictionary.TOTAL || 'Total'} ${total} ${dictionary.ITEMS || 'items'}`
              }
            />
          )}
      </div>
    </div>
  );
  return (
    <>
      <Badge dot={unreadCount > 0} count={unreadCount > 0 ? unreadCount : 0}>
        <BellOutlined
          style={{
            color: iconColor,
            fontSize: '1.5vh',
            cursor: 'pointer',
          }}
          onClick={() => setDrawerVisible(true)}
        />
      </Badge>
      <Drawer
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{dictionary.NOTIFICATIONS}</span>
            <Button
              icon={<ReloadOutlined />}
              size="small"
              onClick={handleManualRefresh}
              disabled={loading}
            >
              {dictionary.REFRESH}
            </Button>
          </div>
        }
        placement="right"
        closable
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        width={400}
        bodyStyle={{ padding: '0px', height: 'calc(100% - 55px)' }}
      >
        {notificationContent}
      </Drawer>
    </>
  );
};

export default MiniBell;
