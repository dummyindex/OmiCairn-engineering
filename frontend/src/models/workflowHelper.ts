import { DataListFetchMode } from '@/constants/data';
import { requestDataSourceList } from '@/request/data';
import { useState, useEffect } from 'react';
import { message } from 'antd';
import { requestRecommendPipeline, requestSimilarPT } from '@/request/gptPipeline';

const useWorkflowHelper = () => {
  const [analysisId, setAnalysisId] = useState<string | number | null>(null);

  const [selectedDataId, setSelectedDataId] = useState<string | number | null>(null);

  const [dataOptions, setDataOptions] = useState<any[]>([]);

  const [selectedDataInfo, setSelectedDataInfo] = useState<any | null>(null);

  const [requests, setRequests] = useState<string | null>('');

  const [requestsTemplateModelOpen, setRequestsTemplateModelOpen] = useState<boolean>(false);

  const [isFindingSimilar, setIsFindingSimilar] = useState<boolean>(false);

  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  const [isImporting, setIsImporting] = useState<boolean>(false);

  const [isRefreshingOptimization, setIsRefreshingOptimization] = useState<boolean>(false);

  const [showIntroduction, setShowIntroduction] = useState<boolean>(false);

  const [similarTemplate, setSimilarTemplate] = useState<any>();

  const [generatedTemplate, setGeneratedTemplate] = useState<any>();

  const [showSimilarTemplate, setShowSimilarTemplate] = useState<boolean>(false);

  const [showGeneratedTemplate, setShowGeneratedTemplate] = useState<boolean>(false);

  const openModal = (analysisId: string | number) => {
    if (!analysisId) return;
    setAnalysisId(analysisId);
  };

  const closeModal = () => {
    setAnalysisId(null);
    setSelectedDataId(null);
    setSelectedDataInfo(null);
    setRequests(null);
    setGeneratedTemplate(null);
    setSimilarTemplate(null);
  };

  const loadDataOptions = async () => {
    if (!analysisId) return;
    const [{ data: publicDataList }, { data: importedDataList }] = await Promise.all([
      requestDataSourceList(DataListFetchMode.PUBLIC),
      requestDataSourceList(DataListFetchMode.IMPORTED, analysisId + ''),
    ]);
    const newDataOptions = []
      .concat(
        publicDataList.map((item: any) => ({
          label: item.name,
          key: item.id,
          value: item.id,
          type: 'public',
        })),
      )
      .concat(
        importedDataList.map((item: any) => ({
          label: item.name,
          value: item.id,
          key: item.id,
          type: 'imported',
        })),
      );
    setDataOptions(newDataOptions);
  };

  const fetchSimilarPT = async () => {
    if (!requests) {
      message.error('Please input your request');
      return;
    }
    setSimilarTemplate(null);
    setIsFindingSimilar(true);
    try {
      const { data: result } = await requestSimilarPT(requests);
      setSimilarTemplate(result);
    } catch (e) {
      message.error('Failed to find similar template');
    } finally {
      setIsFindingSimilar(false);
      setShowSimilarTemplate(true);
    }
  };

  const fetchGeneratedPT = async () => {
    if (!requests) {
      message.error('Please input your request');
      return;
    }
    setGeneratedTemplate(null);
    setIsGenerating(true);
    try {
      const result = await requestRecommendPipeline(requests);
      setGeneratedTemplate(result);
    } catch (e) {
      message.error('Failed to generate template');
    } finally {
      setIsGenerating(false);
      setShowGeneratedTemplate(true);
    }
  };

  useEffect(() => {
    loadDataOptions();
  }, [analysisId]);

  return {
    open: !!analysisId,
    openModal,
    closeModal,

    dataOptions,
    selectedDataId,
    setSelectedDataId,
    selectedDataInfo,
    setSelectedDataInfo,

    requests,
    setRequests,

    requestsTemplateModelOpen,
    setRequestsTemplateModelOpen,

    isRefreshingOptimization,
    setIsRefreshingOptimization,

    setIsFindingSimilar,
    isFindingSimilar,

    setIsGenerating,
    isGenerating,

    showIntroduction,
    setShowIntroduction,

    isImporting,
    setIsImporting,

    fetchSimilarPT,
    fetchGeneratedPT,

    similarTemplate,
    showSimilarTemplate,
    setShowSimilarTemplate,

    generatedTemplate,
    showGeneratedTemplate,
    setShowGeneratedTemplate,
  };
};

export default useWorkflowHelper;
