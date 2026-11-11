import WorkflowIcon from '@/assets/icons/workflow';
import {
  AppstoreFilled,
  AppstoreOutlined,
  BookOutlined,
  ContainerOutlined,
  PartitionOutlined,
  RobotFilled,
} from '@ant-design/icons';
import { useEffect, useState } from 'react';
import { history, useLocation, useModel } from 'umi';
import styles from './homeSider.less';

const SubMenu = ({ title, items, onSelect, selectedKey, width }) => {
  return (
    <div
      style={{
        width,
      }}
    >
      <div
        style={{
          fontSize: '1.2em',
          fontWeight: '500',
          lineHeight: '4em',
          paddingLeft: '1em',
        }}
      >
        {title}
      </div>
      <div className={styles.navMenu}>
        {items.map(({ key, label, icon }: any) => {
          return (
            <div
              className={`${styles.navMenuItem} ${
                key === selectedKey ? styles.navMenuItemActive : styles.navMenuItemInactive
              }`}
              key={key}
              onClick={(e: any) => {
                e.stopPropagation();
                onSelect(key);
              }}
            >
              <span>{icon}</span> <span>{label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const HomeSider: React.FC = () => {
  const location = useLocation();

  const { dictionary } = useModel('localization');

  const [selectedOutterKey, setSelectedOutterKey] = useState<string>('workflow');

  const [selectedInnerKey, setSelectedInnerKey] = useState<string>('Home');

  const { isGuest } = useModel('user');
  const isGuestUser = isGuest();

  const handleOutterSelected = (key: string) => {
    setSelectedOutterKey(key);
    switch (key) {
      case 'workflow':
        history.push('/management/homeMain');
        setSelectedInnerKey('analysis-task');
        break;
      case 'app-store':
        history.push('/management/allApps');
        setSelectedInnerKey('all-apps');
        break;
      case 'ai':
        history.push('/management/gptPage');
        break;
      default:
        break;
    }
  };

  const handleInnerSelected = (key: string) => {
    switch (key) {
      case 'analysis-task':
        history.push('/management/homeMain');
        break;
      case 'data-source':
        history.push('/management/data');
        break;
      case 'all-apps':
        history.push('/management/allApps');
        break;
      case 'my-libraries':
        history.push('/management/myLibraries');
        break;
      default:
        break;
    }
  };

  useEffect(() => {
    const selectedItem = location.pathname;
    switch (selectedItem) {
      case '/management/homeMain':
        setSelectedOutterKey('workflow');
        setSelectedInnerKey('analysis-task');
        break;
      case '/management/data':
        setSelectedOutterKey('workflow');
        setSelectedInnerKey('data-source');
        break;
      case '/management/allApps':
        setSelectedOutterKey('app-store');
        setSelectedInnerKey('all-apps');
        break;
      case '/management/myLibraries':
        setSelectedOutterKey('app-store');
        setSelectedInnerKey('my-libraries');
        break;
      case '/management/gptPage':
        setSelectedOutterKey('ai');
        break;
      default:
        break;
    }
  }, [location]);

  const outterItems = [
    {
      key: 'workflow',
      label: <WorkflowIcon size="1.1em" />,
    },
    ...(!isGuestUser
      ? [
          {
            key: 'app-store',
            label: <AppstoreFilled />,
          },
          {
            key: 'ai',
            label: <RobotFilled />,
          },
        ]
      : []),
  ];

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'stretch',
      }}
    >
      <div className={styles.outterMenu}>
        {outterItems.map((item: any) => {
          return (
            <div
              className={`${styles.outterMenuItem} ${
                item.key === selectedOutterKey
                  ? styles.outterMenuItemActive
                  : styles.outterMenuItemInactive
              }`}
              key={item.key}
              onClick={(e: any) => {
                e.stopPropagation();
                handleOutterSelected(item.key);
              }}
            >
              {item.label}
            </div>
          );
        })}
      </div>
      <div>
        {selectedOutterKey === 'workflow' && (
          <SubMenu
            title={dictionary.WORKFLOW}
            items={[
              {
                key: 'analysis-task',
                label: dictionary.ANALYSIS_TASK,
                icon: <PartitionOutlined />,
              },
              { key: 'data-source', label: dictionary.DATA_SOURCE, icon: <ContainerOutlined /> },
            ]}
            onSelect={handleInnerSelected}
            selectedKey={selectedInnerKey}
            width={'13vw'}
          />
        )}
        {selectedOutterKey === 'app-store' && (
          <SubMenu
            title={dictionary.APP_STORE}
            items={[
              { key: 'all-apps', label: dictionary.ALL_APPS, icon: <AppstoreOutlined /> },
              { key: 'my-libraries', label: dictionary.MY_LIBRARIES, icon: <BookOutlined /> },
            ]}
            onSelect={handleInnerSelected}
            selectedKey={selectedInnerKey}
            width={'13vw'}
          />
        )}
      </div>
    </div>
  );
};

export default HomeSider;
