import { useState } from 'react';
import { Modal, Input, message, InputNumber, Select, Form } from 'antd';
import styles from './visualizerModal.less';
import { LoadingOutlined } from '@ant-design/icons';
import { LLMModel, LLMModelList } from '@/constants/ai';
import CustomImage from '@/components/common/customImage';
import * as customIconNames from '@/assets/customIconNames';
import { requestCopyNode, requestLaunchVisualizerAgent } from '@/request/node';

/**
 * Visualizer Agent Launch Modal
 * Launches visualizer agent to generate visualization code
 *
 * API: POST /visualizer/launch-agent
 * Required params:
 * - node_id: string
 * - model: string
 * - demand: string
 * - figure_counts: number
 */
const VisualizerAgentModal = ({ nodeId, visible, onClose }) => {
  const [isLaunching, setIsLaunching] = useState(false);
  const [form] = Form.useForm();

  const handleCancel = () => {
    onClose();
    form.resetFields();
  };

  const handleLaunch = async () => {
    if (!nodeId) {
      message.error('Node ID is required');
      return;
    }

    // Get values from form
    const values = form.getFieldsValue();
    const { demand, model, figureCounts } = values;

    if (!demand || !demand.trim()) {
      message.warning('Please provide visualization requirements');
      return;
    }

    setIsLaunching(true);

    try {
      // Import the request function

      console.log('Launching visualizer agent with params:', {
        nodeId: nodeId,
        model: model,
        demand: demand,
        figureCounts: figureCounts,
      });

      const copyResponse = await requestCopyNode(nodeId, true);
      console.log('Copy Node response:', copyResponse);
      const copiedNodeId = copyResponse.data?.id;
      if (!copiedNodeId) {
        throw new Error('Failed to copy node for visualizer agent');
      }

      const response = await requestLaunchVisualizerAgent(
        copiedNodeId,
        model,
        demand,
        figureCounts,
      );

      console.log('Launch Visualizer Agent response:', response);

      if (response.code !== 200) {
        throw new Error(response.message || 'Failed to launch visualizer agent');
      }

      message.success('Visualizer agent launched successfully!');
      handleCancel();
    } catch (error: any) {
      console.error('Error launching visualizer agent:', error);
      message.error(`Failed to launch visualizer agent: ${error.message}`);
    } finally {
      setIsLaunching(false);
    }
  };

  return (
    <Modal
      title={<div style={{ textAlign: 'center', width: '100%' }}>Launch Visualizer Agent</div>}
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={718}
      centered
    >
      <div className={styles.modalContent}>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            model: LLMModel.GPT_5_MINI,
            figureCounts: 3,
          }}
        >
          <Form.Item
            label={<div className={styles.modalHeader}>Visualization Requirements</div>}
            name="demand"
            required
            rules={[{ required: true, message: 'Please provide visualization requirements' }]}
          >
            <Input.TextArea
              placeholder="Describe what kind of visualizations you want to generate. For example: 'Generate PCA plot, UMAP, and heatmap for top variable genes'"
              autoSize={{ minRows: 5, maxRows: 10 }}
            />
          </Form.Item>

          <Form.Item
            label={<div className={styles.modalHeader}>Number of Alternative Figures</div>}
            name="figureCounts"
            tooltip="The number of alternative visualization versions to generate"
          >
            <InputNumber min={1} max={10} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label={<div className={styles.modalHeader}>Select LLM Model</div>}
            name="model"
          >
            <Select style={{ width: '100%' }}>
              {LLMModelList.map((modelOption) => {
                return (
                  <Select.Option key={modelOption.id} value={modelOption.value}>
                    {modelOption.label}
                  </Select.Option>
                );
              })}
            </Select>
          </Form.Item>

          <div className={styles.buttonContainer}>
            <button className={styles.generateButton} onClick={handleLaunch} disabled={isLaunching}>
              {isLaunching && <LoadingOutlined style={{ marginRight: '8px' }} />}
              {!isLaunching && (
                <CustomImage
                  name={customIconNames.AIICONSTARWHITE}
                  style={{ height: '16px', marginRight: '8px', cursor: 'pointer' }}
                />
              )}
              {isLaunching ? 'Launching...' : 'Launch Visualizer'}
            </button>
          </div>
        </Form>
      </div>
    </Modal>
  );
};

export default VisualizerAgentModal;
