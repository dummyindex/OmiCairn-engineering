import React, { useState, useEffect } from 'react';
import { Modal, Button, Select, Checkbox, Spin, Image, message } from 'antd';
import { DownOutlined, RightOutlined, LoadingOutlined } from '@ant-design/icons';
import { LLMModel, LLMModelList } from '@/constants/ai';
import { NodeType } from '@/constants/node';
import { requestLatestComputation } from '@/request/computation';
import { requestGetFigureInfo } from '@/request/attachedData';
import { requestListFigureV2 } from '@/request/figure';
import { requestPreviousNodeList } from '@/request/node';

interface ReporterFunctionBlockSelectionModalProps {
  visible: boolean;
  nodeId: string;
  onCancel: () => void;
  onProceed: (
    selectedNodeIds: string[],
    selectedFigures: Record<string, { figureUuid: string; figureName: string }[]>,
    selectedModel: string,
  ) => void;
}

const ReporterFunctionBlockSelectionModal: React.FC<ReporterFunctionBlockSelectionModalProps> = ({
  visible,
  nodeId,
  onCancel,
  onProceed,
}) => {
  const [branchNodesList, setBranchNodesList] = useState<any[]>([]);
  const [isLoadingBranchNodes, setIsLoadingBranchNodes] = useState<boolean>(false);
  const [selectedNodeIds, setSelectedNodeIds] = useState<string[]>([]);
  const [nodeFigures, setNodeFigures] = useState<Record<string, any[]>>({});
  const [selectedFigures, setSelectedFigures] = useState<
    Record<string, { figureUuid: string; figureName: string }[]>
  >({});
  const [expandedNodeId, setExpandedNodeId] = useState<string | null>(null);
  const [loadingFigures, setLoadingFigures] = useState<Record<string, boolean>>({});
  const [originalImageUrls, setOriginalImageUrls] = useState<Record<string, string>>({});
  const [selectedReporterLLMModel, setSelectedReporterLLMModel] = useState<string>(LLMModel.GPT_5);

  const getPendingFunctionBlocks = async () => {
    try {
      const { data } = await requestPreviousNodeList(nodeId, true);
      console.log('Previous node list data:', data);
      return data.filter(
        (node: any) =>
          (node.type === NodeType.COMPUTATION_NODE ||
            node.type === NodeType.COMPUTATION_NODE_V2 ||
            node.type === NodeType.NOTEBOOK_NODE) &&
          node.state === 'finished',
      );
    } catch (error) {
      console.error('Error fetching previous node list:', error);
      return [];
    }
  };

  const loadBranchNodes = async () => {
    setIsLoadingBranchNodes(true);
    setBranchNodesList([]);
    setSelectedNodeIds([]);
    try {
      const branchNodes = await getPendingFunctionBlocks();
      setBranchNodesList(branchNodes);
    } catch (error) {
      console.error('Error loading branch nodes:', error);
      message.error('Failed to load function block nodes');
    } finally {
      setIsLoadingBranchNodes(false);
    }
  };

  useEffect(() => {
    if (visible) {
      loadBranchNodes();
    } else {
      // Reset state when modal is closed
      setBranchNodesList([]);
      setSelectedNodeIds([]);
      setNodeFigures({});
      setSelectedFigures({});
      setExpandedNodeId(null);
      setLoadingFigures({});
      setOriginalImageUrls({});
    }
  }, [visible]);

  const fetchNodeFigures = async (nodeId: string) => {
    if (nodeFigures[nodeId]) {
      return nodeFigures[nodeId];
    }

    setLoadingFigures((prev) => ({ ...prev, [nodeId]: true }));
    try {
      const { data: latestComputation } = await requestLatestComputation(nodeId);
      const { id: computationId } = latestComputation;
      const { data: figuresResponse } = await requestListFigureV2(computationId);

      const figures = figuresResponse || [];
      setNodeFigures((prev) => ({ ...prev, [nodeId]: figures }));
      setSelectedFigures((prev) => ({ ...prev, [nodeId]: [] }));

      return figures;
    } catch (error) {
      console.error('Error fetching figures for node:', nodeId, error);
      return [];
    } finally {
      setLoadingFigures((prev) => ({ ...prev, [nodeId]: false }));
    }
  };

  const loadFigureOriginalImageUrl = async (figureUuid: string) => {
    if (originalImageUrls[figureUuid]) {
      return originalImageUrls[figureUuid];
    }

    try {
      const url = await requestGetFigureInfo(figureUuid, false);
      setOriginalImageUrls((prev) => ({ ...prev, [figureUuid]: url }));
      return url;
    } catch (error) {
      console.error('Error loading original image URL for figure:', figureUuid, error);
      return '';
    }
  };

  const handleNodeSelection = (nodeId: string, checked: boolean) => {
    if (checked) {
      setSelectedNodeIds([...selectedNodeIds, nodeId]);
    } else {
      setSelectedNodeIds(selectedNodeIds.filter((id) => id !== nodeId));
      setSelectedFigures((prev) => {
        const updated = { ...prev };
        delete updated[nodeId];
        return updated;
      });
    }
  };

  const handleNodeExpansion = async (nodeId: string) => {
    if (expandedNodeId === nodeId) {
      setExpandedNodeId(null);
    } else {
      setExpandedNodeId(nodeId);
      await fetchNodeFigures(nodeId);
    }
  };

  const handleFigureSelection = (
    nodeId: string,
    figureUuid: string,
    figureName: string,
    checked: boolean,
  ) => {
    setSelectedFigures((prev) => {
      const currentFigures = prev[nodeId] || [];
      if (checked) {
        const totalSelectedFigures = Object.values(prev).flat().length;
        if (totalSelectedFigures >= 20) {
          message.warning('You can select a maximum of 20 figures in total.');
          return prev;
        }

        if (!selectedNodeIds.includes(nodeId)) {
          setSelectedNodeIds([...selectedNodeIds, nodeId]);
        }
        return { ...prev, [nodeId]: [...currentFigures, { figureUuid, figureName }] };
      } else {
        return {
          ...prev,
          [nodeId]: currentFigures.filter((figure) => figure.figureUuid !== figureUuid),
        };
      }
    });
  };

  const handleProceed = () => {
    if (selectedNodeIds.length === 0) {
      message.warning('Please select at least one function block node.');
      return;
    }
    onProceed(selectedNodeIds, selectedFigures, selectedReporterLLMModel);
  };

  return (
    <Modal
      title="Reporter - Function Block Selection"
      visible={visible}
      onCancel={onCancel}
      footer={[
        <Button
          key="proceed"
          type="primary"
          onClick={handleProceed}
          disabled={isLoadingBranchNodes || selectedNodeIds.length === 0}
        >
          Proceed
        </Button>,
      ].filter(Boolean)}
      width={900}
      centered
    >
      {isLoadingBranchNodes ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>Loading function block nodes...</div>
        </div>
      ) : (
        <>
          <div>
            <h4>Select LLM model for report generation:</h4>
            <Select
              style={{ width: '100%', marginBottom: 16 }}
              value={selectedReporterLLMModel}
              onChange={(value) => setSelectedReporterLLMModel(value)}
              placeholder="Select a model"
            >
              {LLMModelList.map((model) => (
                <Select.Option key={model.id} value={model.value} title={model.description}>
                  {model.label}
                </Select.Option>
              ))}
            </Select>
          </div>
          <div style={{ marginBottom: 16 }}>
            <h4>Current Branch Function Block Nodes</h4>
            <p>
              Select function block nodes from the current execution branch to include in the report
              generation.
            </p>
            <div
              style={{
                marginBottom: 8,
                color:
                  Object.values(selectedFigures).flat().length >= 20
                    ? '#ff4d4f'
                    : Object.values(selectedFigures).flat().length >= 15
                    ? '#faad14'
                    : '#666',
              }}
            >
              Selected Nodes: {selectedNodeIds.length} | Selected Figures:{' '}
              {Object.values(selectedFigures).flat().length}/20
            </div>
          </div>
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {branchNodesList.map((node: any, index: number) => (
              <div
                key={node.id}
                style={{
                  border: '1px solid #e8e8e8',
                  borderRadius: '4px',
                  marginBottom: '8px',
                  backgroundColor: selectedNodeIds.includes(node.id) ? '#e6f7ff' : '#f9f9f9',
                }}
              >
                <div
                  style={{
                    padding: '12px',
                    position: 'relative',
                    cursor: 'pointer',
                  }}
                  onClick={() => handleNodeExpansion(node.id)}
                >
                  <Checkbox
                    checked={selectedNodeIds.includes(node.id)}
                    onChange={(e) => {
                      handleNodeSelection(node.id, e.target.checked);
                    }}
                    onClick={(e) => e.stopPropagation()}
                    style={{ position: 'absolute', left: '12px', top: '12px' }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      left: '40px',
                      top: '8px',
                      width: '4px',
                      height: '4px',
                      backgroundColor: '#1890ff',
                      borderRadius: '50%',
                    }}
                  />
                  <div style={{ fontWeight: 'bold', marginBottom: '4px', marginLeft: '44px' }}>
                    {node.name || `Node ${index + 1}`}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666', marginLeft: '44px' }}>
                    ID: {node.id} | State: {node.state}
                  </div>
                  <div
                    style={{
                      position: 'absolute',
                      right: '12px',
                      top: '12px',
                      cursor: 'pointer',
                      padding: '4px',
                      pointerEvents: 'none',
                    }}
                  >
                    {expandedNodeId === node.id ? <DownOutlined /> : <RightOutlined />}
                  </div>
                </div>

                {expandedNodeId === node.id && (
                  <div style={{ padding: '0 12px 12px 44px', borderTop: '1px solid #f0f0f0' }}>
                    <div style={{ fontWeight: 'bold', marginTop: '8px', marginBottom: '8px' }}>
                      Figures ({selectedFigures[node.id]?.length || 0} selected):
                    </div>
                    {loadingFigures[node.id] ? (
                      <div style={{ textAlign: 'center', padding: '20px' }}>
                        <LoadingOutlined style={{ fontSize: 16, marginRight: 8 }} />
                        Loading figures...
                      </div>
                    ) : (
                      <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
                        {(nodeFigures[node.id] || []).map((figure: any, figureIndex: number) => (
                          <div
                            key={figure.figureUuid}
                            style={{ marginBottom: '8px', display: 'flex', alignItems: 'center' }}
                          >
                            <Checkbox
                              checked={(selectedFigures[node.id] || []).some(
                                (selectedFigure) => selectedFigure.figureUuid === figure.figureUuid,
                              )}
                              onChange={(e) =>
                                handleFigureSelection(
                                  node.id,
                                  figure.figureUuid,
                                  figure.figureName,
                                  e.target.checked,
                                )
                              }
                              style={{ marginRight: '8px' }}
                            />
                            <div
                              style={{
                                minWidth: '24px',
                                height: '20px',
                                borderRadius: '4px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '11px',
                                fontWeight: 500,
                                color: '#666',
                                marginRight: '8px',
                              }}
                            >
                              {figureIndex + 1}
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ fontSize: '13px', fontWeight: 500 }}>
                                {figure.figureName}
                              </div>
                            </div>
                            {figure.thumbnailUrl && (
                              <Image
                                src={figure.thumbnailUrl}
                                alt={figure.figureName}
                                style={{
                                  width: '60px',
                                  height: '60px',
                                  objectFit: 'cover',
                                  borderRadius: '4px',
                                  marginLeft: '8px',
                                  cursor: 'pointer',
                                }}
                                placeholder={
                                  <div
                                    style={{
                                      width: '80px',
                                      height: '80px',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      backgroundColor: '#f5f5f5',
                                      borderRadius: '4px',
                                    }}
                                  >
                                    <LoadingOutlined style={{ fontSize: 16 }} />
                                  </div>
                                }
                                preview={{
                                  src: originalImageUrls[figure.figureUuid] || figure.thumbnailUrl,
                                  onVisibleChange: async (visible) => {
                                    if (visible && !originalImageUrls[figure.figureUuid]) {
                                      await loadFigureOriginalImageUrl(figure.figureUuid);
                                    }
                                  },
                                }}
                              />
                            )}
                          </div>
                        ))}
                        {(nodeFigures[node.id] || []).length === 0 && (
                          <div
                            style={{
                              textAlign: 'center',
                              padding: '10px',
                              color: '#999',
                              fontSize: '12px',
                            }}
                          >
                            No figures found for this node.
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {index < branchNodesList.length - 1 && (
                  <div
                    style={{
                      position: 'absolute',
                      left: '37px',
                      bottom: '-8px',
                      width: '2px',
                      height: '8px',
                      backgroundColor: '#d9d9d9',
                    }}
                  />
                )}
              </div>
            ))}
            {branchNodesList.length === 0 && (
              <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                No finished function block nodes found in the current branch.
              </div>
            )}
          </div>
        </>
      )}
    </Modal>
  );
};

export default ReporterFunctionBlockSelectionModal;
