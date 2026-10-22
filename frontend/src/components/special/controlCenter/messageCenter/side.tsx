import { Menu } from 'antd';
import { useEffect, useState } from 'react';
import { history, useLocation, useModel } from 'umi';

const MessageCenterSide: React.FC = () => {
  const location = useLocation();
  const { dictionary } = useModel('localization');
  const [selectedKey, setSeletedKeys] = useState<string[]>();

  useEffect(() => {
    const selectedItem = location.pathname;
    switch (selectedItem) {
      case '/controlCenter/messageCenter/serviceBulletin':
        setSeletedKeys(['serviceBulletin']);
        break;
      case '/controlCenter/messageCenter/collaborationNotification':
        setSeletedKeys(['collaborationNotification']);
        break;
      case '/controlCenter/messageCenter/analysisProgressNotification':
        setSeletedKeys(['analysisProgressNotification']);
        break;
      default:
        break;
    }
  }, [location.pathname]);

  const linkServiceBulletin = () => {
    history.push('/controlCenter/messageCenter/serviceBulletin');
    setSeletedKeys(['serviceBulletin']);
  };
  const linkCollaborationNotification = () => {
    history.push('/controlCenter/messageCenter/collaborationNotification');
    setSeletedKeys(['collaborationNotification']);
  };
  const linkAnalysisProgressNotification = () => {
    history.push('/controlCenter/messageCenter/analysisProgressNotification');
    setSeletedKeys(['analysisProgressNotification']);
  };

  return (
    <div>
      <Menu
        // defaultSelectedKeys={selectedKey}
        defaultOpenKeys={['serviceBulletin']}
        mode="inline"
        theme="light"
        selectedKeys={selectedKey}
        style={{
          fontWeight: '600',
        }}
      >
        <Menu.Item key="serviceBulletin" onClick={linkServiceBulletin}>
          {dictionary.SERVICE_BULLETIN}
        </Menu.Item>
        <Menu.Item key="collaborationNotification" onClick={linkCollaborationNotification}>
          {dictionary.COLLABORATION_NOTIFICATION}
        </Menu.Item>
        <Menu.Item key="analysisProgressNotification" onClick={linkAnalysisProgressNotification}>
          {dictionary.ANALYSIS_PROGRESS_NOTIFICATION}
        </Menu.Item>
      </Menu>
    </div>
  );
};

export default MessageCenterSide;
