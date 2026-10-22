import type { MenuProps } from 'antd';
import { Menu } from 'antd';
import React, { useEffect, useState } from 'react';

const FunctionBlockList: React.FC<{
  setFunctionBlockId: (id: string) => void;
  functionBlockList: any[];
  functionBlockGroup: string;
  defaultSelectedFB: string;
}> = (props: any) => {
  const { setFunctionBlockId, functionBlockList, functionBlockGroup, defaultSelectedFB } = props;
  const [selectedKeys, setSelectedKeys] = useState([]);

  const [openKeys, setOpenKeys] = useState([defaultSelectedFB]);
  useEffect(() => {
    setSelectedKeys([`menu${defaultSelectedFB}`]);
  }, [defaultSelectedFB]);

  useEffect(() => {
    setOpenKeys([`${functionBlockGroup}`]);
  }, [functionBlockGroup]);

  const onOpenChange: MenuProps['onOpenChange'] = (keys: string[]) => {
    const latestOpenKey = keys.find((key: string) => openKeys.indexOf(key) === -1);
    if (openKeys.indexOf(latestOpenKey!) === -1) {
      setOpenKeys(keys);
    } else {
      setOpenKeys(latestOpenKey ? openKeys.concat([latestOpenKey]) : []);
    }
  };

  const onSelect = (item) => {
    setSelectedKeys(item.key);
  };

  return (
    <div style={{ height: '100%' }}>
      <Menu
        mode="inline"
        selectedKeys={selectedKeys}
        openKeys={openKeys}
        onOpenChange={onOpenChange}
        onSelect={onSelect}
      >
        {functionBlockList &&
          functionBlockList.map((item) => {
            return (
              <Menu.SubMenu
                key={`${item.serialNumber}`}
                title={
                  <span>
                    <span style={{ fontWeight: '600' }}>
                      {item.name}
                      {`(${item.functionBlockList.length})`}
                    </span>
                  </span>
                }
              >
                {item.functionBlockList.map((value: any) => {
                  return (
                    <Menu.Item
                      key={`menu${value.id}`}
                      title={value.name}
                      onClick={() => {
                        setFunctionBlockId(value.id);
                      }}
                    >
                      {value.name}
                    </Menu.Item>
                  );
                })}
              </Menu.SubMenu>
            );
          })}
      </Menu>
    </div>
  );
};

export default FunctionBlockList;
