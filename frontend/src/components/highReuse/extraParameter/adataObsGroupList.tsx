import { Empty, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

const { Option } = Select;

const AdataObsGroupList = (props: any) => {
  const { value, onChange, adataObsKeyRef, dataStructure } = props;
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadList = async (categoryName: string) => {
    if (Object.keys(dataStructure).length == 0) {
      setList([]);
      return;
    }
    setLoading(true);
    const obs = dataStructure?.obs || [];
    const { categoryKeys } = obs.reduce(
      (acc: any, cur: any) => {
        if (cur.dtype === 'category' && cur.key === categoryName) {
          cur.categories.forEach((item) => {
            acc.categoryKeys.push(item);
          });
        }
        return acc;
      },
      { categoryKeys: [] },
    );

    categoryKeys.unshift('None');
    setList(categoryKeys);
    setLoading(false);
  };
  useEffect(() => {
    loadList(adataObsKeyRef.current);
  }, [adataObsKeyRef.current, dataStructure]);
  // useEffect(() => {
  //   if (value === 'all') {
  //     setParameter(list);
  //   } else if (value == null) {
  //     setParameter(undefined);
  //   } else {
  //     setParameter(value);
  //   }
  // }, []);
  const handleSelectChange = (selectedValues) => {
    // Check if "None" is selected and remove it from the selected values
    let updatedValues = selectedValues;
    if (value === undefined) {
      onChange('None');
      return;
    }
    if (selectedValues.includes('None') && selectedValues.length > 1) {
      updatedValues = selectedValues.filter((value) => value !== 'None');
    }
    onChange(updatedValues);
  };

  return (
    <div>
      <Select
        mode="multiple"
        allowClear
        value={value === null ? undefined : value}
        // onChange={(value) => {
        //   // console.log('value', value);
        //   // if (value.includes('all')) {
        //   //   const valueList = list.filter((item) => {
        //   //     return item !== 'None';
        //   //   });
        //   //   console.log('valueList', valueList);

        //   //   onChange(valueList);
        //   //   return;
        //   // }
        //   if (value === undefined) {
        //     onChange('None');
        //     return;
        //   }
        //   onChange(value);
        // }}
        // onChange={handleChange}
        onChange={handleSelectChange}
        loading={loading}
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
        {/* <Option key={'all'} value={'all'} lable={'all'}>
          all
        </Option> */}
        {list.map((item: string) => {
          return (
            <Option key={item} value={item} lable={item}>
              {item}
            </Option>
          );
        })}
      </Select>
    </div>
  );
};

export default AdataObsGroupList;
