import { Empty, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

const SEGMENT = 30;
const { Option } = Select;

const SingleCellSelector = (props: any) => {
  const { onChange, value, dataStructure } = props;
  const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);
  const [cellList, setCellList] = useState([] as any);
  const [showedCellList, setShowedCellList] = useState([] as any);
  const [searchCellKey, setSearchCellKey] = useState<string>('');
  const [showedCount, setShowedCount] = useState(50);
  const [loading, setLoading] = useState(false);

  const loadCellList = async () => {
    if (!dataStructure || !dataStructure.obs_names) {
      setCellList([]);
      return;
    }
    setLoading(true);
    setCellList(dataStructure.obs_names);
    setLoading(false);
  };

  useEffect(() => {
    if (!dataStructure || !dataStructure.obs_names) {
      setCellList([]);
      return;
    }
    loadCellList();
  }, [dataStructure]);

  const filteredCellList = !searchCellKey
    ? cellList
    : cellList.filter(
        (varName: string) =>
          varName.toUpperCase().indexOf(searchCellKey.trim().toUpperCase()) === 0,
      );

  const loadMoreCellData = () => {
    const moreList = [
      ...showedCellList,
      ...cellList.slice(showedCellList.length - 1, showedCellList.length - 1 + SEGMENT),
    ];
    setShowedCellList(moreList);
    setShowedCount(showedCount + SEGMENT);
  };

  const getShowedCellList = () => {
    if (searchCellKey) {
      return filteredCellList.slice(0, showedCount);
    } else {
      return filteredCellList.slice(0, showedCount);
    }
  };
  useEffect(() => {
    if (cellList) {
      setShowedCellList(cellList.slice(0, SEGMENT));
    }
  }, [cellList]);

  const onCellSearch = (value: string) => {
    setSearchCellKey(value);
  };

  return (
    <Select
      showSearch
      value={value}
      onSearch={onCellSearch}
      onChange={onChange}
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
      onPopupScroll={(e: any) => {
        const scrollTop = e.target.scrollTop;
        const childClientHeight = e.target.children[0].clientHeight;
        const clientHeight = e.target.clientHeight;
        if (scrollTop + clientHeight + 20 >= childClientHeight) {
          if (timer) {
            clearTimeout(timer);
          }
          setTimer(
            setTimeout(() => {
              loadMoreCellData();
            }, 500),
          );
        }
      }}
    >
      {getShowedCellList().map((geneset: string) => {
        return (
          <Option key={geneset} value={geneset} lable={geneset}>
            {geneset}
          </Option>
        );
      })}
    </Select>
  );
};

export default SingleCellSelector;
