import { Empty, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

const SEGMENT = 30;
const { Option } = Select;

const SingleGeneSelector = (props: any) => {
  const { value, onChange, dataStructure } = props;
  const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);
  const [geneList, setGeneList] = useState([] as any);
  const [searchGeneKey, setSearchGeneKey] = useState<string>('');
  const [showedGeneList, setShowedGeneList] = useState([] as any);
  const [showedGeneCount, setShowedGeneCount] = useState(50);
  const [loading, setLoading] = useState(false);
  const loadGeneList = async () => {
    if (!dataStructure || !dataStructure.var_names) {
      setGeneList([]);
      return;
    }
    setLoading(true);
    setGeneList(dataStructure.var_names);
    setLoading(false);
  };

  useEffect(() => {
    if (!dataStructure || !dataStructure.var_names) {
      setGeneList([]);
      return;
    }
    loadGeneList();
  }, [dataStructure]);
  const loadMoreGeneData = () => {
    const moreList = [
      ...showedGeneList,
      ...geneList.slice(showedGeneList.length - 1, showedGeneList.length - 1 + SEGMENT),
    ];
    setShowedGeneList(moreList);
    setShowedGeneCount(showedGeneCount + SEGMENT);
  };

  const filteredGeneList = !searchGeneKey
    ? geneList
    : geneList.filter((varName: string) => {
        return varName.toUpperCase().includes(searchGeneKey.trim().toUpperCase());
      });

  const getShowedGeneList = () => {
    if (searchGeneKey) {
      return filteredGeneList.slice(0, showedGeneCount);
    } else {
      return filteredGeneList.slice(0, showedGeneCount);
    }
  };

  const onGeneSearch = (value: string) => {
    setSearchGeneKey(value);
  };

  return (
    <Select
      showSearch
      onSearch={onGeneSearch}
      value={value}
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
              loadMoreGeneData();
            }, 500),
          );
        }
      }}
    >
      {getShowedGeneList().map((geneset: string) => {
        return (
          <Option key={geneset} value={geneset} lable={geneset}>
            {geneset}
          </Option>
        );
      })}
    </Select>
  );
};

export default SingleGeneSelector;
