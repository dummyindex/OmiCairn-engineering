import { useEffect, useState } from 'react';
import { Modal, Button, message, Spin, Input, Space, Tag, Popconfirm } from 'antd';
import { useModel } from 'umi';
import {
  requestDynamicGenerationPlanList,
  requestDynamicGenerationPlanGet,
  requestDynamicGenerationPlanUpdate,
  requestDynamicGenerationPlanDelete,
  requestCreateDynamicGenerationWithPlan,
  requestLaunchDynamicGenerationWithPlan,
  requestLaunchDynamicGenerationWithClaudeCode,
} from '@/request/node';
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
  EditOutlined,
  SaveOutlined,
  CloseOutlined,
  DeleteOutlined,
} from '@ant-design/icons';

interface Plan {
  generation_id: number;
  node_id: number;
  name: string;
  status: string;
  plan_status_message: string;
  created_time: number;
  generation_mode?: string;
}

const AutoGenieProgressModal = () => {
  const { isModalVisible, setIsModalVisible, selectedPlan, setSelectedPlan } =
    useModel('autoGenieProgress');
  const { autoGenieInspectedNodeId } = useModel('analysis');
  const { analysisId } = useModel('analysis');
  const [planList, setPlanList] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'detail'>('list');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isEditingPlan, setIsEditingPlan] = useState(false);
  const [editedSteps, setEditedSteps] = useState<string>('');
  const [parsedSteps, setParsedSteps] = useState<{ text: string; completed: boolean }[]>([]);
  const [deletingPlanId, setDeletingPlanId] = useState<number | null>(null);

  const getPlanStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'generating':
      case 'executing':
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      case 'generated':
      case 'stopped':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'generation_failed':
      case 'execution_failed':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
    }
  };

  const getPlanStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'generating':
      case 'executing':
        return 'processing';
      case 'generated':
      case 'stopped':
        return 'success';
      case 'generation_failed':
      case 'execution_failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getPlanStatusText = (status: string) => {
    if (!status) return 'Loading';
    const statusMap: Record<string, string> = {
      generating: 'Generating',
      generated: 'Generated',
      generation_failed: 'Generation Failed',
      executing: 'Executing',
      stopped: 'Stopped',
      execution_failed: 'Execution Failed',
    };
    return (
      statusMap[status.toLowerCase()] ||
      status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
    );
  };

  const formatDate = (timestamp: number) => {
    if (!timestamp) return 'N/A';
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return 'N/A';
    }
  };

  const fetchPlanList = async () => {
    setLoading(true);
    try {
      const result = await requestDynamicGenerationPlanList(analysisId!);
      if (result.code === 200 && result.data) {
        setPlanList(result.data);
      } else {
        message.error('Failed to fetch plan list');
      }
    } catch (error) {
      message.error('Error fetching plan list');
    } finally {
      setLoading(false);
    }
  };

  const parseSteps = (stepsString: string): { text: string; completed: boolean }[] => {
    const lines = stepsString.split('\n').filter((line) => line.trim());
    return lines.map((line) => {
      const match = line.match(/^-\s*\[([\sxX✓]?)\]\s*(.*)$/);
      if (match) {
        return {
          text: match[2].trim(),
          completed: match[1].toLowerCase() === 'x' || match[1] === '✓',
        };
      }
      return { text: line.trim(), completed: false };
    });
  };

  const fetchPlanDetail = async () => {
    if (!selectedPlan) {
      return;
    }

    setDetailLoading(true);
    try {
      const result = await requestDynamicGenerationPlanGet(
        String(autoGenieInspectedNodeId || selectedPlan.nodeId),
        String(selectedPlan.generationId),
      );
      if (result.code === 200 && result.data?.presigned_url) {
        const response = await fetch(result.data.presigned_url);
        if (!response.ok) {
          throw new Error(`Failed to fetch plan data: ${response.status}`);
        }

        const planData = await response.json();
        setSelectedPlan((prev) =>
          prev
            ? {
                ...prev,
                name: planData.name,
                steps: planData.steps,
                generationMode:
                  prev.generationMode || planData.generation_mode || planData.generationMode,
              }
            : null,
        );

        if (planData.steps && typeof planData.steps === 'string') {
          const parsed = parseSteps(planData.steps);
          setParsedSteps(parsed);
          setEditedSteps(planData.steps);
        }
      }
    } catch (error) {
      message.error('Failed to fetch plan details');
    } finally {
      setDetailLoading(false);
    }
  };

  const parseNewGeneratedSteps = (stepsString: string) => {
    const parsed = parseSteps(stepsString);
    setParsedSteps(parsed);
    return parsed;
  };

  useEffect(() => {
    if (isModalVisible && analysisId) {
      fetchPlanList();
    }
  }, [isModalVisible, analysisId]);

  useEffect(() => {
    if (
      selectedPlan?.generationId &&
      selectedPlan?.nodeId &&
      !selectedPlan.steps &&
      viewMode === 'detail'
    ) {
      fetchPlanDetail();
    }
  }, [selectedPlan?.generationId, selectedPlan?.nodeId, viewMode]);

  useEffect(() => {
    if (isModalVisible && selectedPlan) {
      parseNewGeneratedSteps(selectedPlan.steps);
      setViewMode('detail');
    }
  }, [isModalVisible, selectedPlan]);

  const handleCancel = () => {
    setIsModalVisible(false);
    setSelectedPlan(null);
    setIsEditingPlan(false);
    setEditedSteps('');
    setParsedSteps([]);
  };

  const handleSavePlan = async () => {
    if (!selectedPlan || !editedSteps) return;

    setDetailLoading(true);
    try {
      const updateData = {
        ...selectedPlan.steps,
        steps: editedSteps,
      };

      const result = await requestDynamicGenerationPlanUpdate(
        String(autoGenieInspectedNodeId || selectedPlan.nodeId),
        String(selectedPlan.generationId),
        updateData,
      );

      if (result.code === 200) {
        message.success('Plan updated successfully');
        setIsEditingPlan(false);
        const parsed = parseSteps(editedSteps);
        setParsedSteps(parsed);
      } else {
        message.error('Failed to update plan');
      }
    } catch (error) {
      message.error('Error updating plan');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleEditToggle = () => {
    if (isEditingPlan) {
      setEditedSteps(typeof selectedPlan?.steps === 'string' ? selectedPlan.steps : '');
      setIsEditingPlan(false);
    } else {
      setIsEditingPlan(true);
    }
  };

  const canDeletePlan = (status: string) => {
    return status === 'generated' || status === 'generation_failed';
  };

  const handleDeletePlan = async (plan: Plan) => {
    setDeletingPlanId(plan.generation_id);
    try {
      const result = await requestDynamicGenerationPlanDelete(
        String(plan.generation_id),
        String(plan.node_id),
      );
      if (result.code === 200) {
        message.success('Plan deleted successfully');
        fetchPlanList();
        // If we're in detail view of the deleted plan, go back to list
        if (selectedPlan?.generationId === plan.generation_id) {
          setSelectedPlan(null);
          setViewMode('list');
        }
      } else {
        message.error(result.message || 'Failed to delete plan');
      }
    } catch (error) {
      message.error('Error deleting plan');
    } finally {
      setDeletingPlanId(null);
    }
  };

  const handleLaunchWithPlan = async () => {
    if (!selectedPlan) return;

    // Ensure generationMode is set before launching
    if (!selectedPlan.generationMode) {
      message.warning('Generation mode not detected. Defaulting to standard generation.');
    }

    setIsGenerating(true);
    try {
      const creationResponse = await requestCreateDynamicGenerationWithPlan(
        String(selectedPlan.generationId),
        String(selectedPlan.nodeId),
      );
      if (creationResponse.code !== 200) {
        message.error(
          `Failed to create dynamic FB generation: ${
            creationResponse.message || 'Please try again later.'
          }`,
        );
        return;
      }
      if (selectedPlan.generationMode === 'claude_code') {
        const launchResponse = await requestLaunchDynamicGenerationWithClaudeCode(
          String(selectedPlan.generationId),
          String(selectedPlan.nodeId),
        );
        if (launchResponse.code !== 200) {
          message.error(
            `Failed to launch Agent execution: ${
              launchResponse.message || 'Please try again later.'
            }`,
          );
          return;
        }
        message.success('Agent execution started successfully!');
      } else {
        const launchResponse = await requestLaunchDynamicGenerationWithPlan(
          String(selectedPlan.generationId),
        );
        if (launchResponse.code !== 200) {
          message.error(
            `Failed to launch dynamic FB generation: ${
              launchResponse.message || 'Please try again later.'
            }`,
          );
          return;
        }
        message.success('Function block generation started successfully!');
      }
      handleCancel();
    } catch (error: any) {
      if (error.response) {
        message.error(`Server error: ${error.response.message || 'Please try again later.'}`);
      } else if (error.request) {
        message.error(
          'Network error: Unable to connect to the server. Please check your connection.',
        );
      } else {
        message.error(`Unexpected error: ${error.message}`);
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const renderPlanList = () => {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>Loading planList...</div>
        </div>
      );
    }

    if (planList.length === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          No planList available
        </div>
      );
    }

    return (
      <div style={{ minHeight: '200px' }}>
        {planList.map((plan) => {
          const isPlanLocked =
            plan.status === 'generation_failed' ||
            plan.status === 'generating' ||
            plan.status === 'execution_failed';
          const hasStatusMessage =
            plan.plan_status_message && plan.plan_status_message.trim() !== '';

          return (
            <div
              key={plan.generation_id}
              style={{
                padding: '16px',
                marginBottom: '12px',
                border: '1px solid #f0f0f0',
                borderRadius: '8px',
                backgroundColor: '#fafafa',
                cursor: isPlanLocked ? 'default' : 'pointer',
                opacity: isPlanLocked ? 0.6 : 1,
                transition: 'all 0.3s',
              }}
              onClick={
                isPlanLocked
                  ? undefined
                  : () => {
                      setSelectedPlan({
                        generationId: plan.generation_id,
                        nodeId: plan.node_id,
                        status: plan.status,
                        name: plan.name,
                        steps: '',
                        generationMode: plan.generation_mode,
                      });
                      setViewMode('detail');
                    }
              }
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                  {getPlanStatusIcon(plan.status)}
                  <div style={{ marginLeft: 12, flex: 1 }}>
                    <div style={{ marginBottom: 4 }}>
                      <span style={{ fontWeight: 500, fontSize: '16px' }}>
                        {plan.name || 'Untitled Plan'}
                      </span>
                    </div>
                    <div style={{ fontSize: '14px', color: '#666' }}>
                      {formatDate(plan.created_time)}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <Tag color={getPlanStatusColor(plan.status)}>
                    {getPlanStatusText(plan.status)}
                  </Tag>
                </div>
              </div>

              {hasStatusMessage && (
                <div
                  style={{
                    marginTop: '12px',
                    marginLeft: '36px',
                    padding: '8px 12px',
                    backgroundColor: '#fff7e6',
                    borderRadius: '4px',
                    fontSize: '14px',
                    color: '#d46b08',
                    borderLeft: '3px solid #faad14',
                  }}
                >
                  {plan.plan_status_message}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderPlanDetail = () => {
    if (detailLoading) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>Loading plan details...</div>
        </div>
      );
    }

    return (
      <div style={{ minHeight: '300px' }}>
        {selectedPlan && (
          <div
            style={{
              marginBottom: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center' }}>
              {getPlanStatusIcon(selectedPlan.status)}
              <span style={{ marginLeft: 8, fontWeight: 500, fontSize: '16px' }}>
                Plan Status: {getPlanStatusText(selectedPlan.status)}
              </span>
            </div>
            <Space>
              {selectedPlan.status === 'generated' && (
                <Button
                  icon={isEditingPlan ? <CloseOutlined /> : <EditOutlined />}
                  onClick={handleEditToggle}
                >
                  {isEditingPlan ? 'Cancel' : 'Edit Plan'}
                </Button>
              )}
              {canDeletePlan(selectedPlan.status) && (
                <Popconfirm
                  title="Delete Plan"
                  description="Are you sure you want to delete this plan? This action cannot be undone."
                  onConfirm={() =>
                    handleDeletePlan({
                      generation_id: selectedPlan.generationId,
                      node_id: selectedPlan.nodeId,
                      name: selectedPlan.name || '',
                      status: selectedPlan.status,
                      plan_status_message: '',
                      created_time: 0,
                    })
                  }
                  okText="Delete"
                  cancelText="Cancel"
                  okButtonProps={{ danger: true }}
                >
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                    loading={deletingPlanId === selectedPlan.generationId}
                  >
                    Delete Plan
                  </Button>
                </Popconfirm>
              )}
            </Space>
          </div>
        )}

        {/* Plan Name */}
        {selectedPlan && (
          <div style={{ marginBottom: 24 }}>
            <h3>{selectedPlan.name || 'Untitled Plan'}</h3>
          </div>
        )}

        {isEditingPlan ? (
          <div style={{ marginBottom: 24 }}>
            <h4>Edit Steps (use &quot;- [ ]&quot; format for each step):</h4>
            <Input.TextArea
              value={editedSteps}
              onChange={(e) => setEditedSteps(e.target.value)}
              rows={10}
              placeholder="- [ ] Step 1&#10;- [ ] Step 2&#10;- [x] Completed step"
              style={{ fontFamily: 'monospace' }}
            />
            <div style={{ marginTop: 16 }}>
              <Space>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={handleSavePlan}
                  loading={detailLoading}
                >
                  Save Changes
                </Button>
                <Button onClick={handleEditToggle}>Cancel</Button>
              </Space>
            </div>
          </div>
        ) : (
          parsedSteps.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <h4>Steps:</h4>
              <div
                style={{
                  padding: '16px',
                  borderRadius: '8px',
                  backgroundColor: '#fafafa',
                  border: '1px solid #e0e0e0',
                }}
              >
                {parsedSteps.map((step, index) => (
                  <div
                    key={index}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      marginBottom: index < parsedSteps.length - 1 ? '8px' : 0,
                    }}
                  >
                    <span
                      style={{
                        fontWeight: 500,
                        marginRight: '12px',
                        color: '#1890ff',
                        minWidth: '30px',
                      }}
                    >
                      {index + 1}.
                    </span>
                    <span
                      style={{
                        flex: 1,
                        textDecoration: step.completed ? 'line-through' : 'none',
                        color: step.completed ? '#999' : '#333',
                      }}
                    >
                      {step.text}
                    </span>
                    {step.completed && (
                      <CheckCircleOutlined style={{ color: '#52c41a', marginLeft: '8px' }} />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )
        )}

        <div style={{ marginTop: 24, textAlign: 'right' }}>
          <Space>
            <Button onClick={() => setViewMode('list')}>Back to Plan List</Button>
            {selectedPlan?.status === 'generated' && !isEditingPlan && (
              <Button
                type="primary"
                onClick={handleLaunchWithPlan}
                loading={isGenerating}
                disabled={isGenerating}
              >
                Generate
              </Button>
            )}
          </Space>
        </div>
      </div>
    );
  };

  return (
    <Modal
      title={viewMode === 'list' ? 'Auto Genie Plans' : 'Auto Genie Plan Details'}
      open={isModalVisible}
      onCancel={handleCancel}
      footer={[
        <Button key="close" onClick={handleCancel}>
          Close
        </Button>,
      ]}
      width={900}
      bodyStyle={{
        maxHeight: '70vh',
        overflowY: 'auto',
        padding: '24px',
      }}
      centered
    >
      {viewMode === 'list' ? renderPlanList() : renderPlanDetail()}
    </Modal>
  );
};

export default AutoGenieProgressModal;
