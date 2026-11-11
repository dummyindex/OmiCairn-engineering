import { Empty, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

const { Option } = Select;

const AdataLayerKey = (props: any) => {
  const { value, onChange, dataStructure } = props;

  const [list, setList] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const loadList = async () => {
    if (Object.keys(dataStructure).length == 0) {
      setList([]);
      return;
    }
    setLoading(true);
    const layerkey = Object.keys(dataStructure.layers);
    layerkey.unshift('None');
    setList(layerkey);
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
      style={{ width: 200 }}
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

export default AdataLayerKey;
