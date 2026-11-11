import MyDataBlock from '@/components/special/management/dataSource/myDataBlock';
import SampleDataBlock from '@/components/special/management/dataSource/sampleDataBlock';
import { Input } from 'antd';
import React from 'react';
import style from './dataSource.less';
import { SearchOutlined } from '@ant-design/icons';
import { useModel } from 'umi';

let delayTimer: NodeJS.Timeout;
const DataSource: React.FC = () => {
  const { dictionary } = useModel('localization');
  const [searchKey, setSearchKey] = React.useState('' as string);

  const editSearchKey = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (delayTimer) {
      clearInterval(delayTimer);
    }
    delayTimer = setTimeout(() => {
      setSearchKey(e.target.value);
    }, 200);
  };

  return (
    <div className={style.dataSourceContainer}>
      <Input
        placeholder={dictionary.SEARCH}
        size="large"
        className={style.searchInput}
        onChange={editSearchKey}
        suffix={<SearchOutlined />}
      />
      <h2 className={style.title}>{dictionary.DATA_SOURCE}</h2>
      <SampleDataBlock searchKey={searchKey} />
      <div className={style.gap} />
      <MyDataBlock searchKey={searchKey} />
    </div>
  );
};

export default DataSource;
