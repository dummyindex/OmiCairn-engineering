import { requestGetNodeInformation } from '@/request/node';
import { useEffect, useState } from 'react';

type NodeDetail = {
  id: string | null;
  name: string | null;
  type: string | null;
  x: number | null;
  y: number | null;
  state: string | null;
  analysisId: string | null;
  functionBlockId: string | null;
  functionBlockVersionId: string | null;
  dataId: string | null;
  createdTime: string | null;
  locked: boolean | null;
  tag: string | null;
  systemEnv: string | null;
  annotated: boolean | null;
  avgDuration: number | null;
  reportUuid: string | null;
  reportModel: string | null;
} | null;

const useNodeDetail = () => {
  const [nodeId, setNodeId] = useState(null as string | null);
  const [nodeDetail, setNodeDetail] = useState(null as NodeDetail);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null as string | null);

  const getNodeDetail = async () => {
    if (!nodeId) return;
    setLoading(true);
    try {
      const { data: nodeInformation } = await requestGetNodeInformation(nodeId);
      const {
        id,
        name,
        type,
        x,
        y,
        state,
        analysisId,
        functionBlockId,
        functionBlockVersionId,
        dataId,
        createdTime,
        locked,
        tag,
        systemEnv,
        annotated,
        avgDuration,
        reportUuid,
        reportModel,
      } = nodeInformation;

      setNodeDetail({
        id,
        name,
        type,
        x,
        y,
        state,
        analysisId,
        functionBlockId,
        functionBlockVersionId,
        dataId,
        createdTime: createdTime ? new Date(createdTime).toLocaleString() : null,
        locked,
        tag,
        systemEnv,
        annotated,
        avgDuration,
        reportUuid,
        reportModel,
      });
    } catch (error: any) {
      setError(error?.message || error || 'failed to get node detail');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getNodeDetail();
  }, [nodeId]);

  const showModal = (nodeId: string) => {
    setNodeId(nodeId);
  };

  const closeModal = () => {
    setNodeId(null);
    setNodeDetail(null);
    setLoading(false);
    setError(null);
  };

  return {
    nodeId,
    nodeDetail,
    loading,
    error,
    showModal,
    closeModal,
  };
};

export default useNodeDetail;
