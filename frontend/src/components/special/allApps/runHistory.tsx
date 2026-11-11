import { ComputationStateColorMap } from '@/constants/computation';
import {
  requestComputationList,
  requestComputationOutputList,
  requestOutputFileDownloadInfo,
} from '@/request/computation';
import { useState, useEffect } from 'react';
import { Button, Divider, Image } from 'antd';
import { DoubleLeftOutlined, DoubleRightOutlined, DownloadOutlined } from '@ant-design/icons';
import { formatTimeTool } from '@/util/formatTimeTool';
import { formatFileSize } from '@/util/fileTool';
import { requestFigureList } from '@/request/figure';
import { requestGetFigureInfo } from '@/request/attachedData';
import { useModel } from 'umi';

const OutputList = ({ targetComputation, setTargetComputation }) => {
  const { dictionary } = useModel('localization');
  const [outputs, setOutputs] = useState<any[]>([]);
  const [figures, setFigures] = useState<any[]>([]);
  const [uuidToPresignedUrl, setUuidToPresignedUrl] = useState<any>({});

  const loadOutputs = async () => {
    if (!targetComputation) {
      setOutputs([]);
      return;
    }
    const [{ data: outputs }, { data: figures }] = await Promise.all([
      requestComputationOutputList(targetComputation.id),
      requestFigureList(targetComputation.id),
    ]);
    setOutputs(outputs.objects);
    setFigures(figures);
  };

  const handleDownload = async (output: any) => {
    const { object_key: objectKey } = output;
    const { data: url } = await requestOutputFileDownloadInfo(targetComputation.id, objectKey);
    window.open(url);
  };

  const fetchPresignedUrls = async () => {
    const uuids = figures.map((figure) => figure.figureUuid);
    const uuidToPresignedUrl = {};
    const urls = await Promise.all(uuids.map((uuid) => requestGetFigureInfo(uuid)));
    urls.forEach((url, index) => {
      uuidToPresignedUrl[uuids[index]] = url;
    });
    setUuidToPresignedUrl(uuidToPresignedUrl);
  };

  useEffect(() => {
    loadOutputs();
  }, [targetComputation]);

  useEffect(() => {
    fetchPresignedUrls();
  }, [figures]);

  return (
    <div
      style={{
        height: '70vh',
        overflowY: 'auto',
      }}
    >
      {/* Simple page header */}
      <div>
        <Button
          type="text"
          icon={<DoubleLeftOutlined />}
          onClick={() => setTargetComputation(null)}
        >
          {dictionary.BACK}
        </Button>
      </div>
      <Divider>{dictionary.OUTPUTS}</Divider>
      {outputs.map((output: any) => {
        const { file_name: fileName, size, mime_type: mimeType } = output;
        return (
          <div
            key={fileName}
            style={{
              padding: '1.5em 0',
              borderBottom: '1px solid #f0f0f0',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'row',
                justifyContent: 'flex-start',
                alignItems: 'center',
                gap: '1em',
              }}
            >
              <div
                style={{
                  letterSpacing: '0.05em',
                  width: '15%',
                }}
              >
                {fileName}
              </div>
              <div
                style={{
                  textTransform: 'capitalize',
                  color: ComputationStateColorMap[targetComputation.computationState],
                  width: '10%',
                }}
              >
                {mimeType}
              </div>
              <div
                style={{
                  width: '15%',
                }}
              >
                {formatFileSize(size)}
              </div>
              <div style={{ flex: 1 }} />
              <Button
                // size="small"
                type="text"
                icon={<DownloadOutlined />}
                onClick={() => {
                  handleDownload(output);
                }}
              />
            </div>
          </div>
        );
      })}
      <Divider>{dictionary.FIGURES}</Divider>
      {figures.map((figure: any) => {
        const presignedUrl = uuidToPresignedUrl[figure.figureUuid] || '#';
        return (
          <div
            key={figure.id}
            style={{
              padding: '1.5em 0',
              borderBottom: '1px solid #f0f0f0',
            }}
          >
            <div
              style={{
                fontSize: '1.05em',
                color: '#333',
                textAlign: 'center',
              }}
            >
              {figure.figureName}
            </div>
            <div
              style={{
                display: 'flex',
                flexDirection: 'row',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <Image
                src={presignedUrl}
                width="50%"
                style={{
                  display: 'block',
                  margin: '1em auto',
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

const RunHistory = ({ truckNode, displayedComputation, setDisplayedComputation }) => {
  const [runHistories, setRunHistories] = useState<any[]>([]);

  const loadHistories = async () => {
    if (!truckNode) {
      setRunHistories([]);
      return;
    }
    const { data: computationList } = await requestComputationList('node', truckNode.id);
    setRunHistories(computationList);
  };

  useEffect(() => {
    loadHistories();
  }, [truckNode]);

  if (!!displayedComputation) {
    return (
      <OutputList
        targetComputation={displayedComputation}
        setTargetComputation={setDisplayedComputation}
      />
    );
  }

  return (
    <div
      style={{
        height: '70vh',
        overflowY: 'auto',
      }}
    >
      {runHistories.map((history) => {
        const createdTime = formatTimeTool(history.createdTime);
        return (
          <div
            key={history.id}
            style={{
              padding: '1.5em 0',
              borderBottom: '1px solid #f0f0f0',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'row',
                justifyContent: 'flex-start',
                alignItems: 'center',
                gap: '1em',
              }}
            >
              <div
                style={{
                  letterSpacing: '0.05em',
                }}
              >
                {createdTime}
              </div>
              <div
                style={{
                  textTransform: 'capitalize',
                  color: ComputationStateColorMap[history.computationState],
                }}
              >
                {history.computationState}
              </div>
              <div style={{ flex: 1 }} />
              <Button
                // size="small"
                type="text"
                icon={<DoubleRightOutlined />}
                onClick={() => setDisplayedComputation(history)}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RunHistory;
