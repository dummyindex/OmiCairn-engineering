import { Menu } from 'antd';
import { useEffect, useState } from 'react';
import { history, useLocation, useModel } from 'umi';

const UserCenterSide: React.FC = () => {
  const location = useLocation();
  const { dictionary } = useModel('localization');
  const [selectedKey, setSeletedKeys] = useState<string[]>();

  useEffect(() => {
    const selectedItem = location.pathname;
    switch (selectedItem) {
      case '/controlCenter/userCenter/nameSetting':
        setSeletedKeys(['nameSetting']);
        break;
      case '/controlCenter/userCenter/apiKey':
        setSeletedKeys(['apiKey']);
        break;
      default:
        break;
    }
  }, [location]);

  const linkNameSetting = () => {
    history.push('/controlCenter/userCenter/nameSetting');
    setSeletedKeys(['nameSetting']);
  };
  const linkAPIKey = () => {
    history.push('/controlCenter/userCenter/apiKey');
    setSeletedKeys(['apiKey']);
  };

  return (
    <div>
      <Menu
        defaultOpenKeys={['nameSetting']}
        mode="inline"
        theme="light"
        selectedKeys={selectedKey}
        style={{
          fontWeight: '600',
        }}
      >
        <Menu.Item key="nameSetting" onClick={linkNameSetting}>
          {dictionary.INFORMATION_SETTING}
        </Menu.Item>
        <Menu.Item key="apiKey" onClick={linkAPIKey}>
          Third Party API Key Management
        </Menu.Item>
      </Menu>
    </div>
  );
};

export default UserCenterSide;
