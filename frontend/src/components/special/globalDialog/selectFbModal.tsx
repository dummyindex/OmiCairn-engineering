import { useState, useEffect } from 'react';
import { Modal, Input, Checkbox, Button, Collapse } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useModel } from 'umi';

const { Panel } = Collapse;

// interface FunctionBlock {
//   id: number;
//   name: string;
//   altName: string | null;
//   state: string;
//   type: string;
//   createdTime: string;
//   currentVersionId: number;
//   groupId: number;
// }

// interface BlockGroup {
//   id: number;
//   name: string;
//   altName: string | null;
//   serialNumber: number;
//   createdTime: number;
//   functionBlockList: FunctionBlock[];
// }

const FunctionBlockSelectModal = () => {
  const { dictionary } = useModel('localization');
  const { functionBlockList } = useModel('functionBlock');
  const { selectedBlocks, setSelectedBlocks, isSelectFbModalOpen, setIsSelectFbModalOpen } =
    useModel('analysis');
  const [searchText, setSearchText] = useState('');
  const [tempSelectedBlocks, setTempSelectedBlocks] = useState<number[]>(selectedBlocks);

  useEffect(() => {
    if (isSelectFbModalOpen) {
      setTempSelectedBlocks(selectedBlocks);
    }
  }, [isSelectFbModalOpen, selectedBlocks]);

  const handleSearch = (value: string) => {
    setSearchText(value);
  };

  const handleCheckboxChange = (blockId: number, checked: boolean) => {
    setTempSelectedBlocks((prev) =>
      checked ? [...prev, blockId] : prev.filter((id) => id !== blockId),
    );
  };

  const handleGroupSelectAll = (groupId: number, checked: boolean) => {
    const groupBlocks =
      functionBlockList
        .find((group) => group.id === groupId)
        ?.functionBlockList.filter(
          (block) =>
            block.name.toLowerCase().includes(searchText.toLowerCase()) ||
            (block.altName && block.altName.toLowerCase().includes(searchText.toLowerCase())),
        )
        .map((block) => block.id) || [];

    setTempSelectedBlocks((prev) => {
      if (checked) {
        const newSelection = [...new Set([...prev, ...groupBlocks])];
        return newSelection;
      } else {
        return prev.filter((id) => !groupBlocks.includes(id));
      }
    });
  };

  const handleCancel = () => {
    setIsSelectFbModalOpen(false);
  };

  const handleApply = () => {
    setSelectedBlocks(tempSelectedBlocks);
    setIsSelectFbModalOpen(false);
  };

  const filteredGroups = functionBlockList
    .sort((a, b) => a.serialNumber - b.serialNumber)
    .map((group) => {
      const filteredBlocks = group.functionBlockList.filter(
        (block) =>
          block.name.toLowerCase().includes(searchText.toLowerCase()) ||
          (block.altName && block.altName.toLowerCase().includes(searchText.toLowerCase())),
      );
      return {
        ...group,
        functionBlockList: filteredBlocks,
      };
    })
    .filter((group) => group.functionBlockList.length > 0);

  const isGroupAllSelected = (groupId: number) => {
    const group = filteredGroups.find((g) => g.id === groupId);
    if (!group) return false;

    const groupBlockIds = group.functionBlockList.map((block) => block.id);
    return groupBlockIds.every((id) => tempSelectedBlocks.includes(id));
  };

  const isGroupPartiallySelected = (groupId: number) => {
    const group = filteredGroups.find((g) => g.id === groupId);
    if (!group) return false;

    const groupBlockIds = group.functionBlockList.map((block) => block.id);
    return (
      groupBlockIds.some((id) => tempSelectedBlocks.includes(id)) &&
      !groupBlockIds.every((id) => tempSelectedBlocks.includes(id))
    );
  };

  return (
    <Modal
      title={dictionary.SELECT_FUNCTION_BLOCK}
      centered
      width={600}
      bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          {dictionary.CANCEL}
        </Button>,
        <Button key="apply" type="primary" onClick={handleApply}>
          {dictionary.APPLY + ` (${tempSelectedBlocks.length})`}
        </Button>,
      ]}
      open={isSelectFbModalOpen}
      onCancel={handleCancel}
    >
      <div style={{ padding: '5px' }}>
        <Input
          allowClear
          placeholder="Input function block keywords"
          prefix={<SearchOutlined />}
          onChange={(e) => handleSearch(e.target.value)}
          value={searchText}
          style={{ marginBottom: '15px', padding: '5px' }}
        />
        <Collapse
          defaultActiveKey={filteredGroups.map((group) => group.id.toString())}
          bordered={false}
        >
          {filteredGroups.map((group) => (
            <Panel
              header={
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <span style={{ marginLeft: '8px', marginRight: '8px' }}>
                    {`${group.name} (${group.functionBlockList.length})`}
                  </span>
                  <Checkbox
                    checked={isGroupAllSelected(group.id)}
                    indeterminate={isGroupPartiallySelected(group.id)}
                    onChange={(e) => handleGroupSelectAll(group.id, e.target.checked)}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
              }
              key={group.id}
            >
              {group.functionBlockList.map((block) => (
                <div key={block.id} style={{ padding: '5px 0' }}>
                  <Checkbox
                    checked={tempSelectedBlocks.includes(block.id)}
                    onChange={(e) => handleCheckboxChange(block.id, e.target.checked)}
                  >
                    <span>
                      {`${block.name}`}
                    </span>
                  </Checkbox>
                </div>
              ))}
            </Panel>
          ))}
        </Collapse>
      </div>
    </Modal>
  );
};

export default FunctionBlockSelectModal;
