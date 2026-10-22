import { NodeType } from '@/constants/node';
import { AnalysisType } from '@/constants/analysis';
import { requestCreateFBGroup, requestSearchFunctionBlockMenuList } from '@/request/functionBlock';
import { QuestionCircleOutlined, MoreOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';
import {
  AutoComplete,
  Button,
  Form,
  Input,
  Menu,
  Modal,
  Tooltip,
  message,
  Dropdown,
  Row,
  Col,
} from 'antd';
import React, { useEffect, useState } from 'react';
import type { MouseEventHandler } from 'react';
import { useModel } from 'umi';
import { FunctionBlockTool } from '@/util/functionBlock';
import { FunctionBlockState } from '@/constants/functionBlock';

const CreateGroup = (props) => {
  const { showCreateGroupUI, setShowCreateGroupUI } = props;
  const { analysisAccessType } = useModel('analysis');
  const { dictionary } = useModel('localization');
  const { loadFBList } = useModel('functionBlock');
  const [form] = Form.useForm();
  const createFbGroup = async () => {
    const { name } = await form.validateFields();
    await requestCreateFBGroup(name);
    loadFBList();
    setShowCreateGroupUI(false);
  };
  return (
    <div>
      <Modal
        centered
        destroyOnClose
        open={showCreateGroupUI}
        onOk={() => {
          createFbGroup();
        }}
        onCancel={() => setShowCreateGroupUI(false)}
        title={dictionary.CREATE_GROUP}
        width="20vw"
        footer={[
          <Button key="back" onClick={() => setShowCreateGroupUI(false)}>
            {dictionary.CANCEL}
          </Button>,
          <Button
            disabled={analysisAccessType === AnalysisType.PUBLIC}
            type="primary"
            key="submit"
            onClick={() => createFbGroup()}
          >
            {dictionary.CREATE}
          </Button>,
        ]}
      >
        <Form form={form} autoComplete="off">
          <Form.Item
            label={dictionary.NAME}
            name="name"
            rules={[{ required: true, message: 'Group cannot be empty!' }]}
          >
            <Input placeholder="Please enter a group name" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

type FunctionBlockCandidateProps = {
  key: string;
  name: string;
  label: string;
  state: string;
  isV2: boolean;
  programLanguage: string;
  editable: boolean;
  upgradable: boolean;
  onDragStart: MouseEventHandler;
  onShowDetail: MouseEventHandler;
  onEditClick?: MouseEventHandler;
  onUpgradeClick?: MouseEventHandler;
};

const FunctionBlockCandidate = (props: FunctionBlockCandidateProps) => {
  const {
    key,
    name,
    label,
    state,
    isV2,
    // programLanguage,
    editable,
    upgradable,
    onDragStart,
    onShowDetail,
    onEditClick,
    onUpgradeClick,
  } = props;

  const { userInfo } = useModel('user');
  const { analysisAccessType } = useModel('analysis');
  const onClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'upgrade') {
      onUpgradeClick?.(key);
    } else if (key === 'change') {
      onEditClick?.(key);
    }
  };

  const items: MenuProps['items'] = [
    {
      label: 'upgrade',
      key: 'upgrade',
      disabled: !upgradable,
    },
    {
      label: 'change',
      key: 'change',
      disabled: !editable,
    },
  ];

  const renderDropDown = () => {
    return (
      <Dropdown menu={{ items, onClick }}>
        <Button icon={<MoreOutlined />} size="small" type="text" />
      </Dropdown>
    );
  };

  const disabled = userInfo?.id + '' !== '0' && analysisAccessType === AnalysisType.PUBLIC;

  return (
    <Menu.Item
      key={key}
      disabled={disabled}
      onDragStart={(event: React.MouseEvent<Element, MouseEvent>) => {
        onDragStart(event);
      }}
      style={{
        padding: '0',
        margin: '1vh auto' /*  */,
        color: '#333',
        fontWeight: '600',
        fontSize: '12px',
        width: '10vw',
        height: '4vh',
        lineHeight: '4vh',
        borderRadius: '8px',
        border: '1px solid #333',
        backgroundColor: FunctionBlockTool.getFBColor(state, isV2),
      }}
      draggable
    >
      <Row
        style={{
          width: '10vw',
          height: '4vh',
          display: 'flex',
          justifyContent: 'space-between',
        }}
      >
        <Col span={1} />
        <Col
          span={15}
          style={{
            overflow: 'hidden',
            whiteSpace: 'nowrap',
            textOverflow: 'ellipsis',
            display: 'inline-block',
          }}
        >
          <Tooltip title={name} placement="bottomRight">
            {label}
          </Tooltip>
        </Col>
        <Col span={2} />
        <Col span={3}>
          <Button
            icon={<QuestionCircleOutlined />}
            onClick={(event: React.MouseEvent<Element, MouseEvent>) => {
              event.stopPropagation();
              onShowDetail(event);
            }}
            size="small"
            type="text"
          />
        </Col>
        <Col span={2}>{renderDropDown()}</Col>
        <Col span={1} />
      </Row>
    </Menu.Item>
  );
};

const FunctionBlockList: React.FC = () => {
  const { dictionary } = useModel('localization');
  const { functionBlockList, functionBlockPrivateList } = useModel('functionBlock');
  const { openUploadFbModal } = useModel('functionBlockCreate');
  const { setUpdatedFBId } = useModel('functionBlockUpdate');
  const { openModal: openFBVersionSwitchModal } = useModel('functionBlockVersionSwitch');
  const { showModal: showDetailModal } = useModel('functionBlockDetail');
  const { isGuest } = useModel('user');
  const { analysisAccessType } = useModel('analysis');
  const [FBList, setFBList] = useState<any[]>([]);
  const [filteredFBList, setFilteredFBList] = useState<any[]>([]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchValue, setSearchValue] = useState<string>('');

  // Upload function block
  const [showCreateGroupUI, setShowCreateGroupUI] = useState(false);
  const isGuestUser = isGuest();

  useEffect(() => {
    if (functionBlockList && functionBlockList.length > 0) {
      const defaultItemList: any[] = [];
      const privateItemList: any[] = [];
      functionBlockList.forEach((item) => {
        item.functionBlockList.forEach((value) => {
          defaultItemList.push({ label: value.name, value: `${item.id}/${value.id}` });
          return value.name;
        });
      });
      functionBlockPrivateList.forEach((item) => {
        item.functionBlockList.forEach((value) => {
          privateItemList.push({ label: value.name, value: `${item.id}/${value.id}` });
          return value.name;
        });
      });
      const functionBlockListCopy = [...functionBlockList];
      const FBlist = functionBlockListCopy.sort(function (a, b) {
        return a.serialNumber - b.serialNumber; // Sort ascending by serialNumber
      });

      // Filter out the item with name "__bug_fixer_generated__" and the item with name "__dynamic_fb_generated__"
      const filteredFBlist = FBlist.filter(
        (item) =>
          item.name !== '__bug_fixer_generated__' && item.name !== '__dynamic_fb_generated__',
      );
      const filteredPrivateFBlist = functionBlockPrivateList.filter(
        (item) =>
          item.name !== '__bug_fixer_generated__' && item.name !== '__dynamic_fb_generated__',
      );

      setFBList([
        { group: 'public', list: filteredFBlist },
        { group: 'private', list: filteredPrivateFBlist },
      ]);
    }
  }, [functionBlockList, functionBlockPrivateList]);

  const onDragStart = (evt: any, node: any, id: number) => {
    const { state } = node;
    if (analysisAccessType === AnalysisType.PUBLIC) {
      evt.preventDefault();
      message.warning('guests cannot drag function blocks!');
      return;
    }
    // Block dragging
    if (state !== FunctionBlockState.OK) {
      evt.preventDefault();
      message.warning(`Function block with ${state || 'null'} state cannot be dragged!`);
      return;
    }
    // Record the type of the dragged node
    evt.dataTransfer.setData('node-type', NodeType.COMPUTATION_NODE);
    evt.dataTransfer.setData('label', node.name);
    evt.dataTransfer.setData('fb-id', id);
    evt.dataTransfer.setData('fb-name', node.name);
    evt.dataTransfer.effectAllowed = 'move';
  };

  const [openKeys, setOpenKeys] = useState(['public', 'private']);

  const onOpenChange: MenuProps['onOpenChange'] = (keys: string[]) => {
    const latestOpenKey = keys.find((key: string) => openKeys.indexOf(key) === -1);
    if (openKeys.indexOf(latestOpenKey!) === -1) {
      setOpenKeys(keys);
    } else {
      setOpenKeys(latestOpenKey ? openKeys.concat([latestOpenKey]) : []);
    }
  };

  const handleSearch = async (value: string) => {
    setSearchValue(value);
    if (value.trim() === '') {
      setSearchResults([]);
      setFilteredFBList(FBList);
      return;
    }

    try {
      const result = await requestSearchFunctionBlockMenuList(value);
      if (result) {
        const options = result.data.map((item: any) => ({
          value: item.fb_name,
          key: item.fb_id,
          fb_id: item.fb_id,
          fb_name: item.fb_name,
          description: item.description,
          source: item.source,
          label: (
            <div>
              <strong>{item.fb_name}</strong>
              <div style={{ fontSize: '12px', color: '#888' }}>
                <span>{dictionary.DESCRIPTION}:</span>{' '}
                {item.description
                  ? item.description.length > 100
                    ? `${item.description.substring(0, 100)}...`
                    : item.description
                  : 'No description available'}
              </div>
              <div style={{ fontSize: '12px', color: 'gray' }}>
                <span>{dictionary.SOURCE}:</span> {item.source || 'N/A'}
              </div>
            </div>
          ),
        }));
        setSearchResults(options);
      }
    } catch (error) {
      console.error('Error fetching search results:', error);
    }
  };

  const handleSelect = (value: string, option: any) => {
    setSearchValue(value);

    const filteredList = FBList.map((group) => ({
      ...group,
      list: group.list
        .map((item) => ({
          ...item,
          functionBlockList: item.functionBlockList.filter((fb: any) => fb.name === option.value),
        }))
        .filter((item) => item.functionBlockList.length > 0),
    })).filter((group) => group.list.length > 0);

    setFilteredFBList(filteredList);
  };

  useEffect(() => {
    setFilteredFBList(FBList);
  }, [FBList]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        gap: '1em',
        marginTop: '1em',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '1em',
          padding: '0 1.5em',
        }}
      >
        <Button
          type="default"
          style={{
            flex: 1,
          }}
          size="small"
          onClick={() => setShowCreateGroupUI(true)}
          disabled={analysisAccessType === AnalysisType.PUBLIC || isGuestUser}
        >
          {dictionary.CREATE_GROUP}
        </Button>
        <Button
          type="default"
          style={{
            flex: 1,
          }}
          size="small"
          onClick={() => openUploadFbModal()}
        >
          {dictionary.UPLOAD}
        </Button>
        <CreateGroup
          showCreateGroupUI={showCreateGroupUI}
          setShowCreateGroupUI={setShowCreateGroupUI}
        />
      </div>
      <div
        style={{
          padding: '0 1.5em',
        }}
      >
        <AutoComplete
          style={{ width: '100%' }}
          value={searchValue}
          onSearch={handleSearch}
          onSelect={handleSelect}
          options={searchResults}
          placeholder={dictionary.SEARCH}
          allowClear
        >
          <Input.Search allowClear />
        </AutoComplete>
      </div>
      <Menu mode="inline" openKeys={openKeys} onOpenChange={onOpenChange}>
        {filteredFBList.map((groupItem) => (
          <Menu.SubMenu
            key={groupItem.group}
            title={
              <span style={{ fontWeight: '600' }}>{dictionary[groupItem.group.toUpperCase()]}</span>
            }
          >
            {groupItem.list.map((item) => (
              <Menu.SubMenu
                key={`${item.id}`}
                title={`${item.name} (${
                  item.functionBlockList.length
                })`}
              >
                {item.functionBlockList.map((value: any) => (
                  <FunctionBlockCandidate
                    key={`menu${value.groupId}-${value.id}`}
                    name={value.name}
                    label={value.name}
                    state={value.state}
                    isV2={value.isV2}
                    programLanguage={value.programLanguage}
                    editable={groupItem.group === 'private'}
                    upgradable={groupItem.group === 'private'}
                    onDragStart={(e) => onDragStart(e, value, value.id)}
                    onShowDetail={() => showDetailModal(value.id)}
                    onEditClick={() => {
                      openFBVersionSwitchModal(value.id);
                    }}
                    onUpgradeClick={() => {
                      setUpdatedFBId(value.id);
                    }}
                  />
                ))}
              </Menu.SubMenu>
            ))}
          </Menu.SubMenu>
        ))}
      </Menu>
    </div>
  );
};

export default FunctionBlockList;
