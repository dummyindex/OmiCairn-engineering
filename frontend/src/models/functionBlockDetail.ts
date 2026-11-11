import { useEffect, useState } from 'react';
import { requestGetFBInformation, requestGetFBPreviewList } from '@/request/functionBlock';

type FunctionBlockDetail = {
  description: string | null;
  source: string | null;
  link: string | null;
  programLanguage: string | null;
  runtimeVersion: string | null;
  plotOnly: boolean | null;
  id: string | null;
  name: string | null;
  createdTime: string | null;
  previewImages?: string[];
  currentVersionName: string | null;
} | null;

const useFunctionBlockDetail = () => {
  const [functionBlockId, setFunctionBlockId] = useState(null as string | null);
  const [functionBlockDetail, setFunctionBlockDetail] = useState(null as FunctionBlockDetail);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null as string | null);

  const getFunctionBlockDetail = async () => {
    if (!functionBlockId) return;
    setLoading(true);
    try {
      const [{ data: fbInformation }, { data: fbPreviews }] = await Promise.all([
        requestGetFBInformation(functionBlockId),
        requestGetFBPreviewList({ functionBlockId, functionBlockVersionId: null }),
      ]);
      const {
        current_version_information: cvi,
        currentVersionInformation,
        id,
        name,
        createdTime,
      } = fbInformation;
      const information = cvi || currentVersionInformation || {};
      const {
        description,
        source,
        documentUrl,
        programLanguage,
        runtimeVersion,
        plotOnly,
        name: currentVersionName,
      } = information;
      setFunctionBlockDetail({
        description,
        source,
        link: documentUrl,
        programLanguage,
        runtimeVersion: runtimeVersion || 'none',
        plotOnly,
        id,
        name,
        createdTime: new Date(createdTime).toLocaleString(),
        previewImages: fbPreviews || [],
        currentVersionName,
      });
    } catch (error: any) {
      setError(error?.message || error || 'failed to get function block detail');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getFunctionBlockDetail();
  }, [functionBlockId]);

  const showModal = (functionBlockId: string) => {
    setFunctionBlockId(functionBlockId);
  };

  const closeModal = () => {
    setFunctionBlockId(null);
    setFunctionBlockDetail(null);
    setLoading(false);
    setError(null);
  };

  return {
    functionBlockId,
    functionBlockDetail,
    loading,
    error,
    showModal,
    closeModal,
  };
};

export default useFunctionBlockDetail;
