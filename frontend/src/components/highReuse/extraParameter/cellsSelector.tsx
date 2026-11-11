import { Button, Space, Tag } from 'antd';
import { useModel } from 'umi';
import CellVisualizationSelector from './cellsSelector/index';

const CellsSelector = (props: any) => {
  const { value, nodeId, onChange } = props;

  const { loading, error, setOpen } = useModel('cellSelect');
  const showedValue = value ? value.slice(0, 8) : [];

  const cancelShowModal = () => {
    setOpen(false);
  };

  const getDataAndShowModal = () => {
    setOpen(true);
  };

  const onSubmit = (cellList: string[]) => {
    onChange(cellList);
  };

  return (
    <Space size={[0, 8]} wrap>
      {value && value.length > 8 ? (
        <div>
          {showedValue.map((item: string) => {
            return (
              <Tag color="blue" key={item} style={{ margin: '3px' }}>
                {item}
              </Tag>
            );
          })}
          ...
        </div>
      ) : (
        showedValue.map((item: string) => {
          return (
            <Tag color="blue" key={item} style={{ margin: '3px' }}>
              {item}
            </Tag>
          );
        })
      )}

      <Button
        type="primary"
        loading={loading}
        danger={error}
        // disabled={loading || error}
        onClick={getDataAndShowModal}
      >
        Edit
      </Button>
      <CellVisualizationSelector
        nodeId={nodeId}
        // dataStructure={dataStructure}
        value={value}
        onSubmit={onSubmit}
        cancelShowModal={cancelShowModal}
      />
    </Space>
  );
};

export default CellsSelector;
