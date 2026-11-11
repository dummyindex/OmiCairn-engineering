import { VitessceStatus } from '@/interfaces/visualPanel';
import { requestVitessceState } from '@/request/data';

const _waitForVitesscePrehandle = async (dataId: string) => {
  let vitessceState = await requestVitessceState(dataId);
  if (
    !vitessceState ||
    [VitessceStatus.SUCCESS, VitessceStatus.FAILED].includes(vitessceState.status)
  ) {
    return vitessceState;
  }
  while ([VitessceStatus.PENDING, VitessceStatus.RUNNING].includes(vitessceState.status)) {
    await new Promise((resolve) => setTimeout(resolve, 6000));
    vitessceState = await requestVitessceState(dataId);
    if (!vitessceState) {
      throw new Error('[System Error] Vitessce state is null in the middle of waiting');
    }
  }
  return vitessceState;
};

const waitingDataIdSet = new Set<string>();

export const waitForVitesscePrehandle = async (dataId: string) => {
  if (waitingDataIdSet.has(dataId)) {
    return {
      dispatchSuccess: false,
      vitessceState: null,
    };
  }
  waitingDataIdSet.add(dataId);
  let vitessceState = null;
  try {
    vitessceState = await _waitForVitesscePrehandle(dataId);
  } catch (e) {
    console.error(e);
    return {
      dispatchSuccess: false,
      vitessceState,
    };
  } finally {
    waitingDataIdSet.delete(dataId);
  }
  return {
    dispatchSuccess: true,
    vitessceState,
  };
};
