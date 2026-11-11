import { Empty, message, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

const { Option } = Select;

const AdataObspKey = (props: any) => {
  const { value, onChange, onClear, dataStructure } = props;

  const [list, setList] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const loadList = async () => {
    if (Object.keys(dataStructure).length == 0) {
      setList([]);
      return;
    }
    try {
      setLoading(true);
      const obspKeys = Object.keys(dataStructure.obsp);
      obspKeys.unshift('None');
      setList(obspKeys);
    } catch (e: any) {
      message.error(e.message);
    }
    setLoading(false);
  };
  useEffect(() => {
    if (!dataStructure || Object.keys(dataStructure).length === 0) {
      setList([]);
      return;
    }
    loadList();
  }, [dataStructure]);

  const onObspChange = (value: any) => {
    if (value === undefined || value === 'None') {
      onChange('None');
      return;
    }
    onChange(value);
  };

  return (
    <Select
      value={value}
      allowClear
      onChange={onObspChange}
      onClear={onClear}
      notFoundContent={
        loading ? (
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '8vh',
            }}
          >
            {' '}
            <Spin size="large" />
          </div>
        ) : (
          <Empty />
        )
      }
    >
      {list.map((item: string) => {
        return (
          <Option key={item} value={item} lable={item}>
            {item}
          </Option>
        );
      })}
    </Select>
  );
};

export default AdataObspKey;
