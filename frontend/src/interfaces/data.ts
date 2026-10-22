export interface DataType {
  id: string;
  key: string;
  name: string;
  createdFrom: string;
  uploadType: string;
  species: string;
  description: string;
  createdTime: number;
  state: string;
  dataSize: number;
  errorMessage?: string;
}
