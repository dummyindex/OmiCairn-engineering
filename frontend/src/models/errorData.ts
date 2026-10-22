import { requestDataInfo } from '@/request/data';
import { useState } from 'react';

const useErrorData = () => {
  const [showErrorDataUI, setShowErrorDataUI] = useState<boolean>(false);
  const [targetDataId, setTargetDataId] = useState<string | null>(null);
  const [targetDataInfo, setTargetDataInfo] = useState<any | null>(null);

  const loadDataInfo = async (dataId: string) => {
    const { data: dataInfo } = await requestDataInfo(dataId);
    setTargetDataInfo(dataInfo);
  };

  const openErrorDataUI = (dataId: string) => {
    setTargetDataId(dataId);
    loadDataInfo(dataId);
    setShowErrorDataUI(true);
  };

  const closeErrorDataUI = () => {
    setTargetDataId(null);
    setTargetDataInfo(null);
    setShowErrorDataUI(false);
  };

  return {
    openErrorDataUI,
    closeErrorDataUI,
    targetDataId,
    showErrorDataUI,
    targetDataInfo,
  };
};

export default useErrorData;
