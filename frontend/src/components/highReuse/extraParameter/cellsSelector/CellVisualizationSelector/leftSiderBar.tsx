import { Input, Radio } from 'antd';
import style from '../CellVisualizationSelector/leftSiderBar/leftSider.less';
import { useState } from 'react';
import ObsContent from '../CellVisualizationSelector/leftSiderBar/obs';
import GeneContent from '../CellVisualizationSelector/leftSiderBar/gene';
import { useModel } from 'umi';
import { SearchOutlined } from '@ant-design/icons';
import { CellLeftMenu } from '@/constants/cellSelector';

// const { Search } = Input;

const LeftSiderBar = (props) => {
  const { dataStructure } = props;
  const { setSearchKey } = useModel('cellSelect');

  const [menuSelected, setMenuSelected] = useState<string>(CellLeftMenu.OBS);

  const showContent = (item: string) => {
    switch (item) {
      case CellLeftMenu.OBS:
        return <ObsContent dataStructure={dataStructure} />;
      case CellLeftMenu.GENE:
        return <GeneContent menuSelected={menuSelected} dataStructure={dataStructure} />;
      default: {
        return null;
      }
    }
  };
  // const onSearch = (value: string) => console.log(value);
  return (
    <div className={style.leftCategory}>
      <div style={{ width: '100%', marginBottom: '1vh' }}>
        <Input
          placeholder="input search keywords"
          allowClear
          onChange={({ target: { value } }) => {
            setSearchKey(value);
          }}
          suffix={<SearchOutlined />}
        />
      </div>
      <Radio.Group
        defaultValue={menuSelected}
        buttonStyle="solid"
        onChange={(e: any) => {
          setMenuSelected(e.target.value);
        }}
        size="middle"
        style={{ marginTop: '1vh', marginBottom: '1vh' }}
      >
        <Radio.Button
          // style={{ width: '100' }}
          value={CellLeftMenu.OBS}
        >
          obs
        </Radio.Button>
        <Radio.Button value={CellLeftMenu.GENE}>gene</Radio.Button>
      </Radio.Group>
      <div className={style.content}>{showContent(menuSelected)}</div>
    </div>
  );
};

export default LeftSiderBar;
