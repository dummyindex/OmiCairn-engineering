import { Empty, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

const { Option } = Select;

const AdataUnsKey = (props: any) => {
  const { value, onChange, dataStructure } = props;

  const [list, setList] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const loadList = async () => {
    if (Object.keys(dataStructure).length == 0) {
      setList([]);
      return;
    }
    setLoading(true);
    const unsKey = dataStructure.uns_keys;
    unsKey.unshift('None');
    setList(unsKey);
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
      onChange={(value: string) => {
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
export default AdataUnsKey;
