import { DataListFetchMode } from '@/constants/data';
import { requestLatestComputation } from '@/request/computation';
import { requestDataSourceList } from '@/request/data';
import { getLocationParams } from '@/util/getUrl';
import { Empty, Select } from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';

const { Option } = Select;

const DataSelecter = (props: any) => {
  const [analysisId] = getLocationParams(['analysis-id']);
  const { nodes } = useModel('analysis');
  const { value, onChange } = props;
  //   const [loading, setLoading] = useState(false);
  const [dataSourceList, setDataSourceList] = useState([]);
  const [nodeSelectedList, setNodeSelectedList] = useState([]);
  const getImportedDataList = async () => {
    const { data: importedDataList } = await requestDataSourceList(
      DataListFetchMode.IMPORTED,
      analysisId,
      null,
    );
    setDataSourceList(importedDataList);
  };

  useEffect(() => {
    const nodeList = nodes.filter((item) => item.data.state === 'finished');
    setNodeSelectedList(nodeList);
    getImportedDataList();
  }, []);

  return (
    <Select
      showSearch
      //   value={value}
      onChange={async (value: string) => {
        const fruits = value.split('-');
        switch (fruits[0]) {
          case 'dataId': {
            onChange(fruits[1]);
            // console.log('dataId', fruits[1]);
            return;
          }
          case 'nodeId': {
            // console.log('nodeId', fruits[1]);
            const { data: latestComputation } = await requestLatestComputation(fruits[1]);
            onChange(latestComputation.resultDataId);
            return;
          }
          default:
            onChange(fruits[0]);
            return;
        }
      }}
      notFoundContent={
        // loading ? (
        //   <div
        //     style={{
        //       display: 'flex',
        //       justifyContent: 'center',
        //       alignItems: 'center',
        //       height: '8vh',
        //     }}
        //   >
        //     {' '}
        //     <Spin size="large" />
        //   </div>
        // ) : (
        <Empty />
        // )
      }
    >
      {dataSourceList.map((data) => {
        return (
          <Option
            key={data.id}
            value={`dataId-${data.id}`}
            // value={data.id}
            label={data.name}
          >
            {data.name}
          </Option>
        );
      })}
      {nodeSelectedList.map((node) => {
        return (
          <Option
            key={node.id}
            // value={node.id}
            value={`nodeId-${node.id}`}
            label={node.data.label}
          >
            {node.data.label}
          </Option>
        );
      })}
    </Select>
  );
};

export default DataSelecter;
