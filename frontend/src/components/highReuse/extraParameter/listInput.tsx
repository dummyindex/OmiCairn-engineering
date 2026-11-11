import { PlusOutlined } from '@ant-design/icons';
import { Button, Input, InputNumber, Space, Tag } from 'antd';
import React from 'react';

interface ListInputProps {
  value: any;
  elementType: string;
  onChange: (v: any) => void;
}

export const ElementType = {
  FLOAT: 'float',
  INT: 'int',
  STRING: 'string',
};

const ListInput = (props: ListInputProps) => {
  const { value, elementType, onChange } = props;

  const [addingMode, setAddingMode] = React.useState(false);

  const [inputValue, setInputValue] = React.useState('');

  const removeItem = (index: number) => {
    const newValue = [...value]; // Copy the original value into a new array
    newValue.splice(index, 1);

    onChange(newValue);
  };

  const editInputValue = (newValue: string) => {
    setInputValue(newValue);
  };

  const addItem = () => {
    if (inputValue === '') {
      setAddingMode(false);
      return;
    }
    const newList = [...(value || []), inputValue];
    onChange(newList);
    setInputValue('');
    setAddingMode(false);
  };

  const getAddInput = () => {
    switch (elementType) {
      case ElementType.STRING: {
        return (
          <Input
            size="small"
            onChange={(event: any) => {
              editInputValue(event.target.value);
            }}
            onPressEnter={addItem}
            onBlur={addItem}
          />
        );
      }
      case ElementType.INT: {
        return (
          <InputNumber
            defaultValue={''}
            onChange={(v: number) => {
              editInputValue(v.toString());
            }}
            onPressEnter={addItem}
            onBlur={addItem}
          />
        );
      }
      case ElementType.FLOAT: {
        return (
          <InputNumber
            defaultValue={''}
            onChange={(v: number) => {
              editInputValue(v.toString());
            }}
            step={0.1}
            onPressEnter={addItem}
            onBlur={addItem}
          />
        );
      }
      default: {
        return null;
      }
    }
  };

  return (
    <Space size={[0, 8]} wrap>
      {(value || []).map((item: any, index: number) => {
        const key = `${item}-${index}`;
        return (
          <Tag
            color="blue"
            key={key}
            closable
            onClose={(e) => {
              e.stopPropagation();
              removeItem(index);
            }}
          >
            {item}
          </Tag>
        );
      })}
      {addingMode ? (
        getAddInput()
      ) : (
        <Button
          icon={<PlusOutlined />}
          size="small"
          type="dashed"
          onClick={() => {
            setAddingMode(true);
          }}
        >
          add item
        </Button>
      )}
    </Space>
  );
};

ListInput.defaultProps = {
  elementType: ElementType.STRING,
};

export default ListInput;
