import { useModel } from 'umi';
import { Modal, Button, Tabs, Image, Empty, Spin } from 'antd';
import { useState, useEffect } from 'react';
import { loadFigure } from '@/request/figure';

const Figure = ({ figureUuid }: { figureUuid: string }) => {
  const [base64String, setBase64String] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const fetchFigure = async () => {
    try {
      setLoading(true);

      const base64String = await loadFigure(figureUuid);
      if (!base64String) {
        setBase64String('');
      } else {
        setBase64String(base64String);
      }
    } catch (e) {
      setBase64String('');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFigure();
  }, [figureUuid]);

  return (
    <div
      style={{
        width: '50vw',
      }}
    >
      {loading && (
        <Spin
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
          }}
        />
      )}
      {!loading && !base64String && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />}
      {!loading && base64String && (
        <Image
          id="img"
          src={`data:image/png;base64,${base64String}`}
          style={{ width: '100%', height: '100%' }}
          preview={true}
        />
      )}
    </div>
  );
};

const PlotOnlyPanel = () => {
  const { open, plotOnly, nodeId, setOpen, tagList } = useModel('visualPanelControl');

  const [charts, setCharts] = useState([]);

  useEffect(() => {
    if (nodeId && tagList) {
      const currentTag = tagList.find((tag: any) => +tag.node_id === +nodeId);
      if (!currentTag) {
        setCharts([]);
        return;
      }
      const filteredCharts = (currentTag.charts || []).filter(
        (chart: any) => chart.exist_type === 'static-image',
      );
      setCharts(filteredCharts);
    } else {
      setCharts([]);
    }
  }, [nodeId, tagList]);

  return (
    <Modal
      title="Plot Only"
      width="60vw"
      open={open && plotOnly}
      centered
      footer={
        <Button
          type="primary"
          onClick={() => {
            setOpen(false);
          }}
        >
          Close
        </Button>
      }
      onCancel={() => {
        setOpen(false);
      }}
      destroyOnClose
    >
      {!charts || (charts.length === 0 && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />)}
      {charts && charts.length > 0 && (
        <Tabs
          tabPosition="left"
          items={charts.map((chart: any) => {
            return {
              label: chart.chart_name,
              key: chart.chart_uuid,
              children: <Figure figureUuid={chart.chart_uuid} />,
            };
          })}
        />
      )}
    </Modal>
  );
};

export default PlotOnlyPanel;
