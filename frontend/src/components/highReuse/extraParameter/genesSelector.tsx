import { Button, Space, Tag } from 'antd';
import { useState } from 'react';
import { useModel } from 'umi';
import GenesSelectorModal from './genesSelector/genesSelectorModal';

const GenesSelector = (props: any) => {
  //   const { value, onEdit, valueRange } = props;
  const { value, nodeId, onChange } = props;

  const { loading, error } = useModel('visualPanelControl');
  const showedValue = value ? value.slice(0, 8) : [];

  const [showModal, setShowModal] = useState(false);

  const getDataAndShowModal = () => {
    setShowModal(true);
  };

  const onSubmit = (geneList: string[]) => {
    onChange(geneList);
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
        onClick={getDataAndShowModal}
        loading={loading}
        danger={error}
        disabled={loading || error}
      >
        Edit
      </Button>
      <GenesSelectorModal
        isOpen={showModal}
        setIsOpen={setShowModal}
        nodeId={nodeId}
        value={value}
        onSubmit={onSubmit}
      />
    </Space>
  );
};

export default GenesSelector;
