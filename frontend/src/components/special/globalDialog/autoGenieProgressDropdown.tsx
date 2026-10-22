import { useEffect, useState } from 'react';
import { Dropdown, Button, message, Spin, Card, Tag } from 'antd';
import { useModel } from 'umi';
import { requestDynamicGenerationPlanList } from '@/request/node';
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
  CloseOutlined,
  DownOutlined,
} from '@ant-design/icons';

interface Plan {
  generation_id: number;
  node_id: number;
  name: string;
  status: string;
  plan_status_message: string;
  created_time: number;
}

const AutoGenieProgressDropdown = () => {
  const { isDropdownVisible, setIsDropdownVisible, setSelectedPlan, setIsModalVisible } =
    useModel('autoGenieProgress');
  const { instance, nodes, setTemporaryCenteredNodeId, analysisId } = useModel('analysis');
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(false);

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

  const handleNodeFocus = (nodeId: string) => {
    const targetNode = nodes.find((node) => node.id === nodeId.toString());

    if (targetNode && instance) {
      setTemporaryCenteredNodeId(nodeId.toString());

      setTimeout(() => {
        setTemporaryCenteredNodeId(null);
      }, 800);

      instance.setCenter(targetNode.position.x, targetNode.position.y, {
        duration: 0,
        zoom: 1,
      });
    } else {
      message.error(`Node ${nodeId} not found in the current flow`);
    }
  };

  const fetchPlanList = async () => {
    setLoading(true);
    try {
      const result = await requestDynamicGenerationPlanList(analysisId!);
      if (result.code === 200 && result.data) {
        setPlans(result.data);
      } else {
        message.error('Failed to fetch plan list');
      }
    } catch (error) {
      message.error('Error fetching plan list');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isDropdownVisible && analysisId) {
      fetchPlanList();
    }
  }, [isDropdownVisible, analysisId]);

  const handlePlanClick = (plan: Plan) => {
    const isPlanLocked =
      plan.status === 'generation_failed' ||
      plan.status === 'generating' ||
      plan.status === 'execution_failed';

    if (!isPlanLocked) {
      setSelectedPlan({
        generationId: plan.generation_id,
        nodeId: plan.node_id,
        status: plan.status,
        name: plan.name,
        steps: '',
      });
      setIsModalVisible(true);
      setIsDropdownVisible(false);
    }
  };

  const renderPlanList = () => {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Spin size="small" />
          <div style={{ marginTop: 8, fontSize: '12px' }}>Loading plans...</div>
        </div>
      );
    }

    if (plans.length === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '20px 0', color: '#999', fontSize: '14px' }}>
          No plans available
        </div>
      );
    }

    return (
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {plans.map((plan) => {
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
                padding: '12px',
                marginBottom: '8px',
                border: '1px solid #f0f0f0',
                borderRadius: '6px',
                backgroundColor: '#fafafa',
                cursor: isPlanLocked ? 'default' : 'pointer',
                opacity: isPlanLocked ? 0.6 : 1,
                transition: 'all 0.3s',
              }}
              onClick={() => handlePlanClick(plan)}
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
                  <div style={{ marginLeft: 8, flex: 1 }}>
                    <div style={{ marginBottom: 2 }}>
                      <span style={{ fontWeight: 500, fontSize: '14px' }}>
                        {plan.name || 'Untitled Plan'}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      {formatDate(plan.created_time)}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Button
                    size="small"
                    onClick={(e: React.MouseEvent) => {
                      e.stopPropagation();
                      handleNodeFocus(plan.node_id.toString());
                    }}
                  >
                    Go to Node
                  </Button>
                  <Tag color={getPlanStatusColor(plan.status)}>
                    {getPlanStatusText(plan.status)}
                  </Tag>
                </div>
              </div>

              {hasStatusMessage && (
                <div
                  style={{
                    marginTop: '8px',
                    marginLeft: '28px',
                    padding: '6px 10px',
                    backgroundColor: '#fff7e6',
                    borderRadius: '4px',
                    fontSize: '12px',
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

  const dropdownContent = (
    <Card
      style={{
        width: '500px',
        maxWidth: '90vw',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      }}
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Auto Genie Plans</span>
          <Button
            icon={<CloseOutlined />}
            onClick={() => setIsDropdownVisible(false)}
            size="small"
            type="text"
          />
        </div>
      }
      bordered={false}
      bodyStyle={{ padding: '16px' }}
    >
      {renderPlanList()}
    </Card>
  );

  return (
    <Dropdown
      trigger={['click']}
      open={isDropdownVisible}
      onOpenChange={setIsDropdownVisible}
      overlay={dropdownContent}
      placement="bottomRight"
    >
      <Button
        style={{
          width: 'auto',
          minWidth: '100px',
          height: '3vh',
          fontSize: '1.5vh',
          padding: '0 1vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        type="default"
      >
        Auto Genie Plans
        <DownOutlined style={{ marginLeft: 8, fontSize: '12px' }} />
      </Button>
    </Dropdown>
  );
};

export default AutoGenieProgressDropdown;
