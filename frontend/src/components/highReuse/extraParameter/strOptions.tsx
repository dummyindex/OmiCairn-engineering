import { Select } from 'antd';

const { Option } = Select;

const StrOptions = (props: any) => {
  const { value, onChange, list } = props;

  return (
    <Select
      value={value}
      onChange={(value) => {
        if (value === undefined) {
          onChange(null);
          return;
        }
        onChange(value);
      }}
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

export default StrOptions;
