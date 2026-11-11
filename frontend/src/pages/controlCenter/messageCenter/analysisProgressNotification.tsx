import { InformType, type Notice, type ExpandComputationEndNotice } from '@/interfaces/inform';
import style from '../index.less';
import { Card, Divider, Button } from 'antd';
import { useEffect, useState, useRef } from 'react';
import { history, useModel } from 'umi';
import { requestListInform, requestReadInform } from '@/request/inform';
import { requestNodeListByIdx } from '@/request/node';

export default function AnalysisProgressNotification() {
  const pageRef = useRef(1);
  const { dictionary } = useModel('localization');
  const [informList, setInformList] = useState<ExpandComputationEndNotice[]>([]);
  const [loading, setLoading] = useState(false);
  const [haveMore, setHaveMore] = useState(true);

  const loadComponentEndInformList = async () => {
    const { data } = await requestListInform(pageRef.current, InformType.ComputationEndNotice);
    if (pageRef.current === 1) {
      setInformList(
        (data || []).map((item: Notice) => {
          return {
            ...item,
            payload: JSON.parse(item.payload),
          };
        }),
      );
    } else {
      setInformList(
        (informList || []).concat(
          (data || []).map((item: Notice) => {
            return {
              ...item,
              payload: JSON.parse(item.payload),
            };
          }),
        ),
      );
    }
    setHaveMore((data || []).length === 20);
    await requestReadInform((data || []).map((item: Notice) => item.id));
  };

  const loadMore = async () => {
    setLoading(true);
    pageRef.current += 1;
    try {
      await loadComponentEndInformList();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const goToPanel = async (nodeId: number | string) => {
    if (!nodeId) return;
    const {
      data: [node],
    } = await requestNodeListByIdx([+nodeId]);
    const { analysisId } = node;
    history.push(`/analysisPanel/flowPanel?analysis-id=${analysisId}&nodeId=${nodeId}`);
  };

  useEffect(() => {
    loadComponentEndInformList();
  }, []);

  return (
    <div className={style.box}>
      <div className={style.card}>
        <div className={style.title}>{dictionary.ANALYSIS_PROGRESS_NOTIFICATION}</div>
        <div className={style.content}>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              letterSpacing: '1px',
            }}
          >
            {informList.map((item: ExpandComputationEndNotice) => {
              return (
                <div key={item.id}>
                  <Card
                    title={`${dictionary.COMPUTATION_END}#${item.payload.computation_id}`}
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
                    <p>
                      <strong>{dictionary.COMPUTATION_ID}: </strong> {item.payload.computation_id}
                    </p>
                    <p>
                      <strong>{dictionary.NODE_ID}: </strong> {item.payload.node_id}
                    </p>
                    <p>
                      <strong>{dictionary.SUCCESS}: </strong>{' '}
                      <span
                        style={{
                          color: item.payload.success ? 'green' : 'red',
                        }}
                      >
                        {item.payload.success ? 'Yes' : 'No'}
                      </span>
                    </p>
                    <p>
                      <strong>{dictionary.ERROR_MESSAGE}: </strong>{' '}
                      {item.payload.error_description || 'None'}
                    </p>
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
                        // size="normal"
                        type="primary"
                        style={{
                          fontSize: '0.9em',
                        }}
                        onClick={() => {
                          goToPanel(item.payload.node_id);
                        }}
                      >
                        {dictionary.VIEW_IN_PANEL}
                      </Button>
                    </div>
                  </Card>
                </div>
              );
            })}
            {haveMore && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                }}
              >
                <Button type="link" loading={loading} onClick={loadMore}>
                  {dictionary.SHOW_MORE}
                </Button>
              </div>
            )}
            {!haveMore && (
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
  );
}
