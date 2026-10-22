import { ComponentType, UploadType } from '@/constants/data';
import { useState } from 'react';

const useUploadDataUI = () => {
  const [showUploadDataUI, setShowUploadDataUI] = useState<boolean>(false);

  const [targetAnalysisId, setTargetAnalysisId] = useState<string | null>(null);

  //   anndata
  const [anndataUploadProgress, setAnndataUploadProgress] = useState<Record<string, number>>({});

  const [anndatashowPage, setAnndataShowPage] = useState(false);

  const [currentAnndataUploadIdRef, setCurrentAnndataUploadIdRef] = useState<
    Record<string, string>
  >({});
  const [isAnndataUploading, setIsAnndataUploading] = useState<Record<string, boolean>>({});
  const [isAnndataUploadSuccess, setIsAnndataUploadSuccess] = useState<Record<string, boolean>>({});

  const [fileList, setFileList] = useState<Record<string, File>>({});
  const [persistentDataSource, setPersistentDataSource] = useState<
    { key: string; filename: string; species: string; description: string; progress: number }[]
  >([]);
  const [persistentSelectedFiles, setPersistentSelectedFiles] = useState<
    {
      file: File;
      key: string;
    }[]
  >([]);

  //   assemble
  const [dataId, setDataId] = useState(null as null | string);

  const [assembleShowPage, setAssembleShowPage] = useState(false);
  const [componentUploadedStateDict, setComponentUploadedStateDict] = useState({
    [ComponentType.LAYER_UNSPLICED]: false,
    [ComponentType.LAYER_SPLICED]: false,
    [ComponentType.X]: false,
    [ComponentType.OBS]: false,
    [ComponentType.VAR]: false,
    [ComponentType.OBSM]: false,
    [ComponentType.OBSP]: false,
    [ComponentType.VARM]: false,
    [ComponentType.VARP]: false,
  } as any);

  // 10x out
  const [data10xId, setData10xId] = useState(null as null | string);
  const [uploaded10xFileList, setUploaded10xFileList] = useState([] as any);

  const [uploadType, setUploadType] = useState<string>(UploadType.ANNDATA);

  const openUploadDataUI = (analysisId?: string) => {
    if (analysisId !== undefined) {
      setTargetAnalysisId(analysisId);
    }
    setUploadType(UploadType.ANNDATA);
    setShowUploadDataUI(true);
  };

  const [seuratObjectRdsShowPage, setSeuratObjectRdsShowPage] = useState(false);
  const [isSeuratObjectRdsUploaded, setIsSeuratObjectRdsUploaded] = useState(false);

  const closeUploadDataUI = () => {
    setTargetAnalysisId(null);
    setShowUploadDataUI(false);
    setAnndataShowPage(false);
    setAssembleShowPage(false);
    setSeuratObjectRdsShowPage(false);
    setFileList({});
    setUploaded10xFileList([]);
    setDataId(null);
    setData10xId(null);
    setComponentUploadedStateDict({
      [ComponentType.LAYER_UNSPLICED]: false,
      [ComponentType.LAYER_SPLICED]: false,
      [ComponentType.X]: false,
      [ComponentType.OBS]: false,
      [ComponentType.VAR]: false,
      [ComponentType.OBSM]: false,
      [ComponentType.OBSP]: false,
      [ComponentType.VARM]: false,
      [ComponentType.VARP]: false,
    } as any);
  };

  return {
    openUploadDataUI,
    closeUploadDataUI,
    targetAnalysisId,
    showUploadDataUI,
    uploadType,
    setUploadType,

    // anndata
    anndataUploadProgress,
    setAnndataUploadProgress,
    anndatashowPage,
    setAnndataShowPage,
    currentAnndataUploadIdRef,
    setCurrentAnndataUploadIdRef,
    isAnndataUploading,
    setIsAnndataUploading,
    isAnndataUploadSuccess,
    setIsAnndataUploadSuccess,
    fileList,
    setFileList,
    persistentDataSource,
    setPersistentDataSource,
    persistentSelectedFiles,
    setPersistentSelectedFiles,

    // assemble
    assembleShowPage,
    setAssembleShowPage,
    componentUploadedStateDict,
    setComponentUploadedStateDict,
    dataId,
    setDataId,

    // 10x
    data10xId,
    setData10xId,
    uploaded10xFileList,
    setUploaded10xFileList,

    // seurat object rds
    seuratObjectRdsShowPage,
    setSeuratObjectRdsShowPage,
    isSeuratObjectRdsUploaded,
    setIsSeuratObjectRdsUploaded,
  };
};

export default useUploadDataUI;
