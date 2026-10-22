import { useState, useEffect, useRef } from 'react';
import { Input, Button, Tabs, Empty, Dropdown, Menu } from 'antd';
import { DownOutlined, SearchOutlined } from '@ant-design/icons';
import './allApps.css';
import { Form, message } from 'antd';
import { requestCollectedMiniAppList } from '@/request/functionBlock';
import { requestEditNodeParams, requestMiniToolTruckNode, requestNodeInfo } from '@/request/node';
import { NodeState } from '@/constants/node';
import { requestDispatchTask } from '@/request/task';
import { SpecialAnalysis } from '@/constants/analysis';
import AppDescription from '@/components/special/allApps/description';
import MiniToolApplication from '@/components/special/allApps/application';
import RunHistory from '@/components/special/allApps/runHistory';
import { requestLatestComputation } from '@/request/computation';
import { useModel } from 'umi';

type AppType = {
  name: string;
  id: string;
  description: string;
  tags: string[];
  collectedTime: string;
  args?: any;
};

const { Search } = Input;

// const Description

const AllApps = () => {
  const [selectedApp, setSelectedApp] = useState<AppType | null>(null);
  const [appSwitching, setAppSwitching] = useState<boolean>(false);
  const [truckNode, setTruckNode] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filter, setFilter] = useState<string>('all');
  const [startingTask, setStartingTask] = useState<boolean>(false);
  const [currentTab, setCurrentTab] = useState<string>('description' as string);
  const [apps, setApps] = useState<AppType[]>([]);
  const [displayedComputation, setDisplayedComputation] = useState<any>(null);
  const { dictionary } = useModel('localization');

  const refreshNodeTimer = useRef<any>(null);

  // const [loading, setLoading] = useState(false);
  // const [error, setError] = useState(null);
  const [paramsList, setParamsList] = useState([]);
  const [form] = Form.useForm();

  const loadMore = async () => {
    const { data: result } = await requestCollectedMiniAppList(0, 100, searchTerm);
    setApps(result);
  };

  const loadFormLoadInfo = async () => {
    if (!selectedApp) return;
    setAppSwitching(true);
    try {
      // Load mounted nodes
      const { data: newTruckNode } = await requestMiniToolTruckNode(selectedApp.id);
      const { computationParams: paramsStr } = newTruckNode;
      const params = JSON.parse(paramsStr);
      delete newTruckNode.computationParams;
      setTruckNode(newTruckNode);
      setParamsList(selectedApp.args);
      form.setFieldsValue(params);
    } catch (e) {
      form.resetFields();
      setTruckNode(null);
      setParamsList([]);
      console.error(e);
    } finally {
      setAppSwitching(false);
    }
  };

  const refreshNode = async () => {
    if (!truckNode) return;
    const newTruckNode = await requestNodeInfo(truckNode.id);
    if (!newTruckNode || newTruckNode.id !== truckNode.id) return;
    if (newTruckNode.state !== truckNode.state) {
      setTruckNode(newTruckNode);

      if (newTruckNode.state === NodeState.FINISHED) {
        const { data: newComputation } = await requestLatestComputation(newTruckNode.id);
        setDisplayedComputation(newComputation);
        setCurrentTab('runHistory');
      }
    }
  };

  useEffect(() => {
    loadMore();
  }, [searchTerm]);

  useEffect(() => {
    loadFormLoadInfo();
  }, [selectedApp]);

  useEffect(() => {
    refreshNodeTimer.current = setInterval(() => {
      refreshNode();
    }, 5000);
    return () => {
      clearInterval(refreshNodeTimer.current);
    };
  }, [truckNode]);

  const selectApp = (app: AppType) => {
    setSelectedApp({
      ...app,
      args: app.args && JSON.parse(app.args),
    });
  };

  const startTask = async () => {
    setStartingTask(true);
    try {
      const values = await form.validateFields();
      console.log(values);
      const { code: paramsEditedRCode } = await requestEditNodeParams(truckNode.id, values);
      console.log('The result code of editing parameters:', paramsEditedRCode);
      const { code: dispatchTaskRCode } = await requestDispatchTask(
        SpecialAnalysis.MINI_TOOL + '',
        [truckNode.id],
        [],
      );
      console.log('The result code of dispatching task:', dispatchTaskRCode);
      message.success('Task submitted successfully');
      setTruckNode({
        ...truckNode,
        state: NodeState.PENDING,
      });
    } catch (e) {
      console.error(e);
      message.error('Task submission failed');
    } finally {
      setStartingTask(false);
    }
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
  };

  const clearSearch = () => {
    setSearchTerm('');
  };

  const menu = (
    <Menu onClick={(e) => setFilter(e.key)}>
      <Menu.Item key="all">All apps</Menu.Item>
      <Menu.Item key="private">Private apps</Menu.Item>
      <Menu.Item key="public">Public apps</Menu.Item>
    </Menu>
  );

  const loading =
    appSwitching ||
    [NodeState.PENDING, NodeState.RUNNING].includes(truckNode?.state) ||
    startingTask;

  return (
    <div
      style={{
        height: '95vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
        alignItems: 'stretch',
        padding: '2em',
      }}
    >
      <div>
        <Search
          style={{
            width: '50%',
            marginTop: '-1em',
            marginBottom: '1em',
          }}
          placeholder={dictionary.SEARCH}
          value={searchTerm}
          onSearch={handleSearch}
          onChange={(e) => handleSearch(e.target.value)}
          prefix={<SearchOutlined />}
        />
      </div>
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'row',
          justifyContent: 'flex-start',
          overflow: 'auto',
          alignItems: 'stretch',
        }}
      >
        <div
          style={{
            width: '45%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-start',
            alignItems: 'stretch',
          }}
        >
          <div
            style={{
              height: '7vh',
              display: 'flex',
              flexDirection: 'row',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <h2>{dictionary.MY_LIBRARIES}</h2>
            {searchTerm && (
              <Button className="btn-clear-search" onClick={clearSearch}>
                Clear Search
              </Button>
            )}
            <Dropdown overlay={menu} trigger={['click']}>
              <a className="ant-dropdown-link" onClick={(e) => e.preventDefault()}>
                Filter: {filter.charAt(0).toUpperCase() + filter.slice(1)}{' '}
                <span>
                  <DownOutlined />
                </span>
              </a>
            </Dropdown>
          </div>
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
            }}
          >
            {apps.length ? (
              apps.map((app) => {
                return (
                  <div
                    key={app.id}
                    style={{
                      padding: '0.75em 1em 0.75em 1.25em',
                      borderRadius: '0.5em',
                      margin: '0 0.7em 1em 0',
                      backgroundColor: 'white',
                      boxShadow: '0 0 2px rgba(0, 0, 0, 0.1)',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'flex-start',
                      gap: '1em',
                      cursor: 'pointer',
                      border: selectedApp?.id === app.id ? '1px solid #1890ff' : 'none',
                    }}
                    onClick={() => {
                      selectApp(app);
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'row',
                        justifyContent: 'flex-start',
                        alignItems: 'center',
                      }}
                    >
                      <div
                        style={{
                          fontSize: '1.3em',
                          fontWeight: '500',
                        }}
                      >
                        {app.name}
                      </div>
                      <div
                        style={{
                          flex: 1,
                        }}
                      />
                      <div
                        style={{
                          fontSize: '0.8em',
                          color: 'rgba(0, 0, 0, 0.5)',
                        }}
                      >
                        Collected At {app.createdTime}
                      </div>
                    </div>
                    {/* <div>
                    {app.tags.map((tag) => (
                      <Tag color="blue" key={tag}>
                        {tag}
                      </Tag>
                    ))}
                  </div> */}
                    <div
                      style={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {app.description}
                    </div>
                  </div>
                );
              })
            ) : (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="No apps found"
                style={{
                  margin: '0 1em',
                }}
              />
            )}
          </div>
        </div>
        <div
          style={{
            width: '54%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-start',
            alignItems: 'stretch',
          }}
        >
          <div
            style={{
              height: '0vh',
            }}
          />
          <div
            style={{
              flex: 1,
              backgroundColor: 'white',
              margin: '3.8em 1em 0 2em',
              borderRadius: '0.5em',
            }}
          >
            {!selectedApp && (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="Select an app to view details"
              />
            )}
            {!!selectedApp && (
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'flex-start',
                  alignItems: 'stretch',
                  padding: '0.3em 1.25em',
                }}
              >
                <div
                  style={{
                    fontSize: '1.2em',
                    fontWeight: '500',
                    lineHeight: '3em',
                  }}
                >
                  {selectedApp?.name}
                </div>

                <div style={{ marginTop: '-0.1em' }}>
                  <Tabs
                    activeKey={currentTab}
                    onChange={(key) => setCurrentTab(key)}
                    items={[
                      {
                        label: dictionary.DESCRIPTION,
                        key: 'description',
                        children: <AppDescription app={selectedApp} />,
                      },
                      {
                        label: dictionary.APPLICATION,
                        key: 'application',
                        children: (
                          <MiniToolApplication
                            form={form}
                            loading={loading}
                            paramList={paramsList}
                            startTask={startTask}
                            truckNode={truckNode}
                          />
                        ),
                      },
                      {
                        label: dictionary.RUN_HISTORY,
                        key: 'runHistory',
                        children: (
                          <RunHistory
                            displayedComputation={displayedComputation}
                            setDisplayedComputation={setDisplayedComputation}
                            truckNode={truckNode}
                          />
                        ),
                      },
                    ]}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AllApps;
