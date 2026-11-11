import { getAPIKeys } from '@/request/apiKey';
import { Empty, message, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

const { Option } = Select;

const APIKeyInput = (props: any) => {
  const { value, onChange, onClear } = props;

  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadList = async () => {
    setLoading(true);
    try {
      const apiKeyListResponse = await getAPIKeys();
      const { data: apiKeyList } = apiKeyListResponse;
      if (!apiKeyList) {
        message.error('Failed to load API keys');
        return;
      }
      setList(apiKeyList);
      setLoading(false);
    } catch (error) {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadList();
  }, []);

  return (
    <Select
      value={value}
      allowClear
      onChange={onChange}
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
      {list.map((item: any) => {
        return (
          <Option key={item.id} value={item.value} title={item.name}>
            {item.name}
          </Option>
        );
      })}
    </Select>
  );
};

export default APIKeyInput;
