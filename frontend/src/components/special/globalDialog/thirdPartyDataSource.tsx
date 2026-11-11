import { useState, useEffect, useRef } from 'react';
import { Modal, Table, Button, Tag, Input, message, Tooltip } from 'antd';
import { useModel } from 'umi';
import type { GetProp, TableProps } from 'antd';
import { DatabaseOutlined } from '@ant-design/icons';
import {
  requestAssembleDataComponent,
  requestCreateDataFrame,
  requestDataComponentUploadInfo,
  requestPageThirdPartyDataList,
  requestDataSourceList,
} from '@/request/data';
import { UploadFromType, UploadType, DataListFetchMode } from '@/constants/data';
import { uploadFileToAWS } from '@/request/awsOperation';
import { getLocationParams } from '@/util/getUrl';
import { requestImportDatas } from '@/request/analysis';
import { AnalysisType } from '@/constants/analysis';

type ThirdPartyDataSourceType = {
  id: string;
  name: string;
  assay: string;
  cellCount: number;
  cellType: string;
  cellTypeAncestors: string;
  collectionId: string;
  createdAt: number;
  datasetAssets: string;
  datasetDeployments: string;
  developmentStage: string;
  developmentStageAncestors: string;
  disease: string;
  donorId: string;
  explorerUrl: string;
  isPrimaryData: string;
  isValid: boolean;
  meanGenesPerCell: number;
  organism: string;
  primaryCellCount: number;
  processingStatus: string;
  published: boolean;
  publishedAt: number;
  revision: number;
  schemaVersion: string;
  selfReportedEthnicity: string;
  sex: string;
  suspensionType: string;
  tissue: string;
  tissueAncestors: string;
  tombstone: boolean;
  updatedAt: number;
  importStatus: string;
  dataFrameId: string;
};

type ColumnsType<T> = TableProps<T>['columns'];
type TablePaginationConfig = Exclude<GetProp<TableProps, 'pagination'>, boolean>;

interface TableParams {
  pagination?: TablePaginationConfig;
  sortField?: string;
  sortOrder?: string;
  filters?: Parameters<GetProp<TableProps, 'onChange'>>[1];
}

