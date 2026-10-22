import { generateSequence } from '@/util/common';

export const DefaultVCPU = 8;
export const DefaultMemory = 32;
export const DefaultTimeout = 3600;
export const DefaultGPU = 0;

export const DefaultComputationResourceConfig = {
  vcpu: DefaultVCPU,
  ram: DefaultMemory,
  timeout: DefaultTimeout,
  gpt: DefaultGPU,
};

export const Vcpu2MemoryOptions = {
  '0.25': [0.5, 1, 2],
  '0.5': generateSequence(1, 4, 1),
  1: generateSequence(2, 8, 1),
  2: generateSequence(4, 16, 1),
  4: generateSequence(8, 30, 1),
  8: generateSequence(16, 60, 4),
  16: generateSequence(32, 120, 8),
};
