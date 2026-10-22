import { useState, useEffect } from 'react';
import { message } from 'antd';
import {
  requestGetFBVersionList,
  requestGetFBInformation,
  requestSwitchFunctionBlockVersion,
} from '@/request/functionBlock';

const useFunctionBlockVersionSwitch = () => {
  const [switchedFunctionBlockId, setSwitchedFunctionBlockId] = useState<null | string | number>(
    null,
  );
  const [versionList, setVersionList] = useState<any[]>([]);
  const [currentVersionId, setCurrentVersionId] = useState<null | string | number>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<null | string | Object>(null);

  const clean = () => {
    setVersionList([]);
    setCurrentVersionId(null);
    setLoading(false);
    setError(null);
  };

  const close = () => {
    setSwitchedFunctionBlockId(null);
    clean();
  };

  const openModal = (functionBlockId: string | number) => {
    if (!functionBlockId && functionBlockId !== 0) {
      throw new Error('functionBlockId is required to open modal');
    }
    setSwitchedFunctionBlockId(functionBlockId);
  };

  const fillData = async () => {
    if (!switchedFunctionBlockId) {
      throw new Error('switchedFunctionBlockId is required to load version list');
    }
    setLoading(true);
    try {
      const [{ data: versionList }, { data: fbInformation }] = await Promise.all([
        requestGetFBVersionList(switchedFunctionBlockId),
        requestGetFBInformation(switchedFunctionBlockId),
      ]);
      console.log('fbInformation', fbInformation);
      const { currentVersionId } = fbInformation;
      setVersionList(versionList);
      setCurrentVersionId(currentVersionId);
      setError(null);
      setLoading(false);
    } catch (error) {
      setError(error + '');
      setLoading(false);
    }
  };

  const switchVersion = async (versionId: string | number) => {
    if (!versionId && versionId !== 0) {
      throw new Error('versionId is required to switch version');
    }
    if (!switchedFunctionBlockId && switchedFunctionBlockId !== 0) {
      throw new Error('switchedFunctionBlockId is required to switch version');
    }
    setLoading(true);
    try {
      await requestSwitchFunctionBlockVersion(switchedFunctionBlockId, versionId);
      setCurrentVersionId(versionId);
      message.success('switch version success!');
      setLoading(false);
    } catch (error) {
      message.error('switch version failed!');
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!switchedFunctionBlockId && switchedFunctionBlockId !== 0) {
      clean();
    } else {
      fillData();
    }
  }, [switchedFunctionBlockId]);

  return {
    switchedFunctionBlockId,
    setSwitchedFunctionBlockId,
    versionList,
    setVersionList,
    currentVersionId,
    setCurrentVersionId,
    loading,
    setLoading,
    error,
    setError,
    openModal,
    close,
    switchVersion,
  };
};

export default useFunctionBlockVersionSwitch;