const ThirdPartyDataSource: React.FC = () => {
  const { isThirdPartyDataListModalVisible, setIsThirdPartyDataListModalVisible } =
    useModel('thirdPartyDataSource');
  const { dictionary } = useModel('localization');
  const { isGuest } = useModel('user');
  const { analysisAccessType } = useModel('analysis');
  const [searchKey, setSearchKey] = useState('');
  const [currentDataList, setCurrentDataList] = useState<ThirdPartyDataSourceType[]>([]);
  const [thirdPartyDataFetchingDict, setThirdPartyDataFetchingDict] = useState({});
  const [loadingData, setLoadingData] = useState(false);
  const [tableParams, setTableParams] = useState<TableParams>({
    pagination: {
      current: 1,
      pageSize: 10,
    },
  });
  const [isCellTypeModalVisible, setIsCellTypeModalVisible] = useState(false);
  const [selectedCellTypes, setSelectedCellTypes] = useState<any[]>([]);

  const searchDelayTimer = useRef<NodeJS.Timeout | null>(null);

  const isGuestUser = isGuest();
  const [modalWidth, setModalWidth] = useState(window.innerWidth * 0.7);
  const [modalHeight, setModalHeight] = useState(window.innerHeight * 0.75);

  const maxModalWidth = window.innerWidth * 0.88;
  const maxModalHeight = window.innerHeight * 0.9;

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

  const fetchData = () => {
    setLoadingData(true);
    if (!!searchDelayTimer.current) {
      clearTimeout(searchDelayTimer.current);
    }
    searchDelayTimer.current = setTimeout(async () => {
      const { data: result } = await requestPageThirdPartyDataList(
        tableParams.pagination?.current || 1,
        tableParams.pagination?.pageSize || 10,
        searchKey,
      );
      const { list, total_count: totalCount } = result;
      const [analysisId] = getLocationParams(['analysis-id']);
      if (isGuestUser) {
        const updatedList = list.map((item: ThirdPartyDataSourceType) => ({
          ...item,
          importStatus: 'import',
          dataFrameId: null,
        }));
        setCurrentDataList(updatedList);
      } else {
        if (analysisId) {
          const { data: importedDataSourceList } = await requestDataSourceList(
            DataListFetchMode.IMPORTED,
            analysisId,
            null,
          );
          // Temporarily match by name
          const importedNames = importedDataSourceList.map((item: any) => item.name);
          const updatedList = list.map((item: ThirdPartyDataSourceType) => ({
            ...item,
            importStatus: importedNames.includes(item.name) ? 'imported' : 'import',
            dataFrameId: importedDataSourceList.find(
              (dataSource: any) => dataSource.name === item.name,
            )?.id,
          }));
          setCurrentDataList(updatedList);
        } else {
          const { data: dataList } = await requestDataSourceList(
            DataListFetchMode.ALL,
            null,
            searchKey,
          );
          const importedNames = dataList.map((item: any) => item.name);
          const updatedList = list.map((item: ThirdPartyDataSourceType) => ({
            ...item,
            importStatus: importedNames.includes(item.name) ? 'imported' : 'import',
            dataFrameId: dataList.find((dataSource: any) => dataSource.name === item.name)?.id,
          }));
          setCurrentDataList(updatedList);
        }
      }
      setThirdPartyDataFetchingDict({});
      setTableParams({
        ...tableParams,
        pagination: {
          ...tableParams.pagination,
          total: totalCount,
        },
      });
      setLoadingData(false);
    }, 200);
  };

  useEffect(() => {
    fetchData();
  }, [tableParams.pagination?.current, tableParams.pagination?.pageSize, searchKey]);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const checkImportingRecords = async () => {
      const hasImportingRecords = currentDataList.some(
        (record) => record.importStatus === 'importing',
      );

      if (hasImportingRecords) {
        const [analysisId] = getLocationParams(['analysis-id']);

        try {
          if (analysisId) {
            const { data: importedDataSourceList } = await requestDataSourceList(
              DataListFetchMode.IMPORTED,
              analysisId,
              null,
            );

            const importedNames = importedDataSourceList.map((item: any) => item.name);

            setCurrentDataList((prevList) =>
              prevList.map((item) => ({
                ...item,
                importStatus: importedNames.includes(item.name)
                  ? 'imported'
                  : item.importStatus === 'importing'
                  ? 'importing'
                  : 'import',
                dataFrameId: importedDataSourceList.find(
                  (dataSource: any) => dataSource.name === item.name,
                )?.id,
              })),
            );
          } else {
            const { data: dataList } = await requestDataSourceList(
              DataListFetchMode.ALL,
              null,
              searchKey,
            );

            const importedNames = dataList.map((item: any) => item.name);

            setCurrentDataList((prevList) =>
              prevList.map((item) => ({
                ...item,
                importStatus: importedNames.includes(item.name)
                  ? 'imported'
                  : item.importStatus === 'importing'
                  ? 'importing'
                  : 'import',
                dataFrameId: dataList.find((dataSource: any) => dataSource.name === item.name)?.id,
              })),
            );
          }
        } catch (error) {
          console.error('Error checking import status:', error);
        }
      }
    };

    if (isThirdPartyDataListModalVisible) {
      intervalId = setInterval(checkImportingRecords, 5000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isThirdPartyDataListModalVisible, currentDataList, searchKey]);

  const handleTableChange: TableProps['onChange'] = (pagination, filters, sorter) => {
    setTableParams({
      pagination,
      filters,
      ...sorter,
    });

    // `dataSource` is useless since `pageSize` changed
    if (pagination.pageSize !== tableParams.pagination?.pageSize) {
      setCurrentDataList([]);
    }
  };

  const onClose = () => {
    setIsThirdPartyDataListModalVisible(false);
  };

  const getThirdPartyDataSource = async (
    thirdPartyDataRecord: ThirdPartyDataSourceType,
    analysisId?: string | null,
    uploadType: string = UploadType.THIRD_PARTY_DATA,
  ) => {
    const { id } = thirdPartyDataRecord;
    setThirdPartyDataFetchingDict(() => {
      return {
        ...thirdPartyDataFetchingDict,
        [id]: true,
      };
    });
    const updatedList = currentDataList.map((item: ThirdPartyDataSourceType) => ({
      ...item,
      importStatus: item.id === id ? 'importing' : item.importStatus,
    }));
    setCurrentDataList(updatedList);
    try {
      const description = JSON.stringify(thirdPartyDataRecord);
      const { data: createDataFrameResult } = await requestCreateDataFrame(
        UploadFromType.THIRD_PARTY_DATA,
        thirdPartyDataRecord.name,
        UploadType.THIRD_PARTY_DATA,
        'Unknown',
        description,
      );
      const { id: dataFrameId } = createDataFrameResult;

      const { data: uploadInfo } = await requestDataComponentUploadInfo(
        dataFrameId as string,
        'ident.txt',
        '',
        UploadType.THIRD_PARTY_DATA,
        id.length,
      );
      const info = {
        third_party_data_id: id,
        upload_type: uploadType,
      };
      const infoStr = JSON.stringify(info);
      const file = new File([new Blob([infoStr])], 'ident.txt');
      await uploadFileToAWS(file, uploadInfo.presigned_url, new AbortController());
      await requestAssembleDataComponent(dataFrameId);
      if (!!analysisId) {
        await requestImportDatas(analysisId, [dataFrameId]);
      }
      message.success('The target data was successfully obtained, please wait for prehandling...');
    } catch (e) {
      message.error('Failed to get data source.');
      console.error(e);
    } finally {
      setThirdPartyDataFetchingDict(() => {
        return {
          ...thirdPartyDataFetchingDict,
          [id]: false,
        };
      });
    }
  };

  const columns: ColumnsType<ThirdPartyDataSourceType> = [
    {
      title: dictionary.NAME,
      dataIndex: 'name',
      key: 'id',
      ellipsis: {
        showTitle: false,
      },
      render: (text: string, item: ThirdPartyDataSourceType) => {
        return (
          <div
            key={item.id}
            title={text}
            style={{
              width: '13vw',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            <DatabaseOutlined
              style={{
                marginRight: '15px',
              }}
            />
            <Tooltip placement="topLeft" title={text}>
              <span>{text}</span>
            </Tooltip>
          </div>
        );
      },
    },
    {
      title: dictionary.CELL_COUNT,
      dataIndex: 'cellCount',
      key: 'id',
    },
    {
      title: dictionary.CELL_TYPE,
      dataIndex: 'cellType',
      key: 'id',
      ellipsis: {
        showTitle: false,
      },
      render: (cellType: any) => {
        const firstRow = cellType.slice(0, 2);
        const secondRow = cellType.slice(2, 4);
        const thirdRow = cellType.slice(4, 6);
        const hasMore = cellType.length > 6;

        return (
          <div
            style={{
              width: '11vw',
              overflowX: 'auto',
              gap: '4px',
            }}
          >
            {/* First row of tags */}
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'nowrap' }}>
              {firstRow.map(({ label }: any) => (
                <Tag
                  key={label}
                  color="blue"
                  title={label}
                  style={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    width: '3vw',
                  }}
                >
                  {label}
                </Tag>
              ))}
            </div>

            {/* Second row of tags */}
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'nowrap' }}>
              {secondRow.map(({ label }: any) => (
                <Tag
                  key={label}
                  color="blue"
                  title={label}
                  style={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    width: '3vw',
                  }}
                >
                  {label}
                </Tag>
              ))}
            </div>

            {/* Third row of tags */}
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'nowrap' }}>
              {thirdRow.map(({ label }: any) => (
                <Tag
                  key={label}
                  color="blue"
                  title={label}
                  style={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    width: '3vw',
                  }}
                >
                  {label}
                </Tag>
              ))}
            </div>

            {hasMore && (
              <Tag
                color="#bbb"
                style={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  cursor: 'pointer',
                }}
                onClick={() => {
                  setSelectedCellTypes(cellType);
                  setIsCellTypeModalVisible(true);
                }}
              >
                ...
              </Tag>
            )}
          </div>
        );
      },
    },
    {
      title: 'Disease',
      dataIndex: 'disease',
      key: 'id',
      ellipsis: {
        showTitle: false,
      },
      render: (disease: any) => {
        return (
          <div
            style={{
              width: '6vw',
            }}
          >
            {(disease || []).map(({ label }: any) => {
              return (
                <Tag
                  key={label}
                  color="blue"
                  title={label}
                  style={{
                    textCollapse: 'ellipsis',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    width: '5vw',
                  }}
                >
                  {label}
                </Tag>
              );
            })}
          </div>
        );
      },
    },
    {
      title: dictionary.IS_PRIMARY_DATA,
      dataIndex: 'isPrimaryData',
      key: 'id',
    },
    {
      title: dictionary.ORGANISM,
      dataIndex: 'organism',
      key: 'id',
      ellipsis: {
        showTitle: false,
      },
      render: (organism: any) => {
        return (
          <div
            style={{
              width: '6vw',
            }}
          >
            {(organism || []).map(({ label }: any) => {
              return (
                <Tag
                  key={label}
                  color="blue"
                  title={label}
                  style={{
                    textCollapse: 'ellipsis',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    width: '5vw',
                  }}
                >
                  {label}
                </Tag>
              );
            })}
          </div>
        );
      },
    },
    {
      title: dictionary.PRIMARY_CELL_COUNT,
      dataIndex: 'primaryCellCount',
      key: 'id',
    },
    {
      title: dictionary.ACTION,
      key: 'action',
      render: (_: any, record: ThirdPartyDataSourceType) => {
        const { importStatus: status } = record;
        return (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'stretch',
              gap: '10px',
              paddingRight: '30%',
            }}
          >
            <Button
              type="primary"
              style={{ marginLeft: '-10%', minWidth: '150px' }}
              loading={status === 'importing'}
              size="small"
              disabled={
                isGuestUser || (status === 'import' && analysisAccessType === AnalysisType.PUBLIC)
              }
              onClick={() => {
                const [analysisId] = getLocationParams(['analysis-id']);
                if (status === 'imported') {
                  // setCurrentAnalysisId(analysisId);
                  // history.push(`/management/data?highlightId=${record.dataFrameId}`);
                  // onClose();
                  message.info(
                    'View function is currently under construction. Please check back later.',
                  );
                  return;
                }
                if (!analysisId) {
                  getThirdPartyDataSource(record, null, UploadType.THIRD_PARTY_DATA);
                  return;
                }
                Modal.confirm({
                  title: 'Import into the current analysis',
                  content:
                    'Are you sure you want to import this data source into the current analysis?',
                  onOk: () => {
                    getThirdPartyDataSource(record, analysisId, UploadType.THIRD_PARTY_DATA);
                  },
                  onCancel: () => {
                    message.info('Import canceled.');
                  },
                });
              }}
            >
              {status === 'imported'
                ? dictionary.VIEW
                : status === 'import'
                ? dictionary.IMPORT
                : dictionary.IMPORTING}{' '}
              as anndata
            </Button>
            <Button
              type="primary"
              ghost
              style={{ marginLeft: '-10%', minWidth: '150px' }}
              loading={status === 'importing'}
              size="small"
              disabled={
                isGuestUser || (status === 'import' && analysisAccessType === AnalysisType.PUBLIC)
              }
              onClick={() => {
                const [analysisId] = getLocationParams(['analysis-id']);
                if (status === 'imported') {
                  // setCurrentAnalysisId(analysisId);
                  // history.push(`/management/data?highlightId=${record.dataFrameId}`);
                  // onClose();
                  message.info(
                    'View function is currently under construction. Please check back later.',
                  );
                  return;
                }
                if (!analysisId) {
                  getThirdPartyDataSource(record, null, UploadType.GENERAL);
                  return;
                }
                Modal.confirm({
                  title: 'Import into the current analysis',
                  content:
                    'Are you sure you want to import this data source into the current analysis?',
                  onOk: () => {
                    getThirdPartyDataSource(record, analysisId, UploadType.GENERAL);
                  },
                  onCancel: () => {
                    message.info('Import canceled.');
                  },
                });
              }}
            >
              {status === 'imported'
                ? dictionary.VIEW
                : status === 'import'
                ? dictionary.IMPORT
                : dictionary.IMPORTING}{' '}
              as general
            </Button>
          </div>
        );
      },
    },
  ];

  return (
    <div>
      <Modal
        centered
        width={modalWidth}
        open={isThirdPartyDataListModalVisible}
        onCancel={onClose}
        title={dictionary.IMPORT_FROM_DATA_LAKE}
        okButtonProps={{ style: { display: 'none' } }}
        cancelText={dictionary.CLOSE}
        style={{
          resize: 'both',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <div
          style={{
            height: '100%',
          }}
        >
          <Input
            placeholder="Filter by name"
            value={searchKey}
            onChange={(e: any) => setSearchKey(e.target.value)}
            style={{
              marginBottom: '20px',
            }}
          />
          <Table
            columns={columns}
            rowKey={(record: ThirdPartyDataSourceType) => record.id}
            dataSource={currentDataList}
            pagination={tableParams.pagination}
            loading={loadingData}
            onChange={handleTableChange}
            scroll={{ y: 60 * 5 }}
          />
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
      </Modal>
      <Modal
        centered
        open={isCellTypeModalVisible}
        onCancel={() => setIsCellTypeModalVisible(false)}
        title={dictionary.CELL_TYPE}
        footer={null}
        width={600}
      >
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            padding: '16px',
            maxHeight: '400px',
            overflowY: 'auto',
          }}
        >
          {selectedCellTypes.map(({ label }) => (
            <Tag
              key={label}
              color="blue"
              style={{
                padding: '4px 12px',
                margin: '4px',
              }}
            >
              {label}
            </Tag>
          ))}
        </div>
      </Modal>
    </div>
  );
};

export default ThirdPartyDataSource;
