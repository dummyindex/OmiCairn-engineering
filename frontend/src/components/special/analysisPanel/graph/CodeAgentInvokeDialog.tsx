import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { useState } from 'react';
import { Modal, message, InputNumber, Select } from 'antd';
import styles from './CodeAgentInvokeDialog.less';
import { requestCopyNode } from '@/request/node';
import { LoadingOutlined } from '@ant-design/icons';
import { LLMModel, LLMModelList } from '@/constants/ai';
import { requestInvokeCodeAgent } from '@/request/task';

interface CodeAgentInvokeDialogProps {
  visible: boolean;
  nodeId: string | null;
  onClose: () => void;
  buttonText?: string;
  title?: string;
}

const CodeAgentInvokeDialog: React.FC<CodeAgentInvokeDialogProps> = ({
  visible,
  nodeId,
  onClose,
  buttonText = 'Start Code Agent',
  title = 'Code Agent Configuration',
}) => {
  const [isStarting, setIsStarting] = useState(false);
  const [maxDebug, setMaxDebug] = useState(3);
  const [llmModel, setLlmModel] = useState(LLMModel.GPT_4O_MINI);

  const handleCancel = () => {
    onClose();
  };

  const triggerCodeAgent = async () => {
    if (!nodeId) {
      message.error('No node selected');
      return;
    }

    setIsStarting(true);
    try {
      console.log('Preparing to copy node before invoking code agent:', nodeId);
      const copyResponse = await requestCopyNode(nodeId, true);
      console.log('Copy Node response:', copyResponse);
      const newNodeId = copyResponse.data?.id;
      if (!newNodeId) {
        throw new Error('Failed to copy node. Cannot proceed with Code Agent.');
      }
      console.log('Triggering code agent for node:', newNodeId);
      const response = await requestInvokeCodeAgent(newNodeId, maxDebug, llmModel);
      console.log('Trigger Code Agent response:', response);

      if (response.code !== 200) {
        throw new Error(response.message || 'Please try again later.');
      }

      message.success('Code agent was triggered successfully');
      onClose();
    } catch (error: any) {
      console.error('Error triggering code agent:', error);
      message.error(`Failed to trigger code agent: ${error.message}`);
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <Modal
      title={<div style={{ textAlign: 'center', width: '100%' }}>{title}</div>}
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={718}
      centered
    >
      <div className={styles.modalContent}>
        <div>
          <div className={styles.modalHeader}>Maximum number of debugging rounds</div>
          <InputNumber
            defaultValue={3}
            min={1}
            onChange={(value) => setMaxDebug(value || 3)}
            value={maxDebug}
            style={{ width: '100%' }}
          />
        </div>

        <div>
          <div className={styles.modalHeader}>Select LLM model</div>
          <Select
            defaultValue={LLMModel.GPT_4O_MINI}
            value={llmModel}
            style={{ width: '100%' }}
            onChange={(value) => {
              console.log('Selected LLM Model:', value);
              setLlmModel(value);
            }}
          >
            {LLMModelList.map((modelOption) => {
              return (
                <Select.Option key={modelOption.id} value={modelOption.value}>
                  {modelOption.label}
                </Select.Option>
              );
            })}
          </Select>
        </div>

        <div className={styles.buttonContainer}>
          <button
            className={styles.generateButton}
            onClick={triggerCodeAgent}
            disabled={isStarting}
          >
            {isStarting && <LoadingOutlined style={{ marginRight: '8px' }} />}
            {!isStarting && (
              <CustomImage
                name={customIconNames.AIICONSTARWHITE}
                style={{ height: '16px', marginRight: '8px', cursor: 'pointer' }}
              />
            )}
            {buttonText}
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default CodeAgentInvokeDialog;
