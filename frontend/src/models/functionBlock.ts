import {
  requestPublicFBGroupList,
  requestPrivateFBGroupList,
  requestUpdatedRecords,
} from '@/request/functionBlock';
import { getServerTime } from '@/util/common';
import { useState, useRef } from 'react';

const formatTime = (time: Date) => {
  // Zero-pad single digits
  const pad = (n: number) => (n < 10 ? `0${n}` : n);
  const year = time.getFullYear();
  const month = time.getMonth() + 1;
  const date = time.getDate();
  const hour = time.getHours();
  const minute = time.getMinutes();
  const second = time.getSeconds();
  return `${year}-${pad(month)}-${pad(date)} ${pad(hour)}:${pad(minute)}:${pad(second)}`;
};

const useFunctionBlock = () => {
  const startTime = useRef<string | null>();
  const updateTimer = useRef<NodeJS.Timeout | null>(null);
  const [functionBlockList, setFunctionBlockList] = useState<any[]>([]);
  const [functionBlockPrivateList, setFunctionBlockPrivateList] = useState<any[]>([]);
  const [fbId2Group, setFbId2Group] = useState<any>({});

  const loadFBList = async () => {
    startTime.current = formatTime(getServerTime());
    const { data: publicMenuList } = await requestPublicFBGroupList();
    const { data: result } = await requestPrivateFBGroupList();
    const fbId2Group: any = {};
    setFunctionBlockPrivateList(result);
    setFunctionBlockList(publicMenuList);
    result.forEach((group: any) => {
      group.functionBlockList.forEach((fb: any) => {
        fbId2Group[fb.id] = {
          group: group,
          public: false,
        };
      });
    });
    publicMenuList.forEach((group: any) => {
      group.functionBlockList.forEach((fb: any) => {
        fbId2Group[fb.id] = {
          group: group,
          public: true,
        };
      });
    });
    setFbId2Group(fbId2Group);
  };

  const updateFBList = async (startTimeStr: string) => {
    const { data: updatedRecords } = await requestUpdatedRecords(startTimeStr);
    if (updatedRecords.length > 0) {
      startTime.current = formatTime(getServerTime());
      await loadFBList();
    }
  };

  const initFBList = async () => {
    await loadFBList();
    if (updateTimer.current) {
      clearInterval(updateTimer.current);
    }
    const startTimeStr = formatTime(getServerTime());
    startTime.current = startTimeStr;
    updateTimer.current = setInterval(() => {
      updateFBList(startTime.current);
    }, 5000);
  };

  return {
    functionBlockList,
    fbId2Group,
    loadFBList,
    setFunctionBlockList,
    functionBlockPrivateList,
    setFunctionBlockPrivateList,
    initFBList,
  };
};

export default useFunctionBlock;
