import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { DataListFetchMode } from '@/constants/data';
import type { DataType } from '@/interfaces/data';
import { downloadFile } from '@/request/awsOperation';
import {
  requestDataEdit,
  requestDataReferencedState,
  requestDataSourceList,
  requestDeleteDataSource,
  requestDownloadDataSource,
} from '@/request/data';
import {
  CloseCircleOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  PlusOutlined,
  QuestionOutlined,
  RollbackOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import {
  Button,
  Divider,
  Dropdown,
  Form,
  Input,
  Menu,
  message,
  Modal,
  Popconfirm,
  Popover,
  Switch,
  Table,
  Tooltip,
} from 'antd';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { history, useLocation, useModel } from 'umi';
import style from './myDataBlock.less';

interface EditFormProps {
  item: DataType;
  onSubmit: (id: string, values: any) => Promise<void>;
}

const EditForm = (props: EditFormProps) => {
  const { item, onSubmit } = props;
  const { dictionary } = useModel('localization');
  const onFinish = async (values: any) => {
    await onSubmit(item.id, values);
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
      <Form.Item label="name" name="name" initialValue={item.name}>
        <Input />
      </Form.Item>

      <Form.Item label="description" name="description" initialValue={item.description}>
        <Input
          allowClear={{
            clearIcon: <CloseCircleOutlined />,
          }}
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

const formatFileSize = (bytes: number): string => {
  if (!bytes || bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${units[i]}`;
};

const MyDataBlock = () => {
  const [pollInterval] = useState<number>(10000);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const [searchKey, setSearchKey] = useState('');

  const [dataList, setDataList] = React.useState([] as DataType[]);
  const [loading, setLoading] = React.useState(false as boolean);
  const [errorMsgShow, setErrorMsgShow] = React.useState(false as boolean);
  const [errorMessage, setErrorMessage] = React.useState<string>('');

  const [isDataFilterEnabled, setIsDataFilterEnabled] = useState(true);

  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [selectedRows, setSelectedRows] = useState<DataType[]>([]);

  const { openUploadDataUI, showUploadDataUI, isAnndataUploadSuccess } = useModel('uploadDataUI');
  const {
    setIsThirdPartyDataListModalVisible: setThirdPartyDataSourceModalVisible,
    setDataCaptureModalVisible,
  } = useModel('thirdPartyDataSource');
  const { currentAnalysisId } = useModel('thirdPartyDataSource');

  const { dictionary } = useModel('localization');
  const { isGuest } = useModel('user');
  const location = useLocation();
  const highlightId = new URLSearchParams(location.search).get('highlightId');
  const highlightedRowRef = useRef<HTMLElement | null>(null);

  const [currentPage, setCurrentPage] = useState(1);
  const [isSearchingHighlightedRow, setIsSearchingHighlightedRow] = useState(false);
  const previousPageRef = useRef(currentPage);
  const currentPageRef = useRef(currentPage);
  const isGuestUser = isGuest();

  useEffect(() => {
    currentPageRef.current = currentPage;
  }, [currentPage]);

  const findAndHighlightRow = useCallback(async () => {
    if (!highlightId) return;

    const element = document.getElementById(highlightId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      element.classList.add(style.highlightRow);
      highlightedRowRef.current = element;
      setTimeout(() => {
        element.classList.remove(style.highlightRow);
        element.classList.add(style.normalRow);
      }, 2000);
      setIsSearchingHighlightedRow(false);
      return;
    }

    const totalPages = Math.ceil(dataList.length / 10);
    if (currentPageRef.current < totalPages) {
      setCurrentPage((prev) => prev + 1);
    } else {
      message.error('Could not find the specified data row');
      setIsSearchingHighlightedRow(false);
      setCurrentPage(previousPageRef.current);
    }
  }, [highlightId, dataList.length]);

  useEffect(() => {
    if (highlightId && !isSearchingHighlightedRow) {
      previousPageRef.current = currentPage;

      if (isDataFilterEnabled) {
        setIsDataFilterEnabled(false);
      }

      setIsSearchingHighlightedRow(true);
      setCurrentPage(1);
    }
  }, [highlightId]);

  useEffect(() => {
    if (isSearchingHighlightedRow) {
      const timeoutId = setTimeout(() => {
        findAndHighlightRow();
      }, 100);

      return () => clearTimeout(timeoutId);
    }
  }, [findAndHighlightRow, isSearchingHighlightedRow, currentPage]);

  const deleteData = async (id: string) => {
    const { data: referenced } = await requestDataReferencedState(id);
    if (referenced) {
      Modal.confirm({
        title: 'This Data is referenced by one or more nodes.',
        content:
          'This Data is referenced by one or more nodes. If you delete it, the nodes will be affected. Are you sure to delete this data?',
        async onOk() {
          setLoading(true);
          await requestDeleteDataSource(id);
          const dataListAfterDelete = dataList.filter((item: DataType) => item.id !== id);
          setDataList(dataListAfterDelete);
          setLoading(false);
        },
        onCancel() {
          message.info('Canceled');
        },
      });
    } else {
      setLoading(true);
      await requestDeleteDataSource(id);
      const dataListAfterDelete = dataList.filter((item: DataType) => item.id !== id);
      setDataList(dataListAfterDelete);
      setLoading(false);
    }
  };

  const loadDataList = async (searchKeyParam?: string) => {
    setLoading(true);
    try {
      const isGuest = localStorage.getItem('isGuest') === 'true';

      if (isGuest) {
        setDataList([]);
      } else {
        const { data: dataList } = await requestDataSourceList(
          DataListFetchMode.ALL,
          null,
          searchKeyParam,
        );
        const dataListWithKey = dataList.map((item: DataType) => ({
          ...item,
          key: item.id,
        }));
        dataListWithKey.sort((a, b) => b.createdTime - a.createdTime);
        setDataList(dataListWithKey);
      }
    } catch (error) {
      console.error('Error loading data list:', error);
    } finally {
      setLoading(false);
    }
  };

  const editData = async (id: string, values: any) => {
    await requestDataEdit(id, values.name, values.description);
    loadDataList(searchKey);
  };

  const downloadData = async (
    id: string,
    item: any,
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const { data: downloadUrl } = await requestDownloadDataSource(id);
      const result = await downloadFile(downloadUrl, item.name);
      return result;
    } catch (error) {
      return { success: false, error: 'Failed to get download URL' };
    }
  };

  const downloadSelectedData = async () => {
    const downloadableItems = selectedRows.filter((item) => item.state === 'ok');
    const failedItems: string[] = [];
    let successCount = 0;

    for (const item of downloadableItems) {
      const result = await downloadData(item.id, item);
      if (result.success) {
        successCount++;
      } else {
        failedItems.push(item.name);
      }
    }

    if (failedItems.length === 0) {
      message.success(`Downloaded ${successCount} file(s)`);
    } else if (successCount === 0) {
      message.error(`Failed to download ${failedItems.length} file(s): ${failedItems.join(', ')}`);
    } else {
      message.warning(`Downloaded ${successCount} file(s). Failed: ${failedItems.join(', ')}`);
    }

    setSelectedRowKeys([]);
    setSelectedRows([]);
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[], rows: DataType[]) => {
      setSelectedRowKeys(keys);
      setSelectedRows(rows);
    },
    getCheckboxProps: (record: DataType) => ({
      disabled: record.state !== 'ok',
    }),
  };

  const handleMessageClick = (msg: string) => {
    setErrorMessage(msg);
    setErrorMsgShow(true);
  };

  const handleErrorMsgCancel = () => {
    setErrorMsgShow(false);
    setErrorMessage('');
  };

  const getFilteredData = (dataList: DataType[]) => {
    if (!isDataFilterEnabled) {
      return dataList;
    }
    return dataList.filter((item) => !(item.state === 'error' || item.state === 'uploading'));
  };

  const columns = [
    {
      title: dictionary.NAME,
      dataIndex: 'name',
      key: 'id',
      render: (text: string) => {
        return (
          <div
            style={{
              width: '10vw',
              // Hide overflow
              overflow: 'hidden',
              // Replace overflow with an ellipsis
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            <DatabaseOutlined
              style={{
                marginRight: '10px',
              }}
            />
            <span>{text || 'Unamed data'}</span>
          </div>
        );
      },
    },
    {
      title: dictionary.DESCRIPTION,
      dataIndex: 'description',
      key: 'id',

      render: (text: string) => {
        return (
          <div
            style={{
              width: '8vw',
            }}
            title={text}
          >
            {text && text.slice(0, 100)}
            {text && text.length > 100 ? '...' : ''}
          </div>
        );
      },
    },
    {
      title: dictionary.SPECIES,
      dataIndex: 'species',
      key: 'id',
      render: (text: string) => {
        return (
          <div
            style={{
              whiteSpace: 'nowrap',
            }}
          >
            {text}
          </div>
        );
      },
    },
    {
      title: dictionary.UPLOAD_TYPE,
      dataIndex: 'uploadType',
      key: 'id',
    },
    // {
    //   title: dictionary.COLLECTED,
    //   dataIndex: 'collected',
    //   key: 'id',
    //   render: (checked: boolean) => {
    //     return <Checkbox checked={checked} readOnly={true} />;
    //   },
    // },
    {
      title: dictionary.CREATED_FROM,
      dataIndex: 'createdFrom',
      key: 'id',
      render: (text: string) => {
        return <span>{text}</span>;
      },
    },
    {
      title: dictionary.FILE_SIZE || 'File Size',
      dataIndex: 'dataSize',
      key: 'id',
      render: (size: number) => {
        return <span>{formatFileSize(size)}</span>;
      },
      sorter: (a: DataType, b: DataType) => a.dataSize - b.dataSize,
      sortDirections: ['ascend', 'descend'],
    },
    {
      title: dictionary.CREATED_AT,
      dataIndex: 'createdTime',
      key: 'id',
      render: (time: number) => {
        const date = new Date(time);
        return <span>{date.toLocaleString()}</span>;
      },
      sorter: (a: DataType, b: DataType) => a.createdTime - b.createdTime,
      sortDirections: ['ascend', 'descend'],
    },
    {
      title: dictionary.ACTION,
      dataIndex: 'id',
      key: 'id',
      render: (id: string, item: DataType) => {
        return (
          <div>
            <Popover
              title={'Edit data information'}
              content={<EditForm item={item} onSubmit={editData} />}
            >
              <Button type="link" icon={<EditOutlined />} />
            </Popover>
            <Popover title={dictionary.DOWNLOAD_DATA}>
              <Button
                type="link"
                icon={<DownloadOutlined />}
                onClick={async () => {
                  const result = await downloadData(id, item);
                  if (!result.success) {
                    message.error(result.error || 'Download failed');
                  }
                }}
                disabled={item.state !== 'ok'}
              />
            </Popover>
            <Popconfirm
              placement="topLeft"
              title={'Are you sure to delete this data?'}
              description={'This action cannot be undone.'}
              onConfirm={() => deleteData(id)}
              okText="Yes"
              cancelText="No"
              // disabled={item.state !== 'ok'}
            >
              <Button type="link" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </div>
        );
      },
    },
    {
      title: dictionary.STATE,
      dataIndex: 'state',
      key: 'id',
      render: (text: string, record: any) => {
        return (
          <>
            {record.errorMessage ? (
              <span
                style={{ cursor: 'pointer' }}
                onClick={() => handleMessageClick(record.errorMessage)}
              >
                <WarningOutlined />
              </span>
            ) : null}{' '}
            {text}
          </>
        );
      },
    },
  ];

  const openUploadEntry = () => {
    openUploadDataUI();
  };

  const importMenu = (
    <Menu>
      <Menu.Item key="upload" onClick={openUploadEntry}>
        {dictionary.UPLOAD_FROM_DEVICE}
      </Menu.Item>
      <Menu.Item key="thirdParty" onClick={() => setThirdPartyDataSourceModalVisible(true)}>
        {dictionary.IMPORT_FROM_DATA_LAKE}
      </Menu.Item>
    </Menu>
  );

  const handleSearch = (value: string) => {
    setSearchKey(value);
  };

  useEffect(() => {
    loadDataList(searchKey);

    if (!isGuestUser) {
      intervalRef.current = setInterval(() => {
        loadDataList(searchKey);
      }, pollInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [searchKey, isGuestUser]);

  useEffect(() => {
    if (!showUploadDataUI) {
      loadDataList(searchKey);
    }
  }, [showUploadDataUI]);

  // Handle success of anndata upload
  useEffect(() => {
    if (isAnndataUploadSuccess) {
      loadDataList(searchKey);
    }
  }, [isAnndataUploadSuccess]);

  const navigateToAnalysis = () => {
    history.push(`/analysisPanel/flowPanel?analysis-id=${currentAnalysisId}`);
  };

  return (
    <div className={style.myDataBlock}>
      <div className={style.title}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className={style.titleText}>{dictionary.MY_DATA}</div>
          <Dropdown overlay={importMenu} trigger={['hover']}>
            <Button icon={<PlusOutlined />} type={'primary'}>
              {dictionary.IMPORT_DATA}
            </Button>
          </Dropdown>
          <Button onClick={() => setDataCaptureModalVisible(true)}>
            <CustomImage
              name={customIconNames.AIICONSTAR}
              style={{ height: '16px', marginRight: '8px', cursor: 'pointer' }}
            />
            <span className="gradient-text">{dictionary.DATA_CAPTURE}</span>
          </Button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Switch
              checkedChildren="Data filter"
              unCheckedChildren="Data filter"
              checked={isDataFilterEnabled}
              onChange={(checked) => setIsDataFilterEnabled(checked)}
              disabled={isGuestUser}
            />
            <Tooltip title="When data filter enabled, only shows data with state 'ok' or 'processing'. Disable to view all data.">
              <QuestionOutlined style={{ cursor: 'pointer', color: '#8c8c8c' }} />
            </Tooltip>
          </div>
          {selectedRowKeys.length > 0 && (
            <Button icon={<DownloadOutlined />} onClick={downloadSelectedData}>
              {dictionary.DOWNLOAD_DATA} ({selectedRowKeys.length})
            </Button>
          )}
          {currentAnalysisId && (
            <div>
              <Divider type="vertical" />
              <Button icon={<RollbackOutlined />} onClick={navigateToAnalysis}>
                {dictionary.BACK_TO_ANALYSIS}
              </Button>
            </div>
          )}
        </div>
        <div className={style.searchBar}>
          <Input.Search
            placeholder={dictionary.SEARCH}
            onSearch={handleSearch}
            onChange={(e) => {
              if (e.target.value === '') {
                setSearchKey('');
              }
            }}
            enterButton
          />
        </div>
      </div>
      <Table
        rowSelection={rowSelection}
        loading={loading}
        columns={columns}
        dataSource={getFilteredData(dataList)}
        rowClassName={(record) => {
          const className = record.id === highlightId ? style.highlightRow : '';
          return `${className} row-id-${record.id}`;
        }}
        rowKey="id"
        onRow={(record) => ({
          id: record.id,
        })}
        pagination={{
          current: currentPage,
          onChange: (page) => {
            if (!isSearchingHighlightedRow) {
              setCurrentPage(page);
            }
          },
          pageSize: 10,
          total: dataList.length,
        }}
      />
      <Modal
        centered
        title={dictionary.ERROR_MESSAGE}
        open={errorMsgShow}
        onCancel={handleErrorMsgCancel}
        footer={[
          <Button key="back" onClick={handleErrorMsgCancel}>
            {dictionary.CLOSE}
          </Button>,
        ]}
      >
        {errorMessage}
      </Modal>
    </div>
  );
};

export default MyDataBlock;
