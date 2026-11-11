import { EnterOutlined } from '@ant-design/icons';
import { Button, Tooltip } from 'antd';
import { useModel } from 'umi';

const AxisButton = () => {
  const { chartOptionDic, setChartOptionDic } = useModel('cellSelect');

  return (
    <div style={{ marginLeft: '0.2vw', marginRight: '0.2vw' }}>
      <Tooltip title="toggle to show or hide axis">
        <Button
          type={chartOptionDic?.EmbeddingD3ChartOptions?.isShowAxis ? 'primary' : 'default'}
          icon={<EnterOutlined rotate={90} />}
          onClick={(e) => {
            e.stopPropagation();
            setChartOptionDic({
              ...chartOptionDic,
              EmbeddingD3ChartOptions: {
                ...chartOptionDic.EmbeddingD3ChartOptions,
                isShowAxis: !chartOptionDic?.EmbeddingD3ChartOptions?.isShowAxis,
              },
            });
          }}
          // style={{ marginLeft: '7px', marginRight: '6px' }}
        />
      </Tooltip>
    </div>
  );
};

export default AxisButton;
