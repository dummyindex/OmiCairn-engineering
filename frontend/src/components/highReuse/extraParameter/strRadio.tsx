import { Radio } from 'antd';

const StrRadio = (props: any) => {
  const { value, onChange, list } = props;

  return (
    <div>
      <Radio.Group
        size="middle"
        optionType="button"
        buttonStyle="solid"
        defaultValue={value}
        onChange={onChange}
      >
        {list.map((item: string) => {
          return (
            <Radio.Button value={item} key={item}>
              {item}
            </Radio.Button>
          );
        })}
      </Radio.Group>
    </div>
  );
};

export default StrRadio;
