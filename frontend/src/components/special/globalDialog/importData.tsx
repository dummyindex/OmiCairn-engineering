import { Modal, Table, Input, Switch, Tooltip, Button, message } from 'antd';
import { useModel } from 'umi';
import {
  SearchOutlined,
  DatabaseOutlined,
  WarningOutlined,
  QuestionOutlined,
} from '@ant-design/icons';
import React from 'react';
import { useEffect } from 'react';
import { requestDataSourceList } from '@/request/data';
import { DataListFetchMode } from '@/constants/data';
import { AnalysisType } from '@/constants/analysis';
import { requestImportDatas } from '@/request/analysis';
import type { DataType } from '@/interfaces/data';

let delayTimer: NodeJS.Timeout;

const ImportDataDialog = () => {
  const { targetAnalysisId, showImportDataUI, closeImportDataUI, selectedIds, setSelectedIds } =
    useModel('importDataUI');
  const { analysisAccessType } = useModel('analysis');
  const { dictionary } = useModel('localization');

  const [searchKey, setSearchKey] = React.useState('' as string);

  const [dataList, setDataList] = React.useState<DataType[]>([]);

  const [importing, setImporting] = React.useState(false as boolean);

  const [errorMsgShow, setErrorMsgShow] = React.useState(false as boolean);

  const [errorMessage, setErrorMessage] = React.useState<string>('');

  const { isGuest } = useModel('user');
  const isGuestUser = isGuest();

  const [modalWidth, setModalWidth] = React.useState(window.innerWidth * 0.7);
  const [modalHeight, setModalHeight] = React.useState(window.innerHeight * 0.6);

  const [isDataFilterEnabled, setIsDataFilterEnabled] = React.useState(true);

  const maxModalWidth = window.innerWidth * 0.87;
  const maxModalHeight = window.innerHeight * 0.85;

  const handleResizeStart = (e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    const startX = e.clientX;
    const startY = e.clientY;
    const startWidth = modalWidth;
    const startHeight = modalHeight;

    const handleResize = (moveEvent: MouseEvent) => {
      const newWidth = Math.min(
        maxModalWidth,
        Math.max(800, startWidth + moveEvent.clientX - startX),
      );
      const newHeight = Math.min(
        maxModalHeight,
        Math.max(600, startHeight + moveEvent.clientY - startY),
      );
      setModalWidth(newWidth);
      setModalHeight(newHeight);
    };

    const handleResizeStop = () => {
      document.removeEventListener('mousemove', handleResize);
      document.removeEventListener('mouseup', handleResizeStop);
    };

    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', handleResizeStop);
  };

  const handleMessageClick = (msg: string) => {
    setErrorMessage(msg);
    setErrorMsgShow(true);
  };

  const columns = [
    {
      title: dictionary.NAME,
      dataIndex: 'name',
      key: 'id',
      ellipsis: {
        showTitle: false,
      },
      render: (text: string) => {
        return (
          <span>
            <DatabaseOutlined style={{ marginRight: '1rem' }} />
            <Tooltip placement="topLeft" title={text}>
              {text}
            </Tooltip>
          </span>
        );
      },
    },
    {
      title: dictionary.CREATED_FROM,
      dataIndex: 'createdFrom',
      key: 'id',
    },
    {
      title: dictionary.UPLOAD_TYPE,
      dataIndex: 'uploadType',
      key: 'id',
    },
    {
      title: dictionary.SPECIES,
      dataIndex: 'species',
      key: 'id',
    },
    {
      title: dictionary.DESCRIPTION,
      dataIndex: 'description',
      key: 'id',
      ellipsis: {
        showTitle: false,
      },
      render: (text: string) => {
        return (
          <div
            style={{
              width: '10vw',
            }}
          >
            <span>
              <Tooltip
                placement="topLeft"
                title={`${text && text.slice(0, 100)}${text && text.length > 100 ? '...' : ''}`}
              >
                {text && text.slice(0, 100)}
                {text && text.length > 100 ? '...' : ''}
              </Tooltip>
            </span>
          </div>
        );
      },
    },
    {
      title: dictionary.CREATED_AT,
      dataIndex: 'createdTime',
      key: 'id',
      render: (text: number) => {
        return <span>{new Date(text).toLocaleString()}</span>;
      },
    },
    {
      title: dictionary.STATE,
      dataIndex: 'state',
      key: 'id',
    },
    {
      title: dictionary.ERROR_MESSAGE,
      dataIndex: 'errorMessage',
      key: 'id',
      render: (text: string) => {
        return (
          <>
            {text ? (
              <span style={{ cursor: 'pointer' }} onClick={() => handleMessageClick(text)}>
                <WarningOutlined />
              </span>
            ) : (
              ''
            )}
          </>
        );
      },
    },
  ];

  const editSearchKey = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (delayTimer) {
      clearInterval(delayTimer);
    }
    delayTimer = setTimeout(() => {
      setSearchKey(e.target.value);
    }, 200);
  };

  const loadAllDataList = async () => {
    const { data: dataList } = await requestDataSourceList(DataListFetchMode.ALL, null, searchKey);
    setDataList(
      dataList.map((data: any) => {
        return {
          ...data,
          key: data.id,
        };
      }),
    );
  };

  const importData = async () => {
    if (targetAnalysisId === null) {
      throw Error('targetAnalysisId is null');
    }
    try {
      setImporting(true);
      await requestImportDatas(targetAnalysisId, selectedIds);
      message.success('Import data successfully');
    } catch (e) {
      message.error('Failed to import data');
    } finally {
      setImporting(false);
    }
  };

  const loadSelectedDataIdList = async () => {
    const { data: importedDataList } = await requestDataSourceList(
      DataListFetchMode.IMPORTED,
      targetAnalysisId,
    );
    setSelectedIds(
      importedDataList.map((data: any) => {
        return data.id;
      }),
    );
  };

  const handleErrorMsgCancel = () => {
    setErrorMsgShow(false);
    setErrorMessage('');
  };

  const getFilteredData = (dataList: DataType[]) => {
    if (!isDataFilterEnabled) {
      return dataList;
    }
    return dataList.filter((item) => item.state === 'ok' || item.state === 'processing');
  };

  useEffect(() => {
    loadAllDataList();
  }, [searchKey]);

  useEffect(() => {
    if (targetAnalysisId === null) {
      return;
    }
    loadSelectedDataIdList();
  }, [targetAnalysisId]);

  return (
    <Modal
      centered
      destroyOnClose
      open={showImportDataUI}
      onCancel={closeImportDataUI}
      cancelText="close"
      title={dictionary.IMPORT_FROM_EXISITING_DATA}
      okButtonProps={{ hidden: true }}
      cancelButtonProps={{ hidden: true }}
      width={modalWidth}
      bodyStyle={{ height: modalHeight - 60, overflowY: 'auto' }}
      style={{ resize: 'both', overflow: 'hidden', position: 'relative' }}
    >
      <div style={{ height: '100%' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '1rem',
          }}
        >
          <Input
            placeholder={dictionary.SEARCH}
            size="large"
            suffix={<SearchOutlined />}
            style={{ width: '70%' }}
            onChange={editSearchKey}
          />
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Switch
              checkedChildren="Data filter"
              unCheckedChildren="Data filter"
              checked={isDataFilterEnabled}
              onChange={(checked) => setIsDataFilterEnabled(checked)}
              disabled={isGuestUser}
            />
            <Tooltip title="When data filter enabled, only shows data with state 'ok' or 'processing'. Disable to view all data.">
              <QuestionOutlined
                style={{ cursor: 'pointer', color: '#8c8c8c', marginLeft: '0.5rem' }}
              />
            </Tooltip>
          </div>
        </div>
        <Table
          columns={columns}
          dataSource={getFilteredData(dataList)}
          rowSelection={{
            type: 'checkbox',
            onSelect: (record: DataType, selected: boolean) => {
              const { id } = record;
              const set = new Set(selectedIds);
              if (selected) {
                set.add(id);
              } else {
                set.delete(id);
              }
              setSelectedIds(Array.from(set));
            },
            onSelectAll: (selected: boolean, _: DataType[], changeRows: DataType[]) => {
              const set = new Set(selectedIds);
              if (selected) {
                changeRows.forEach((row: DataType) => {
                  set.add(row.id);
                });
              } else {
                changeRows.forEach((row: DataType) => {
                  set.delete(row.id);
                });
              }
              setSelectedIds(Array.from(set));
            },
            selectedRowKeys: selectedIds,
            getCheckboxProps: (item) => ({
              disabled: isGuestUser || item.state !== 'ok',
            }),
          }}
          scroll={{ y: 56 * 5 }}
        />
        <div
          style={{
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'flex-end',
            alignItems: 'center',
          }}
        >
          {/* <div
            style={{
              marginRight: '2rem',
            }}
          >
            {selectedIds.length} {dictionary.SELECTED}
          </div> */}
          <Button
            disabled={analysisAccessType === AnalysisType.PUBLIC}
            type="primary"
            size="middle"
            loading={importing}
            onClick={importData}
          >
            {dictionary.CONFIRM}
          </Button>
        </div>
        <div
          style={{
            position: 'absolute',
            width: '20px',
            height: '20px',
            right: 0,
            bottom: 0,
            cursor: 'se-resize',
            backgroundColor: 'transparent',
            zIndex: 1000,
            transform: 'translate(50%, 50%)',
          }}
          onMouseDown={handleResizeStart}
        />
      </div>
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
    </Modal>
  );
};

export default ImportDataDialog;
