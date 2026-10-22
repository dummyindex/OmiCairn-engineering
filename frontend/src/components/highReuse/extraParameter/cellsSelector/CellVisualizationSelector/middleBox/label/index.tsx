import { ExtraIcon } from '@/components/common/extraIcon';
import { ColorMode } from '@/constants/cellSelector';
import { Button, Tooltip } from 'antd';
import { useModel } from 'umi';

const LabelButton = () => {
  const { chartShowLabels, setChartShowLabels, colorMode } = useModel('cellSelect');
  return (
    <Tooltip title="toggle to show or hide labels">
      <Button
        onClick={() => {
          setChartShowLabels(!chartShowLabels);
        }}
        icon={<ExtraIcon type="icon-text" />}
        type={chartShowLabels ? 'primary' : 'default'}
        disabled={colorMode !== ColorMode.CATEGORY_OBS}
        style={{ marginLeft: '0.2vw', marginRight: '0.2vw' }}
      />
    </Tooltip>
  );
};

export default LabelButton;
