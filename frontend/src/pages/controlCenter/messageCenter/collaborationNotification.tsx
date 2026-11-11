import { useEffect, useRef, useState } from 'react';
import style from '../index.less';
import { Card, Button, Divider, message } from 'antd';
import {
  requestAcceptCollaboration,
  requestAnalysisInvitationList,
  requestRejectCollaboration,
} from '@/request/analysis';
import { InvitationStatus } from '@/interfaces/invitation';
import type { CollaborationInvitation } from '@/interfaces/invitation';
import { useLocation, useModel } from 'umi';

const statusColors = {
  [InvitationStatus.Pending]: 'orange',
  [InvitationStatus.Accepted]: 'green',
  [InvitationStatus.Rejected]: 'red',
};

export default function CollaborationNotification() {
  const location = useLocation();
  const { dictionary } = useModel('localization');
  const firstScrollRef = useRef<boolean>(true);

  const pageRef = useRef<number>(1);
  const [invitationList, setInvitationList] = useState<CollaborationInvitation[]>([]);

  const [loading, setLoading] = useState<boolean>(false);
  const [haveMore, setHaveMore] = useState<boolean>(true);

  const itemRefMap = useRef<Map<number, any>>(new Map());

  const loadCollaborationInivtationList = async () => {
    setLoading(true);
    try {
      const { data: newInvitationList } = await requestAnalysisInvitationList(pageRef.current);
      if (pageRef.current === 1) {
        setInvitationList(newInvitationList);
      } else {
        setInvitationList(invitationList.concat(newInvitationList));
      }
      setHaveMore(newInvitationList.length === 20);
    } catch (e) {
      message.error('Failed to load collaboration invitation list');
    }
    setLoading(false);
  };

  const acceptInvitation = async (invitation_id: string | number, index: number) => {
    try {
      await requestAcceptCollaboration(invitation_id);
      invitationList[index].status = InvitationStatus.Accepted;
      setInvitationList([...invitationList]);
      message.success('Accept Invitation Successfully');
    } catch (e) {
      message.error('Accept Invitation Failed');
    }
  };

  const rejectInvitation = async (invitation_id: string | number, index: number) => {
    try {
      await requestRejectCollaboration(invitation_id);
      invitationList[index].status = InvitationStatus.Rejected;
      setInvitationList([...invitationList]);
      message.success('Reject Invitation Successfully');
    } catch (e) {
      message.error('Reject Invitation Failed');
    }
  };

  useEffect(() => {
    loadCollaborationInivtationList();
  }, []);

  useEffect(() => {
    const invitationId = new URLSearchParams(location.search).get('invitation-id');
    if (!!invitationId && itemRefMap.current.has(+invitationId)) {
      if (!firstScrollRef.current) {
        return;
      }
      firstScrollRef.current = false;
      const ref = itemRefMap.current.get(+invitationId);
      ref?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [location, invitationList]);

  return (
    <div className={style.box}>
      <div className={style.card}>
        <div className={style.title}>{dictionary.COLLABORATION_NOTIFICATION}</div>
        <div className={style.content}>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1em',
              letterSpacing: '1px',
            }}
          >
            {invitationList.map((item: CollaborationInvitation, index) => (
              <div
                key={item.id}
                ref={(ref) => {
                  if (ref) {
                    itemRefMap.current.set(item.id, ref);
                  }
                }}
              >
                <Card
                  title={`${dictionary.COLLABORATION_NOTIFICATION} #${item.id}`}
                  extra={
                    <div
                      style={{
                        fontSize: '0.9em',
                        color: 'grey',
                      }}
                    >
                      {item.createdTime}
                    </div>
                  }
                >
                  <div>
                    <p>
                      <strong>{dictionary.INVITOR}: </strong>
                      {item.inviterName || 'unnamed user'}
                    </p>
                    <p>
                      <strong>{dictionary.TYPE}: </strong>
                      {item.otype || 'unnamed type'}
                    </p>
                    <p>
                      <strong>{dictionary.NAME}: </strong>
                      {item.oname || 'unnamed'}
                    </p>
                    <p>
                      <strong>{dictionary.DESCRIPTION}: </strong>
                      {item.message || 'You are cordially invited to participate in this project!'}
                    </p>
                    <p>
                      <strong>{dictionary.STATUS}: </strong>
                      <span
                        style={{
                          color: statusColors[item.status],
                          textTransform: 'capitalize',
                        }}
                      >
                        {item.status}
                      </span>
                    </p>
                  </div>
                  <Divider />
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <div
                      style={{
                        flex: 1,
                      }}
                    />
                    <Button
                      disabled={item.status !== InvitationStatus.Pending}
                      type="primary"
                      onClick={() => {
                        acceptInvitation(item.id, index);
                      }}
                    >
                      {dictionary.ACCEPT}
                    </Button>
                    <div
                      style={{
                        width: '1em',
                      }}
                    />
                    <Button
                      disabled={item.status !== InvitationStatus.Pending}
                      type="primary"
                      danger
                      onClick={() => {
                        rejectInvitation(item.id, index);
                      }}
                    >
                      {dictionary.REJECT}
                    </Button>
                  </div>
                </Card>
              </div>
            ))}

            {haveMore ? (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '2em',
                }}
              >
                <Button
                  type="link"
                  onClick={() => {
                    pageRef.current++;
                    loadCollaborationInivtationList();
                  }}
                >
                  {loading ? `${dictionary.LOADING}...` : dictionary.SHOW_MORE}
                </Button>
              </div>
            ) : (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  fontSize: '0.9em',
                  color: 'gray',
                }}
              >
                -- {dictionary.NO_MORE} --
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
