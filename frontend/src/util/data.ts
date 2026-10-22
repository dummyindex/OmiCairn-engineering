import { DataState } from '@/constants/data';

const DataStateColor = {
  [DataState.UPLOADING]: 'rgba(114, 120, 185, 1)',
  [DataState.PROCESSING]: 'rgba(114, 120, 185, 1)',
  [DataState.PREHANDLING]: 'rgba(114, 120, 185, 1)',
  [DataState.ERROR]: 'rgba(245, 34, 45, 1)',
  [DataState.OK]: 'rgb(70, 77, 154)',
};

const DataStateColorV2 = {
  [DataState.UPLOADING]: 'rgba(114, 120, 185, 1)',
  [DataState.PROCESSING]: 'rgba(114, 120, 185, 1)',
  [DataState.PREHANDLING]: 'rgba(114, 120, 185, 1)',
  [DataState.ERROR]: 'rgba(245, 34, 45, 1)',
  [DataState.OK]: 'rgba(6, 191, 247, 1)',
};

export class DataTool {
  static getStateColor(state: number): string {
    return DataStateColor[state] || 'grey';
  }

  static getDataMenuColor(state: string, uploadType: string): string {
    if (uploadType === 'general') {
      return DataStateColorV2[state] || 'grey';
    }
    return DataStateColor[state] || 'grey';
  }
}
