import { SideMenuTab } from '@/constants/layout';
import {
  SnippetsOutlined,
  DatabaseOutlined,
  PartitionOutlined,
  FileOutlined,
} from '@ant-design/icons';
import { Button, Segmented, Tooltip } from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';
import DataSourceMenu from './dataSourceMenu';
import FunctionBlockMenu from './functionBlockMenu';
import AnalysisTree from './analysisTree';
import style from './index.less';
import './segmentedButton.css';

import { Version, VersionUpdatedTime } from '@/constants';

export default function Sider() {
  const { initFBList } = useModel('functionBlock');
  const { dictionary } = useModel('localization');
  const [selectedOutterKey, setSelectedOutterKey] = useState('analysis');
  const [selectedInnerKey, setSelectedInnerKey] = useState(SideMenuTab.DATA_SOURCE);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  useEffect(() => {
    initFBList();
  }, []);

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleOutterSelected = (key) => {
    setSelectedOutterKey(key);
  };

  const handleInnerSelected = (key) => {
    setSelectedInnerKey(key);
  };

  const outterItems = [
    {
      key: 'analysis',
      label: <PartitionOutlined />,
      tooltip: 'Analysis',
    },
    {
      key: 'docs',
      label: <SnippetsOutlined />,
      tooltip: 'Explorer',
    },
  ];

  const renderContent = () => {
    if (selectedOutterKey === 'analysis') {
      return (
        <>
          <div
            style={{
              margin: '0 1em 0 1em',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingBottom: '1em',
                paddingTop: '1em',
                borderBottom: '1px solid #f0f0f0',
                gap: '5px',
              }}
            >
              <Segmented
                className="custom-segmented"
                style={{
                  borderRadius: '6px',
                  padding: '4px',
                  width: '90%',
                  fontSize: '13px',
                  fontWeight: '500',
                  font: 'Roboto',
                }}
                block
                options={[
                  {
                    label: (
                      <>
                        <DatabaseOutlined
                          style={{
                            marginRight: '5px',
                            display: windowWidth < 1700 ? 'none' : 'inline-block',
                          }}
                        />
                        {dictionary.DATA_SOURCE}
                      </>
                    ),
                    value: SideMenuTab.DATA_SOURCE,
                  },
                  {
                    label: (
                      <>
                        <PartitionOutlined
                          style={{
                            marginRight: '5px',
                            display: windowWidth < 1700 ? 'none' : 'inline-block',
                          }}
                        />
                        {dictionary.FUNCTION_BLOCK}
                      </>
                    ),
                    value: SideMenuTab.FUNCTION_BLOCK,
                  },
                ]}
                value={selectedInnerKey}
                onChange={handleInnerSelected}
              />
              <Button
                type="text"
                icon={<FileOutlined />}
                onClick={() => {
                  window.open('/functionBlock', '_blank');
                }}
              />
            </div>
          </div>
          <div className={style.menuBox}>
            {selectedInnerKey === SideMenuTab.DATA_SOURCE ? (
              <DataSourceMenu />
            ) : (
              <FunctionBlockMenu />
            )}
          </div>
        </>
      );
    } else if (selectedOutterKey === 'docs') {
      return <AnalysisTree />;
    }
    return null;
  };

  return (
    <div className={style.leftSider}>
      <div
        style={{
          height: '100%',
          display: 'flex',
          flexDirection: 'row',
        }}
      >
        <div className={style.outterMenu}>
          {outterItems.map((item) => {
            return (
              <Tooltip key={item.key} title={item.tooltip} placement="right">
                <div
                  className={`${style.outterMenuItem} ${
                    item.key === selectedOutterKey
                      ? style.outterMenuItemActive
                      : style.outterMenuItemInactive
                  }`}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleOutterSelected(item.key);
                  }}
                >
                  {item.label}
                </div>
              </Tooltip>
            );
          })}
        </div>

        <div style={{ width: 'calc(100% - 2.5vw)', position: 'relative' }}>
          {renderContent()}
          <div style={{ position: 'absolute', bottom: '10px', left: '20px', fontSize: '12px' }}>
            {Version} ( {VersionUpdatedTime} )
          </div>
        </div>
      </div>
    </div>
  );
}
