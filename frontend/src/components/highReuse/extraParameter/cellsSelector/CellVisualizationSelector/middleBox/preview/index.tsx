import { EyeOutlined } from '@ant-design/icons';
import { Button, Tooltip } from 'antd';
import { useModel } from 'umi';

const PreviewButton = () => {
  const { setVisible } = useModel('cellSelect');
  return (
    <Tooltip title="toggle to show or hide labels">
      <Button
        onClick={() => {
          setVisible(true);
        }}
        icon={<EyeOutlined style={{ color: '#888' }} />}
        type="default"
        // disabled={colorMode !== ColorMode.CATEGORY_OBS}
        style={{ marginLeft: '0.2vw', marginRight: '0.2vw' }}
      />
    </Tooltip>
  );
};

export default PreviewButton;
