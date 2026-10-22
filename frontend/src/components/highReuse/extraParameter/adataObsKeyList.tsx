import { Empty, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

const { Option } = Select;

const AdataObsKeyList = (props: any) => {
  const { value, onChange, dataStructure } = props;

  const [list, setList] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const loadList = async () => {
    if (Object.keys(dataStructure).length == 0) {
      setList([]);
      return;
    }
    setLoading(true);
    const obsKey = dataStructure.obs.map((item) => {
      return item.key;
    });
    obsKey.unshift('None');
    setList(obsKey);
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
      mode="multiple"
      allowClear
      value={value === null ? undefined : value}
      onChange={(value) => {
        if (value.includes('None')) {
          onChange(['None']);
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

export default AdataObsKeyList;
