import { FunctionBlockUpdateStep } from '@/constants/functionBlock';
import { useState, useRef } from 'react';

const useFunctionBlockUpdate = () => {
  const currentUploadIdRef = useRef<null | string>(null);
  const [updatedFBId, setUpdatedFBId] = useState<null | number | string>(null);
  const [updatedStep, setUpdatedStep] = useState(FunctionBlockUpdateStep.INPUT);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [fileList, setFileList] = useState<any[]>([]);
  const [validateError, setValidateError] = useState({});
  const [updateInfo, setUpdateInfo] = useState<{
    functionBlockId: string;
    versionName: string;
  }>({ functionBlockId: '', versionName: '' });

  return {
    currentUploadIdRef,
    updatedFBId,
    setUpdatedFBId,
    updatedStep,
    setUpdatedStep,
    isUploading,
    setIsUploading,
    uploadProgress,
    setUploadProgress,
    fileList,
    setFileList,
    validateError,
    setValidateError,
    updateInfo,
    setUpdateInfo,
  };
};

export default useFunctionBlockUpdate;
