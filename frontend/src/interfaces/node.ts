export interface Node {
    analysisId: number;
    computationParams: string | null;
    createdTime: number | null;
    dataId: number | null;
    functionBlockId: number | null;
    id: number;
    locked: boolean;
    name: string | null;
    state: string;
    type: string;
    x: number;
    y: number;
}