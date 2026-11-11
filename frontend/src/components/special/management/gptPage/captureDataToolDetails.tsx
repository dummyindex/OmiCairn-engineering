import { UploadFromType, UploadType } from '@/constants/data';
import { requestImportDatas } from '@/request/analysis';
import { uploadFileToAWS } from '@/request/awsOperation';
import { requestV3UpdateChat, requestV3UpdateChatSubTask } from '@/request/chat';
import {
  requestAssembleDataComponent,
  requestCreateDataFrame,
  requestDataComponentUploadInfo,
  requestDataInfo,
} from '@/request/data';
import { Button, Card } from 'antd';
import { useEffect, useState } from 'react';

interface DatasetItem {
  id: string;
  name: string;
  data_description: string;
  conformity_degree: number;
  reason: string;
}

interface ImportedRecord {
  data_id: string;
  status: 'importing' | 'imported' | 'error';
  error?: string;
}

const DataItem = ({
  data,
  importDataset,
  importStatus,
}: {
  data: DatasetItem;
  importDataset: (data: DatasetItem, uploadType: string) => void;
  importing: boolean;
  importStatus?: 'importing' | 'imported' | 'error';
}) => {
  const [tempLoading, setTempLoading] = useState<boolean>(false);

  const getButtonProps = () => {
    if (tempLoading) {
      return {
        type: 'primary' as const,
        loading: true,
        children: 'Importing...',
        disabled: true,
      };
    }
    switch (importStatus) {
      case 'importing':
        return {
          type: 'primary' as const,
          loading: true,
          children: 'Importing...',
          disabled: true,
        };
      case 'imported':
        return {
          type: 'default' as const,
          style: { backgroundColor: '#52c41a', borderColor: '#52c41a', color: 'white' },
          children: 'Imported',
          disabled: true,
        };
      case 'error':
        return {
          type: 'default' as const,
          style: { backgroundColor: '#ff4d4f', borderColor: '#ff4d4f', color: 'white' },
          children: 'Error - Retry',
          disabled: false,
        };
      default:
        return {
          type: 'primary' as const,
          children: 'Import',
          disabled: false,
        };
    }
  };

  const buttonProps = getButtonProps();

  return (
    <Card key={data.id} size="small" style={{ marginBottom: '8px', border: '1px solid #e8e8e8' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 'bold', marginBottom: '4px', fontSize: '13px' }}>
            {data.name}
          </div>
          <div
            style={{
              fontSize: '11px',
              color: '#666',
              marginBottom: '4px',
              lineHeight: '1.4',
            }}
          >
            {data.data_description}
          </div>
          <div style={{ fontSize: '11px', color: '#999' }}>
            Relevance: {Math.floor(data.conformity_degree / 10)}% | {data.reason}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <Button
            size="small"
            onClick={() => {
              importDataset(data, UploadType.GENERAL);
              setTempLoading(true);
              setTimeout(() => setTempLoading(false), 4000);
            }}
            {...buttonProps}
          >
            import as General
          </Button>
          <Button
            size="small"
            ghost
            onClick={() => {
              importDataset(data, UploadType.THIRD_PARTY_DATA);
              setTempLoading(true);
              setTimeout(() => setTempLoading(false), 4000);
            }}
            {...buttonProps}
          >
            import as Anndata
          </Button>
        </div>
      </div>
    </Card>
  );
};

