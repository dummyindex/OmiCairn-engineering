import { useEffect } from 'react';
import { CheckCircleFilled } from '@ant-design/icons';

type Props = {
  initialValue?: boolean;
  value: boolean;
  onChange?: (value: boolean) => void;
  style?: React.CSSProperties;
};
const CustomRadio = (props: Props) => {
  const { initialValue, value, onChange, style } = props;

  useEffect(() => {
    if (initialValue !== undefined && !!onChange) {
      onChange(initialValue);
    }
  }, [initialValue]);

  const handleChange = () => {
    if (!onChange) return;
    onChange(!value);
  };

  return (
    <CheckCircleFilled
      style={{ color: value ? '#1890ff' : '#d9d9d9', ...(style || {}) }}
      onClick={handleChange}
    />
  );
};

export default CustomRadio;
