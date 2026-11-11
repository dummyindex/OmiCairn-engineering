import { requestPathwaysOrganismList } from '@/request/pathways';
import { Select } from 'antd';
import { useEffect, useState } from 'react';

const { Option } = Select;

const OrganismSelector = (props: any) => {
  const { value, organismFormItemRef, onChange } = props;

  const [speciesList, setSpeciesList] = useState<string[]>([]);

  const getSpeciesList = async () => {
    const { data: list } = await requestPathwaysOrganismList();
    if (list) {
      setSpeciesList(list);
    }
  };

  useEffect(() => {
    getSpeciesList();
    organismFormItemRef.current = value;
  }, []);

  const onOrganismSelectChange = (value: any) => {
    organismFormItemRef.current = value;
    onChange(value);
  };

  return (
    <Select onChange={onOrganismSelectChange} value={value}>
      {speciesList.map((organism: string) => {
        return (
          <Option key={organism} value={organism} lable={organism}>
            {organism}
          </Option>
        );
      })}
    </Select>
  );
};

export default OrganismSelector;
