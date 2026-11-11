import { useEffect, useState } from 'react';
import style from './sampleDataBlock.less';
import { Table, Button } from 'antd';
import { DatabaseOutlined } from '@ant-design/icons';
import { requestDataSourceList } from '@/request/data';
import { DataListFetchMode } from '@/constants/data';
import { useModel } from 'umi';
import type { DataType } from '@/interfaces/data';

interface Props {
  searchKey: string;
}

const SampleDataBlock = (props: Props) => {
  const { searchKey } = props;
  const { dictionary } = useModel('localization');
  const { setIsThirdPartyDataListModalVisible: setThirdPartyDataSourceModalVisible } =
    useModel('thirdPartyDataSource');

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const [dataList, setDataList] = useState([] as DataType[]);

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const [loading, setLoading] = useState(false as boolean);

  const columns = [
    {
      title: dictionary.NAME,
      dataIndex: 'name',
      key: 'id',
      render: (text: string, item: DataType) => {
        return (
          <div
            key={item.id}
            title={text}
            style={{
              width: '13vw',
              // Hide overflow
              overflow: 'hidden',
              // Replace overflow with an ellipsis
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            <DatabaseOutlined
              style={{
                marginRight: '15px',
              }}
            />
            <span>{text}</span>
          </div>
        );
      },
    },
    {
      title: dictionary.DESCRIPTION,
      dataIndex: 'description',
      key: 'id',
      render: (text: string) => {
        return (
          <span
            style={{
              wordWrap: 'break-word',
              wordBreak: 'break-word',
              whiteSpace: 'normal',
              display: 'block',
            }}
          >
            {text || 'No explanation at the moment'}
          </span>
        );
      },
    },
  ];

  const loadDataList = async () => {
    setLoading(true);
    const { data: dataList } = await requestDataSourceList(
      DataListFetchMode.PUBLIC,
      null,
      searchKey,
    );
    setDataList(
      dataList.map((item: any) => {
        return {
          ...item,
          key: item.id,
        };
      }),
    );
    setLoading(false);
  };

  const handleShowMore = () => {
    setThirdPartyDataSourceModalVisible(true);
  };

  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    loadDataList();
  }, [searchKey]);

  return (
    <div className={style.sampleDataBlock}>
      <div className={style.title}>
        <div className={style.titleText}>{dictionary.SAMPLE_DATA}</div>
        <Button type="primary" onClick={handleShowMore}>
          {dictionary.SHOW_MORE}
        </Button>
      </div>
      <Table loading={loading} columns={columns} dataSource={dataList} />
    </div>
  );
};

export default SampleDataBlock;
