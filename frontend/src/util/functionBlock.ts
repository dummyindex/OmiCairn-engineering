import { FunctionBlockState } from '@/constants/functionBlock';

export const FunctionBlockStateColorV1 = {
  [FunctionBlockState.UNUPLOAD]: '#d9d9d9',
  [FunctionBlockState.PREHANDLING]: '#faad14',
  [FunctionBlockState.OK]: '#FFF',
  [FunctionBlockState.FAILED]: '#f5222d',
};

export const FunctionBlockStateColorV2 = {
  [FunctionBlockState.UNUPLOAD]: '#8cebebff',
  [FunctionBlockState.PREHANDLING]: '#faad14',
  [FunctionBlockState.OK]: '#c8f3f3ff',
  [FunctionBlockState.FAILED]: '#f35106ff',
};

export class FunctionBlockTool {
  static getFBColor(state: string, isV2: boolean): string {
    if (isV2) {
      return FunctionBlockStateColorV2[state] || 'red';
    }
    return FunctionBlockStateColorV1[state] || 'grey';
  }
}
