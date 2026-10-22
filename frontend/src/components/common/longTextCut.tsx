import React from 'react';
import { Tooltip } from 'antd';
interface Props {
  text: string;
  maxLength: number;
}

const LongTextCut: React.FC<Props> = ({ text, maxLength }) => {
  if (text.length <= maxLength) {
    return <>{text}</>;
  }
  const remainLength = maxLength - 2 - (maxLength % 2); // (n - 2) % 2 == n % 2
  return (
    <Tooltip title={text}>
      <span>
        {text.slice(0, remainLength / 2)}...{text.slice(-remainLength)}
      </span>
    </Tooltip>
  );
};

export default LongTextCut;
