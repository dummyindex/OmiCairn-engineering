export type FileMap = Record<
  string,
  { type: 'file' | 'folder'; file: null | File; children: null | FileMap }
>;
