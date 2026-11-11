import { Empty, message, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

const { Option } = Select;

const AdataObsKey = (props: any) => {
  const { value, onChange, onClear, adataObsKeyRef, dataStructure } = props;

  const [list, setList] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const loadList = async () => {
    if (Object.keys(dataStructure).length == 0) {
      setList([]);
      return;
    }
    try {
      setLoading(true);
      const obsKeys = dataStructure.obs.map((item) => {
        return item.key;
      });
      obsKeys.unshift('None');
      setList(obsKeys);
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
    adataObsKeyRef.current = value;
  }, [dataStructure]);

  const onObsChange = (value: any) => {
    if (value === undefined || value === 'None') {
      onChange('None');
      adataObsKeyRef.current = null;
      return;
    }
    adataObsKeyRef.current = value;
    onChange(value);
  };

  return (
    <Select
      value={value}
      allowClear
      onChange={onObsChange}
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

export default AdataObsKey;
