import { requestLibraryNameList } from '@/request/pathways';
import { Empty, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

const { Option } = Select;

const LibrarySelector = (props: any) => {
  const { value, organismFormItemRef, onChange } = props;
  const [libraryNameList, setLibraryNameList] = useState([]);
  const [librarySearchValue, setLibrarySearchValue] = useState('');
  const [loading, setLoading] = useState(false);

  const getLibraryNameList = async (species: string) => {
    // if (species) {
    setLoading(true);
    const { data: list } = await requestLibraryNameList(species);
    setLibraryNameList(list);
    // }
    // else{
    //    const { data: list } = await requestLibraryNameList();
    // }
    setLoading(false);
  };

  useEffect(() => {
    getLibraryNameList(organismFormItemRef.current);
  }, [organismFormItemRef.current]);

  const librarySearch = (value: any) => {
    setLibrarySearchValue(value);
  };

  const librarySelected = (value: string[]) => {
    onChange(value);
  };

  const filteredLibraryList = !librarySearchValue
    ? libraryNameList
    : libraryNameList.filter((varName: string) =>
        varName.toUpperCase().includes(librarySearchValue.trim().toUpperCase()),
      );
  return (
    <Select
      value={value === null ? undefined : value}
      showSearch
      mode="multiple"
      filterOption={false}
      onSearch={librarySearch}
      searchValue={librarySearchValue}
      onChange={librarySelected}
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
    >
      {!loading &&
        filteredLibraryList.map((library: string) => {
          return (
            <Option key={library} value={library} lable={library}>
              {library}
            </Option>
          );
        })}
    </Select>
  );
};

export default LibrarySelector;
