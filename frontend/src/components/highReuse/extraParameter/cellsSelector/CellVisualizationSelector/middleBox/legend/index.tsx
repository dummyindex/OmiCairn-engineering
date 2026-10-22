import { ProfileOutlined } from '@ant-design/icons';
import { Button, Tooltip } from 'antd';
import { useModel } from 'umi';

const LegendButton = () => {
  const { chartOptionDic, setChartOptionDic } = useModel('cellSelect');

  return (
    <div style={{ marginLeft: '0.2vw', marginRight: '0.2vw' }}>
      <Tooltip title="toggle to show or hide legend">
        <Button
          type={chartOptionDic.EmbeddingD3ChartOptions.isShowLegend ? 'primary' : 'default'}
          icon={<ProfileOutlined />}
          onClick={(e) => {
            e.stopPropagation();
            setChartOptionDic({
              ...chartOptionDic,
              EmbeddingD3ChartOptions: {
                ...chartOptionDic.EmbeddingD3ChartOptions,
                isShowLegend: !chartOptionDic.EmbeddingD3ChartOptions.isShowLegend,
              },
            });
          }}
        />
      </Tooltip>
    </div>
  );
};

export default LegendButton;