const DataCaptureToolDetails = ({ subTask, analysisId }: any) => {
  const [dataList, setDataList] = useState<DatasetItem[]>([]);
  const [importedRecordDict, setImportedRecordDict] = useState<Record<string, ImportedRecord>>({});
  const [pollingDatasets, setPollingDatasets] = useState<Set<string>>(new Set());

  const startPolling = (datasetId: string, dataFrameId: string) => {
    // If this dataset is already being polled, do not start polling again
    if (pollingDatasets.has(datasetId)) {
      return;
    }

    // Mark polling as started
    setPollingDatasets((prev) => new Set(prev).add(datasetId));

    const interval = setInterval(async () => {
      try {
        const { data: newDataInfo } = await requestDataInfo(dataFrameId);
        if (newDataInfo.state === 'ok') {
          if (!!analysisId) {
            await requestImportDatas(analysisId, [dataFrameId]);
          }
          await requestV3UpdateChatSubTask(subTask.id, {
            outputs: JSON.stringify({
              ...JSON.parse(subTask.outputs || '{}'),
              imported_dict: {
                ...JSON.parse(subTask.outputs || '{}')?.imported_dict,
                [datasetId]: {
                  data_id: dataFrameId,
                  status: 'imported',
                },
              },
            }),
          });
          await requestV3UpdateChat(subTask.chatId, {});
          clearInterval(interval);
          // Remove the polling marker
          setPollingDatasets((prev) => {
            const newSet = new Set(prev);
            newSet.delete(datasetId);
            return newSet;
          });
        } else if (newDataInfo.state === 'error') {
          await requestV3UpdateChatSubTask(subTask.id, {
            outputs: JSON.stringify({
              ...JSON.parse(subTask.outputs || '{}'),
              imported_dict: {
                ...JSON.parse(subTask.outputs || '{}')?.imported_dict,
                [datasetId]: {
                  data_id: dataFrameId,
                  status: 'error',
                  error: newDataInfo.error_message,
                },
              },
            }),
          });
          await requestV3UpdateChat(subTask.chatId, {});
          clearInterval(interval);
          // Remove the polling marker
          setPollingDatasets((prev) => {
            const newSet = new Set(prev);
            newSet.delete(datasetId);
            return newSet;
          });
        }
      } catch (error) {
        console.error('Error while polling data info:', error);
        clearInterval(interval);
        // Remove the polling marker
        setPollingDatasets((prev) => {
          const newSet = new Set(prev);
          newSet.delete(datasetId);
          return newSet;
        });
      }
    }, 5000); // Poll every 5 seconds
  };

  const importDataset = async (thirdPartyDataRecord: DatasetItem, uploadType: string) => {
    const { id } = thirdPartyDataRecord;
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
      await requestV3UpdateChatSubTask(subTask.id, {
        outputs: JSON.stringify({
          ...JSON.parse(subTask.outputs || '{}'),
          imported_dict: {
            ...JSON.parse(subTask.outputs || '{}')?.imported_dict,
            [id]: {
              data_id: dataFrameId,
              status: 'importing',
            },
          },
        }),
      });
      await requestV3UpdateChat(subTask.chatId, {});

      // Start polling to monitor the data processing status
      startPolling(id, dataFrameId);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    let dataList = [];
    let importedRecordDict = {};
    try {
      const subTaskDetails = JSON.parse(subTask.outputs || '{}');
      console.log('DataCaptureToolDetails subTaskDetails:', subTaskDetails);
      dataList = subTaskDetails?.['data']?.['selected_data_list'] || [];
      importedRecordDict = subTaskDetails?.['imported_dict'] || {};
    } catch (error) {
      dataList = [];
      importedRecordDict = {};
    }
    setDataList(dataList);
    setImportedRecordDict(importedRecordDict);

    // Check whether any data is being imported; if so, start polling
    Object.entries(importedRecordDict).forEach(([datasetId, record]: [string, any]) => {
      if (record.status === 'importing' && record.data_id && !pollingDatasets.has(datasetId)) {
        startPolling(datasetId, record.data_id);
      }
    });
  }, [subTask]);

  return (
    <div style={{ height: '100%', overflow: 'auto' }} id={subTask?.id}>
      <Card title="Data Capture" size="small" style={{ marginBottom: '16px' }}>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
            Captured Datasets:
          </label>
          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {dataList.map((item) => {
              const importRecord = importedRecordDict[item.id];
              const importing = importRecord?.status === 'importing';
              const importStatus = importRecord?.status;
              return (
                <DataItem
                  key={item.id}
                  data={item}
                  importDataset={importDataset}
                  importing={importing}
                  importStatus={importStatus}
                />
              );
            })}
            {(!dataList || dataList.length === 0) && (
              <div style={{ padding: '12px', textAlign: 'center', color: '#999' }}>
                No datasets captured
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default DataCaptureToolDetails;
