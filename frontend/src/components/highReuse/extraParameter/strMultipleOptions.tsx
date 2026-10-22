import { Select } from 'antd';

const { Option } = Select;

const StrMultipleOptions = (props: any) => {
  const { value, onChange, list } = props;

  return (
    <Select
      mode="multiple"
      allowClear
      value={value === null ? undefined : value}
      onChange={onChange}
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

export default StrMultipleOptions;
