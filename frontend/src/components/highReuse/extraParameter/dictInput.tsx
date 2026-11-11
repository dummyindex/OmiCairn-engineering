import { Input } from 'antd';

type DictInputProps = {
  value?: string;
  onChange?: (value: string) => void;
};

const DictInput = (props: DictInputProps) => {
  const { value, onChange } = props;

  const onStrChange = (v: string) => {
    try {
      const resultDict = JSON.parse(v);
      onChange(resultDict);
    } catch (e) {
      onChange(v);
    }
  };

  return (
    <Input.TextArea
      value={typeof value === 'string' ? value : JSON.stringify(value)}
      onChange={(e: any) => onStrChange(e.target.value)}
    />
  );
};

export default DictInput;
