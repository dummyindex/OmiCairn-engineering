import { Card, Button, Badge, Spin, Image } from 'antd';
import { DownloadOutlined, FileOutlined } from '@ant-design/icons';
import { useEffect, useState } from 'react';
import { requestComputationOutputList, requestLatestComputation } from '@/request/computation';
import { requestGetFigureInfo, requestGetTagList } from '@/request/attachedData';
import { downloadFile } from '@/request/awsOperation';

const NodeRealTimeDetails = ({ currentNodeId, currentNodeInfo }) => {
  const [figureList, setFigureList] = useState<any[]>([]);
  const [outputs, setOutputs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const load = async () => {
    console.log('Loading figure list for node:', currentNodeId);
    setIsLoading(true);
    try {
      const { data: latestComputation } = await requestLatestComputation(currentNodeId);
      const { resultDataId } = latestComputation;
      const tagList = await requestGetTagList(resultDataId);
      const currentTag = tagList.find((tag: any) => +tag.node_id === +currentNodeId);

      if (!currentTag) {
        setFigureList([]);
        return;
      }

      const { charts } = currentTag;
      const staticFigureList = charts.filter((chart: any) => chart.exist_type === 'static-image');

      const [figureList, { data: outputs }] = await Promise.all([
        Promise.all(
          staticFigureList.map(async (figure: any) => {
            const [thumbnailUrl, originalUrl] = await Promise.all([
              requestGetFigureInfo(figure.chart_uuid, true),
              requestGetFigureInfo(figure.chart_uuid, false),
            ]);
            return {
              ...figure,
              url: originalUrl,
              thumbnailUrl,
            };
          }),
        ),
        requestComputationOutputList(latestComputation.id),
      ]);
      setFigureList(figureList);
      setOutputs(outputs.objects || []);
    } catch (error) {
      console.error('Error loading figure list:', error);
      setFigureList([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFigureDownload = async (figure: any) => {
    const content = await fetch(figure.url).then((res) => res.blob());
    const url = window.URL.createObjectURL(content);
    const link = document.createElement('a');
    link.href = url;
    link.download = figure.chart_name || 'figure.png';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  useEffect(() => {
    if (currentNodeId) {
      load();
    }
  }, [currentNodeId, currentNodeInfo]);

  if (!currentNodeId || !currentNodeInfo || currentNodeInfo?.type !== 'computation node') {
    return (
      <div style={{ padding: '16px', textAlign: 'center', color: '#999' }}>No Node Details</div>
    );
  }

  return (
    <Card
      title={
        <div>
          Node Outputs <Spin hidden={!isLoading} size="small" />
        </div>
      }
      size="small"
      style={{ marginTop: '16px' }}
    >
      {/* Row 1: Figure List */}
      <div style={{ marginBottom: '16px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '3px',
          }}
        >
          <span style={{ fontWeight: 'bold', fontSize: '14px' }}>Figures:</span>
          <Badge count={figureList.length} style={{ backgroundColor: '#52c41a' }} />
        </div>

        <div
          style={{
            display: 'flex',
            gap: '8px',
            overflowX: 'auto',
            padding: '3px 0',
          }}
        >
          {figureList?.length === 0 ? (
            <div style={{ padding: '16px', textAlign: 'center', color: '#999' }}>No Figures</div>
          ) : (
            figureList.map((figure, index) => (
              <div
                key={index}
                style={{
                  flex: '0 0 auto',
                  width: '120px',
                  height: '100px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '6px',
                  padding: '4px',
                  position: 'relative',
                  cursor: 'pointer',
                  overflow: 'hidden',
                }}
              >
                <Image
                  src={figure.thumbnailUrl}
                  alt={figure.chart_name || `Figure ${index + 1}`}
                  width="100%"
                  height="70px"
                  style={{ objectFit: 'cover', borderRadius: '4px' }}
                  preview={{ src: figure.url }}
                  placeholder={<Spin size="small" />}
                />
                <div
                  style={{
                    position: 'absolute',
                    bottom: '4px',
                    left: '4px',
                    right: '4px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: '4px',
                  }}
                >
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    type="text"
                    style={{
                      fontSize: '10px',
                      padding: '0 4px',
                      background: 'rgba(255,255,255,0.8)',
                      flex: 1,
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleFigureDownload(figure);
                    }}
                  />
                </div>
                <div
                  style={{
                    position: 'absolute',
                    top: '4px',
                    left: '4px',
                    right: '4px',
                    fontSize: '10px',
                    background: 'rgba(0,0,0,0.6)',
                    color: 'white',
                    padding: '2px 4px',
                    borderRadius: '3px',
                    textAlign: 'center',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {figure.chart_name || `Figure ${index + 1}`}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Row 2: Outputs List */}
      <div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '3px',
          }}
        >
          <span style={{ fontWeight: 'bold', fontSize: '14px' }}>Outputs:</span>
          <Badge count={outputs.length} style={{ backgroundColor: '#1890ff' }} />
        </div>

        <div
          style={{
            display: 'flex',
            gap: '8px',
            overflowX: 'auto',
            padding: '3px 0',
          }}
        >
          {outputs.length === 0 ? (
            <div style={{ padding: '16px', textAlign: 'center', color: '#999' }}>
              No Output Files
            </div>
          ) : (
            outputs.map((output, index) => (
              <div
                key={output.object_key}
                style={{
                  flex: '0 0 auto',
                  padding: '8px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '6px',
                  background: '#fafafa',
                  display: 'flex',
                  justifyContent: 'flex-start',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                  <FileOutlined style={{ marginRight: '6px', color: '#52c41a' }} />
                  <span style={{ fontSize: '12px', fontWeight: 'bold' }}>
                    {output.file_name || `Output ${index + 1}`}
                  </span>
                </div>
                <Button
                  size="small"
                  icon={<DownloadOutlined />}
                  type="text"
                  onClick={() => {
                    downloadFile(output.object_key);
                  }}
                />
              </div>
            ))
          )}
        </div>
      </div>
    </Card>
  );
};

export default NodeRealTimeDetails;
