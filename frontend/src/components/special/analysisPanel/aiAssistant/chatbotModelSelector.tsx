import React, { useState } from 'react';
import { Dropdown, Menu } from 'antd';
import { CheckOutlined, DownOutlined } from '@ant-design/icons';

interface ModelOption {
  key: string;
  label: string;
  icon?: React.ReactNode;
}

interface ModelSelectorProps {
  defaultModel?: string;
  onChange?: (modelKey: string) => void;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({ defaultModel = 'gpt4o-mini', onChange }) => {
  const [selectedModel, setSelectedModel] = useState<string>(defaultModel);

  const modelOptions: ModelOption[] = [{ key: 'gpt4o-mini', label: 'GPT-4o-Mini' }];

  const handleModelSelect = (key: string) => {
    setSelectedModel(key);
    if (onChange) {
      onChange(key);
    }
  };

  const modelMenu = (
    <Menu
      selectedKeys={[selectedModel]}
      onClick={({ key }) => handleModelSelect(key as string)}
      style={{
        width: '115px',
        height: '136px',
        boxShadow: '0 3px 6px rgba(0, 0, 0, 0.05)',
        borderRadius: '8px',
        border: '1px solid rgba(240, 240, 240, 1)',
      }}
    >
      {modelOptions.map((model) => (
        <Menu.Item
          key={model.key}
          icon={selectedModel === model.key ? <CheckOutlined /> : null}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            height: '32px',
            padding: '5px 12px',
            alignItems: 'center',
            fontSize: '14px',
            font: 'Roboto',
            fontWeight: 400,
            lineHeight: '22px',
          }}
        >
          {model.label}
        </Menu.Item>
      ))}
    </Menu>
  );

  return (
    <Dropdown
      overlay={modelMenu}
      trigger={['click']}
      placement="bottomCenter"
      arrow={{ pointAtCenter: true }}
    >
      <div
        style={{
          display: 'flex',
          width: '85px',
          height: '22px',
          borderRadius: '17px',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 8px',
          gap: '4px',
          fontSize: '12px',
          cursor: 'pointer',
          border: '1px solid rgba(240, 240, 240, 1)',
          marginTop: '1px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {modelOptions.find((m) => m.key === selectedModel)?.label || 'Select Model'}
        </div>
        <DownOutlined style={{ fontSize: '10px', color: '#666' }} />
      </div>
    </Dropdown>
  );
};

export default ModelSelector;
