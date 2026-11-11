import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { useState, useEffect } from 'react';
import { Modal, Input, message, InputNumber, Select } from 'antd';
import { useModel } from 'umi';
import styles from './modals.less';
import { requestTriggerBugFixer } from '@/request/node';
import { LoadingOutlined } from '@ant-design/icons';
import { LLMModel, LLMModelList } from '@/constants/ai';

const BugFixerModal = () => {
  const { bugFixerInspectedNodeId, setBugFixerInspectedNodeId, currentSelectedNodes } =
    useModel('analysis');
  const { dictionary } = useModel('localization');
  const [fixerPrompt, setFixerPrompt] = useState('');
  const [isBugFixerStarting, setIsBugFixerStarting] = useState(false);
  const [maxDebug, setMaxDebug] = useState(3);
  const [llmModel, setLlmModel] = useState(LLMModel.GPT_4O_MINI); // Default LLM model

  useEffect(() => {
    const handleOpenBugFixerAI = () => {
      if (currentSelectedNodes.length === 0) {
        message.info(
          'Please select a node first. Click on a node to select it, then try Bug Fixer AI again.',
        );
      } else if (currentSelectedNodes.length === 1) {
        const selectedNode = currentSelectedNodes[0];
        if (selectedNode.data?.state !== 'failed') {
          message.info("Please select a node with 'failed' state to open the Bug Fixer AI.");
          return;
        }
        setBugFixerInspectedNodeId(selectedNode.id);
      } else {
        message.info(
          'Please select only one node. Deselect the extra nodes by clicking on them, then try Bug Fixer AI again.',
        );
      }
    };

    window.addEventListener('openBugFixerAI', handleOpenBugFixerAI);

    return () => {
      window.removeEventListener('openBugFixerAI', handleOpenBugFixerAI);
    };
  }, [currentSelectedNodes, setBugFixerInspectedNodeId]);

  const handleCancel = () => {
    setBugFixerInspectedNodeId(null);
  };

  const triggerFixer = async () => {
    setIsBugFixerStarting(true);
    try {
      console.log('Triggering bug fixer with prompt:', fixerPrompt);
      const response = await requestTriggerBugFixer(
        bugFixerInspectedNodeId,
        maxDebug,
        llmModel,
        fixerPrompt,
      );
      console.log('Trigger Bug Fixer response:', response);
      if (response.code !== 200) {
        throw new Error(response.message || 'Please try again later.');
      }
      message.success('Bug fixer was triggered successfully');
      setBugFixerInspectedNodeId(null);
    } catch (error: any) {
      console.error('Error triggering bug fixer:', error);
      message.error(`Failed to trigger bug fixer: ${error.message}`);
    }
    setIsBugFixerStarting(false);
  };

  return (
    <Modal
      title={<div style={{ textAlign: 'center', width: '100%' }}> {'Additional support'} </div>}
      visible={!!bugFixerInspectedNodeId}
      // confirmLoading={isBugFixerStarting}
      onCancel={handleCancel}
      footer={null}
      width={718}
      centered
    >
      <div className={styles.modalContent}>
        <div>
          <div className={styles.modalHeader}>Add extra information for debugging</div>
          <Input.TextArea
            placeholder="Input the extra link to help AI agent better understand the bug"
            autoSize={{ minRows: 5, maxRows: 10 }}
            onChange={(e) => setFixerPrompt(e.target.value)}
          />
        </div>
        <div>
          <div className={styles.modalHeader}>Maximum number of debugging rounds</div>
          <InputNumber
            defaultValue={3}
            min={1}
            onChange={(value) => setMaxDebug(value)}
            value={maxDebug}
            style={{ width: '100%' }}
          />
        </div>

        <div>
          <div className={styles.modalHeader}>Select LLM model for bug fixing</div>
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
          <button className={styles.generateButton} onClick={triggerFixer}>
            {isBugFixerStarting && <LoadingOutlined style={{ marginRight: '8px' }} />}
            {!isBugFixerStarting && (
              <CustomImage
                name={customIconNames.AIICONSTARWHITE}
                style={{ height: '16px', marginRight: '8px', cursor: 'pointer' }}
              />
            )}

            {dictionary.FIX_BUG}
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default BugFixerModal;
