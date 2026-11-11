import { FunctionBlockCreateStep } from '@/constants/functionBlock';
import { useState, useRef } from 'react';

const useFunctionBlockCreate = () => {
  const currentUploadIdRef = useRef<string>('');
  const [showUploadFbModal, setShowUploadFbModal] = useState(false);
  const [createStep, setCreateStep] = useState(FunctionBlockCreateStep.INPUT);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [file, setFile] = useState<any>([]);
  const [validateError, setValidateError] = useState({});
  const [createInfo, setCreateInfo] = useState<{
    name: string;
    type: string;
    groupName: string;
    groupId: string;
    versionName: string;
  }>({
    name: '',
    type: '',
    groupName: '',
    groupId: '',
    versionName: '',
  });

  const openUploadFbModal = () => {
    setShowUploadFbModal(true);
  };

  const closeUploadFbModal = () => {
    setShowUploadFbModal(false);
  };

  return {
    showUploadFbModal,
    openUploadFbModal,
    closeUploadFbModal,
    createStep,
    setCreateStep,
    isUploading,
    setIsUploading,
    uploadProgress,
    setUploadProgress,
    file,
    setFile,
    validateError,
    setValidateError,
    createInfo,
    setCreateInfo,
    currentUploadIdRef,
  };
};

export default useFunctionBlockCreate;
