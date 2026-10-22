import { useState } from 'react';

const useThirdPartyDataSource = () => {
  const [dataCaptureModalVisible, setDataCaptureModalVisible] = useState(false);
  const [isThirdPartyDataListModalVisible, setIsThirdPartyDataListModalVisible] = useState(false);
  const [currentAnalysisId, setCurrentAnalysisId] = useState<string | null>(null);

  return {
    dataCaptureModalVisible,
    setDataCaptureModalVisible,
    isThirdPartyDataListModalVisible,
    setIsThirdPartyDataListModalVisible,
    currentAnalysisId,
    setCurrentAnalysisId,
  };
};

export default useThirdPartyDataSource;
