import { requestEdgeListOfAnalysis } from '@/request/edge';
import { requestNodeListOfAnalysis, requestUpdateNodePositionList } from '@/request/node';
import { AnalysisType } from '@/constants/analysis';
import {
  requestDeletePipelineTemplate,
  requestDeletePipelineTemplateGroup,
  requestEditPipelineTemplate,
  requestEditPipelineTemplateGroup,
  requestFBListInPT,
  requestGroupPipelineGet,
  requestImportPipelineTemplate,
  requestPipelineTemplateList,
  requestPublicPTGroupList,
  requestPublicPtList,
} from '@/request/pipeline';
import { AdobePagemaker } from '@/util/adobePagemaker';
import { formatTimeTool } from '@/util/formatTimeTool';
import { getLocationParams } from '@/util/getUrl';
import { cutString } from '@/util/stringHelpers';
import {
  DeleteFilled,
  DeleteOutlined,
  EditOutlined,
  QuestionCircleOutlined,
  ShareAltOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import {
  Button,
  Collapse,
  Form,
  Input,
  Menu,
  message,
  Popconfirm,
  Popover,
  Select,
  Spin,
  Tag,
} from 'antd';
import { useEffect, useState } from 'react';
import { useReactFlow } from 'reactflow';
import { useModel } from 'umi';
import style from './index.less';

const { Search } = Input;
const { Panel } = Collapse;

interface EditFormProps {
  item: string;
  onSubmit: (id: string, values: any) => Promise<void>;
}

const UpdateTemplateForm = (props: any) => {
  const { dictionary } = useModel('localization');
  const { item, form, groupList, onSubmit, categoryName } = props;
  const [value, setValue] = useState<string>();
  const options = groupList.map((item: string) => {
    return { value: item, label: item };
  });

  const handleChange = (value: string) => {
    setValue(value);
  };

  const onFinish = async (values: any) => {
    await onSubmit(item.id, values.categoryName, values.categoryGroup);
  };

  return (
    <Form form={form} onFinish={onFinish} labelAlign="right" autoComplete="off">
      <Form.Item
        label={dictionary.NAME}
        key="categoryName"
        required
        name="categoryName"
        initialValue={item.name}
      >
        <Input />
      </Form.Item>
      <Form.Item
        label={dictionary.CATEGORY}
        key="category"
        name="categoryGroup"
        initialValue={categoryName}
      >
        <Select
          placeholder="Please select the desired category group"
          onChange={handleChange}
          value={value}
          options={options}
        />
      </Form.Item>
      <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
        <Button type="primary" htmlType="submit">
          {dictionary.SUBMIT}
        </Button>
      </Form.Item>
    </Form>
  );
};

const EditForm = (props: EditFormProps) => {
  const { item, onSubmit } = props;
  const { dictionary } = useModel('localization');
  const onFinish = async (values: any) => {
    await onSubmit(item, values.name);
  };
  return (
    <Form
      name="basic"
      labelCol={{ span: 8 }}
      wrapperCol={{ span: 16 }}
      style={{ maxWidth: 600 }}
      initialValues={{ remember: true }}
      onFinish={onFinish}
      autoComplete="off"
    >
      <Form.Item label={dictionary.NAME} name="name" initialValue={item}>
        <Input />
      </Form.Item>
      <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
        <Button type="primary" htmlType="submit">
          {dictionary.SUBMIT}
        </Button>
      </Form.Item>
    </Form>
  );
};

const FBlist = (props: any) => {
  const { dictionary } = useModel('localization');
  const [fbListData, setFbListData] = useState([]);
  const [loading, setLoading] = useState(false);
  const { id } = props;
  const handlePanelChange = async (key: any) => {
    if (key.length === 0) {
      return;
    }
    setLoading(true);
    try {
      const { data } = await requestFBListInPT(key[0]); // Call the API to fetch the list data
      setFbListData(data); // Store the list data in state
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const uniqueArray = fbListData.map((item) => {
    return { [item.id]: item.name };
  });

  return (
    <Collapse
      size="small"
      style={{
        width: '100%',
        marginBottom: '8vh',
        marginTop: '0.5vh',
      }}
      onChange={handlePanelChange}
      bordered
    >
      <Panel key={id} header={dictionary.FB_LIST}>
        {loading ? (
          <Spin style={{ width: '100%' }} />
        ) : (
          uniqueArray.map((value: any) => {
            return (
              <Tag
                key={`${Object.keys(value)[0]}`}
                style={{
                  border: '1px solid #2949B0',
                  padding: '1px 10px',
                  marginRight: '1vw',
                  marginBottom: '1vw',
                  borderRadius: '3px',
                  lineHeight: '2.5vh',
                  textAlign: 'center',
                  backgroundColor: '#fff',
                }}
              >
                {value[Object.keys(value)[0]]}
              </Tag>
            );
          })
        )}
      </Panel>
    </Collapse>
  );
};

const Discription = (props: any) => {
  const { dictionary } = useModel('localization');
  const { text, id } = props;
  return (
    <Collapse
      size="small"
      style={{
        width: '100%',
        marginTop: '0.5vh',
      }}
      bordered
    >
      <Panel header={dictionary.DESCRIPTION} key={id}>
        {text}
      </Panel>
    </Collapse>
  );
};

export default function PipelineTemplate() {
  const { dictionary } = useModel('localization');
  const [analysisId] = getLocationParams(['analysis-id']);
  const [categoryName, setCategoryName] = useState('CategoryName');
  const [publicCategoryList, setPublicCategoryList] = useState([]);
  const [groupList, setGroupList] = useState([]);
  const [pipelineList, setPipelineList] = useState([] as any[]);
  const [filteredPipelineList, setFilteredPipelineList] = useState([] as any[]);
  const [searchQuery, setSearchQuery] = useState('');
  const [defaultSelectedKeys, setDefaultSelectedKeys] = useState([] as any[]);
  const [showEditCollection, setShowEditCollection] = useState(false);
  const { analysisAccessType, setNodes, setEdges, createNode, instance } = useModel('analysis');
  const { closeModal } = useModel('workflowHelper');
  const [openKeys, setOpenKeys] = useState<string[]>(['sub1']);
  const { setCenter } = useReactFlow();

  const onOpenChange: MenuProps['onOpenChange'] = (keys) => {
    setOpenKeys(keys);
  };

  const onSearch = (value: string) => {
    setSearchQuery(value);
    if (!value.trim()) {
      setFilteredPipelineList(pipelineList);
      return;
    }

    const filtered = pipelineList.filter((pipeline) =>
      pipeline.name.toLowerCase().includes(value.toLowerCase()),
    );
    setFilteredPipelineList(filtered);
  };

  useEffect(() => {
    setFilteredPipelineList(pipelineList);
  }, [pipelineList]);

  const getPublicPipelineList = async (groupName: string) => {
    const result = await requestPublicPtList(groupName);
    setPipelineList(result.data);
    setFilteredPipelineList(result.data);
    setCategoryName(groupName);
    setSearchQuery('');
  };

  const getPipelineList = async (groupName: string) => {
    const result = await requestPipelineTemplateList(groupName);
    setPipelineList(result.data);
    setFilteredPipelineList(result.data);
    setCategoryName(groupName);
    setSearchQuery('');
  };

  const community = (item: string) => {
    setShowEditCollection(false);
    getPublicPipelineList(item);
    setDefaultSelectedKeys([item]);
  };

  const personal = (item: string) => {
    setShowEditCollection(true);
    getPipelineList(item);
    setDefaultSelectedKeys([item]);
  };

  const getPublicGroupList = async () => {
    const { data } = await requestPublicPTGroupList();
    setPublicCategoryList(data);
    if (data && data.length > 0) {
      community(data[0]);
    }
    setCategoryName('CategoryName');
  };

  const getGroupList = async () => {
    const { data } = await requestGroupPipelineGet();
    setGroupList(data);
    // if (data[0]) {
    //   const { data: list } = await requestPipelineTemplateList(data[0]);
    //   setPipelineList(list);
    //   personal(data[0]);
    //   return;
    // }
    setCategoryName('CategoryName');
  };

  useEffect(() => {
    getPublicGroupList();
    getGroupList();
  }, []);

  const confirmEditCategoryName = async (oldName: string, newOld: string) => {
    await requestEditPipelineTemplateGroup(oldName, newOld);
    getGroupList();
  };

  const confirmEditTemplate = async (id: string, name: string, group: string) => {
    if (!categoryName) {
      message.warning('name is required!');
      return;
    }
    await requestEditPipelineTemplate(id, name, group);
    getPipelineList(categoryName);
  };

  const deleteTemplate = async (id: string) => {
    await requestDeletePipelineTemplate(id);
    getPipelineList(categoryName);
  };

  const deleteCategoryGroup = async (name: string) => {
    await requestDeletePipelineTemplateGroup(name);
    getGroupList();
  };

  // Import while preventing overlap
  const movePipeline = async (pipelineList, newNodeList) => {
    const nodeAdobePagemaker = new AdobePagemaker(instance);
    let fage = 0;
    let leftMostPositionX = 0;
    let rightMostPositionX = 0;
    let topMostPositionY = 0;

    while (true) {
      const currentY = 200 * fage;
      // eslint-disable-next-line @typescript-eslint/no-loop-func
      const nodesPositionList = pipelineList.newNodeList.map((item) => {
        if (item.x < leftMostPositionX) {
          leftMostPositionX = item.x;
        }
        if (item.x > rightMostPositionX) {
          rightMostPositionX = item.x;
        }
        if (item.y < topMostPositionY) {
          topMostPositionY = item.y;
        }
        return { x: item.x, y: item.y - currentY };
      });

      if (!nodeAdobePagemaker.judgePosition(nodesPositionList, null)) {
        const nodeList = pipelineList.newNodeList.map((item) => {
          const currentPositionX = item.x;
          const currentPositionY = item.y - currentY;
          newNodeList.forEach((element) => {
            if (item.id == element.id) {
              element.position.y = currentPositionY;
            }
          });
          return { node_id: item.id, x: currentPositionX, y: currentPositionY };
        });
        setNodes(() => [...newNodeList]);
        await requestUpdateNodePositionList(nodeList);
        setCenter((leftMostPositionX + rightMostPositionX) / 2, topMostPositionY, {
          duration: 0,
          zoom: 0.2,
        });
        break;
      }
      fage++;
    }
  };

  // Import
  const importPipeline = async (id: any) => {
    if (analysisId) {
      try {
        const { data: pipelineList } = await requestImportPipelineTemplate(
          id,
          parseInt(analysisId),
        );
        const [{ data: edgeList }, { data: nodeList }] = await Promise.all([
          requestEdgeListOfAnalysis(analysisId),
          requestNodeListOfAnalysis(analysisId),
        ]);

        const newEdges = edgeList.map((edge: any) => {
          return {
            id: String(edge.id),
            animated: true,
            source: String(edge.sourceNodeId),
            target: String(edge.targetNodeId),
          };
        });
        const newNodes = nodeList.map((node: any) => {
          return createNode(node);
        });

        setEdges(() => [...newEdges]);
        await movePipeline(pipelineList, newNodes);
        closeModal();
        message.success('Import was successful');
      } catch (e) {
        console.error(e);
        message.error('Import failed');
      }
    }
  };

  return (
    <div className={style.piplineTemplate}>
      <Search
        placeholder={dictionary.SEARCH}
        allowClear
        onSearch={onSearch}
        value={searchQuery}
        onChange={(e) => onSearch(e.target.value)}
        size="large"
        style={{
          marginBottom: '2.5vh',
        }}
      />
      <div
        style={{
          height: '60vh',
          marginBottom: '9vh',
          display: 'flex',
          justifyContent: 'space-between',
        }}
      >
        <Menu
          mode="inline"
          openKeys={openKeys}
          onOpenChange={onOpenChange}
          selectedKeys={defaultSelectedKeys}
          defaultOpenKeys={['sub1']}
          style={{ width: '13vw', overflow: 'auto' }}
        >
          <Menu.SubMenu
            key="sub1"
            title={
              <span>
                <span
                  style={{
                    fontWeight: '600',
                    fontSize: '12px',
                  }}
                >
                  Community Template
                </span>
              </span>
            }
          >
            {publicCategoryList.map((item) => {
              return (
                <Menu.Item
                  key={item}
                  style={{
                    padding: '0 2vw',
                    margin: '1vh auto',
                    color: '#333',
                    fontWeight: '600',
                    fontSize: '12px',
                    textAlign: 'center',
                    height: '4vh',
                    lineHeight: '4vh',
                    borderRadius: ' 17px',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      paddingLeft: '1vw',
                      paddingRight: '1vw',
                    }}
                    title={item}
                    onClick={() => {
                      community(item);
                    }}
                  >
                    {cutString(item, 13)}
                  </div>
                </Menu.Item>
              );
            })}
          </Menu.SubMenu>
          <Menu.SubMenu
            key="sub2"
            title={
              <span>
                <span
                  style={{
                    fontWeight: '600',
                    fontSize: '12px',
                  }}
                >
                  My Templates
                </span>
              </span>
            }
          >
            {groupList.map((item) => {
              return (
                <Menu.Item
                  key={item}
                  style={{
                    padding: '0 1vw',
                    margin: '1vh auto',
                    color: '#333',
                    fontWeight: '600',
                    fontSize: '12px',
                    textAlign: 'center',
                    height: '4vh',
                    lineHeight: '4vh',
                    borderRadius: ' 17px',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      paddingLeft: '1vw',
                      paddingRight: '1vw',
                    }}
                    title={item}
                    onClick={() => {
                      personal(item);
                    }}
                  >
                    <div style={{ flex: 1 }}>{cutString(item, 10)}</div>
                    <Popover
                      title={dictionary.EDIT}
                      content={<EditForm item={item} onSubmit={confirmEditCategoryName} />}
                    >
                      <EditOutlined
                        className={style.editCategoryName}
                        style={{
                          paddingLeft: '1vw',
                          paddingRight: '1vw',
                        }}
                      />
                    </Popover>

                    <Popconfirm
                      placement="rightBottom"
                      title={dictionary.DELETE}
                      description="Are you sure you want to delete this category group?"
                      icon={
                        <QuestionCircleOutlined
                          style={{
                            color: 'red',
                          }}
                        />
                      }
                      onConfirm={() => {
                        deleteCategoryGroup(item);
                      }}
                    >
                      <DeleteOutlined className={style.editCategoryName} />
                    </Popconfirm>
                  </div>
                </Menu.Item>
              );
            })}
          </Menu.SubMenu>
        </Menu>

        <div
          className={style.list}
          style={{
            height: '100%',
            width: '43vw',
          }}
        >
          <div className={style.categoryName}>{categoryName}</div>
          <div
            style={{
              width: '44vw',
              height: '55vh',
              overflow: 'auto',
              paddingRight: '3vh',
            }}
          >
            {filteredPipelineList.map((item) => {
              return (
                <div
                  key={item.id}
                  className={style.template}
                  style={{
                    width: '100%',
                  }}
                >
                  <div className={style.templateName}>
                    <div>
                      <div
                        style={{
                          fontSize: '14px',
                          fontWeight: '600',
                        }}
                      >
                        {item.name}
                      </div>
                      <div
                        style={{
                          fontSize: '12px',
                          fontWeight: '500',
                        }}
                      >
                        {dictionary.CREATED_AT}: {formatTimeTool(item.createdTime)}
                      </div>
                    </div>
                    <div className={style.templateNameHead}>
                      {showEditCollection ? (
                        <div style={{ display: 'flex' }}>
                          <div className={style.editCollection}>
                            <Popconfirm
                              title="Delete the task"
                              description="Are you sure to delete this task?"
                              icon={
                                <QuestionCircleOutlined
                                  style={{
                                    color: 'red',
                                  }}
                                />
                              }
                              onConfirm={() => {
                                deleteTemplate(item.id);
                              }}
                            >
                              <DeleteFilled
                                style={{
                                  marginRight: '0.5vw',
                                  color: '#5971C0',
                                }}
                              />
                              {dictionary.DELETE}
                            </Popconfirm>
                          </div>
                          <Popover
                            title={'Edit Category information'}
                            content={
                              <UpdateTemplateForm
                                categoryName={categoryName}
                                groupList={groupList}
                                item={item}
                                onSubmit={confirmEditTemplate}
                              />
                            }
                          >
                            <div className={style.editCollection}>
                              <EditOutlined
                                style={{
                                  marginRight: '0.5vw',
                                  color: '#5971C0',
                                }}
                              />
                              {dictionary.EDIT}
                            </div>
                          </Popover>
                        </div>
                      ) : null}
                      <div
                        className={
                          analysisAccessType === AnalysisType.PUBLIC
                            ? style.importPiplineDisabled
                            : style.importPipline
                        }
                        onClick={() => {
                          if (analysisAccessType !== AnalysisType.PUBLIC) {
                            importPipeline(item.id);
                          }
                        }}
                      >
                        <ShareAltOutlined
                          style={{
                            marginRight: '0.5vw',
                          }}
                        />
                        {dictionary.IMPORT_PIPELINE}
                      </div>
                    </div>
                  </div>
                  {item.description && <Discription text={item.description} id={item.id} />}
                  <FBlist id={item.id} />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
