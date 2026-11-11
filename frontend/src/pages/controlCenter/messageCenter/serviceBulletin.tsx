import { useEffect, useRef, useState } from 'react';
import style from '../index.less';
import { Card, Modal, Button } from 'antd';
import ReactMarkdown from 'react-markdown';
import type { Announcement, ExpandAnnouncement } from '@/interfaces/inform';
import { requestListAnnouncement } from '@/request/inform';
import { useLocation, useModel } from 'umi';

type DetailsModalProps = {
  announcement: ExpandAnnouncement | null;
  setAnnouncement: (announcement: ExpandAnnouncement | null) => void;
};

const DetailsModal = (props: DetailsModalProps) => {
  const { announcement, setAnnouncement } = props;

  return (
    <Modal
      title={announcement?.content?.title}
      open={!!announcement}
      centered
      width="50vw"
      okButtonProps={{ style: { display: 'none' } }}
      cancelText="Close"
      onCancel={() => {
        setAnnouncement(null);
      }}
    >
      <ReactMarkdown>{announcement?.content?.content}</ReactMarkdown>
    </Modal>
  );
};

export default function ServiceBulletin() {
  const location = useLocation();

  const { dictionary } = useModel('localization');

  const firstScrollRef = useRef<boolean>(true);

  const itemRefMap = useRef<Map<number, any>>(new Map());

  const pageRef = useRef<number>(1);

  const [announcementOnShow, setAnnouncementOnShow] = useState<ExpandAnnouncement | null>(null);

  const [announcementList, setAnnouncementList] = useState<ExpandAnnouncement[]>([]);

  const [haveMore, setHaveMore] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(false);

  const loadAnnouncementList = async () => {
    setLoading(true);
    try {
      const { data: newAnnouncementList } = await requestListAnnouncement(pageRef.current);
      if (pageRef.current === 1) {
        setAnnouncementList(
          newAnnouncementList.map((item: Announcement) => {
            return {
              ...item,
              content: JSON.parse(item.content),
            };
          }),
        );
      } else {
        setAnnouncementList(
          announcementList.concat(
            newAnnouncementList.map((item: Announcement) => {
              return {
                ...item,
                content: JSON.parse(item.content),
              };
            }),
          ),
        );
      }
      setHaveMore(newAnnouncementList.length === 20);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnnouncementList();
  }, []);

  useEffect(() => {
    const announcementId = new URLSearchParams(location.search).get('announcement-id');
    if (!!announcementId && itemRefMap.current.has(+announcementId)) {
      if (firstScrollRef.current) {
        itemRefMap.current.get(+announcementId)?.scrollIntoView({
          behavior: 'smooth',
        });
      }
      firstScrollRef.current = false;
    }
  }, [location, announcementList]);

  return (
    <div className={style.box}>
      <div className={style.card}>
        <div className={style.title}>{dictionary.SERVICE_BULLETIN}</div>
        <DetailsModal announcement={announcementOnShow} setAnnouncement={setAnnouncementOnShow} />
        <div className={style.content}>
          <div
            style={{
              // overflow: 'auto',
              letterSpacing: '1px',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            {announcementList?.map((item) => {
              return (
                <div
                  key={item.id}
                  ref={(ref) => {
                    if (ref) {
                      itemRefMap.current.set(item.id, ref);
                    }
                  }}
                >
                  <Card
                    title={'#' + item.id + ' ' + item.content.title}
                    onClick={() => {
                      setAnnouncementOnShow(item);
                    }}
                    style={{
                      marginBottom: 10,
                      cursor: 'pointer',
                    }}
                    extra={
                      <div
                        style={{
                          color: 'gray',
                          fontSize: '0.9em',
                        }}
                      >
                        {item.createdTime}
                      </div>
                    }
                  >
                    <ReactMarkdown>{item.content.content}</ReactMarkdown>
                  </Card>
                </div>
              );
            })}
            <div>
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
                      loadAnnouncementList();
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
                  <span>-- {dictionary.NO_MORE} --</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
