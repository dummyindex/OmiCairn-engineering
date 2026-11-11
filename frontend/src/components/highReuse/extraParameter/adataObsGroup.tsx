import { Empty, message, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

const { Option } = Select;

const AdataObsGroup = (props: any) => {
  const { value, onChange, dataStructure } = props;

  const [list, setList] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const loadList = async () => {
    if (Object.keys(dataStructure).length == 0) {
      setList([]);
      return;
    }
    try {
      setLoading(true);
      const obs = dataStructure?.obs || [];
      const { categoryKeys } = obs.reduce(
        (acc: any, cur: any) => {
          if (cur.dtype === 'category') {
            acc.categoryKeys.push(cur.key);
          }
          return acc;
        },
        { categoryKeys: [] },
      );
      categoryKeys.unshift('None');
      setList(categoryKeys);
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

  return (
    <Select
      value={value}
      allowClear
      onChange={(value) => {
        if (value === undefined || value === 'None') {
          onChange('None');
          return;
        }
        onChange(value);
      }}
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

export default AdataObsGroup;
