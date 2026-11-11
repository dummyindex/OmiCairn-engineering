import { ChartOperationMode } from '@/constants/cellSelector';
import { DragOutlined, RadiusUprightOutlined } from '@ant-design/icons';
import { Radio, Tooltip } from 'antd';
import { useModel } from 'umi';

const ChartOperationModeSelect = () => {
  const { chartOperationMode, setChartOperationMode } = useModel('cellSelect');
  return (
    <Tooltip title="select chart operation mode">
      <Radio.Group
        buttonStyle="solid"
        size="middle"
        value={chartOperationMode}
        onChange={(e) => {
          setChartOperationMode(e.target.value);
        }}
        style={{
          marginLeft: '0.2vw',
          marginRight: '0.2vw',
          whiteSpace: 'nowrap',
        }}
      >
        <Radio.Button value={ChartOperationMode.BRUSH}>
          <RadiusUprightOutlined />
        </Radio.Button>
        <Radio.Button value={ChartOperationMode.DRAG}>
          <DragOutlined />
        </Radio.Button>
      </Radio.Group>
    </Tooltip>
  );
};

export default ChartOperationModeSelect;
