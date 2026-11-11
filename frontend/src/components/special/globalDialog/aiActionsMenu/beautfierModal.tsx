import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { useState } from 'react';
import { Modal, Select, InputNumber, Popover, Input, message } from 'antd';
import { useModel } from 'umi';
import { SystemEnv } from '@/constants/computation';
import styles from './modals.less';
import { requestCreateVisualizer, requestLaunchingVisualizer } from '@/request/node';
import { LoadingOutlined, QuestionCircleOutlined } from '@ant-design/icons';

const BeautfierModal = () => {
  const { beautifierInspectedNodeId, setBeautifierInspectedNodeId } = useModel('analysis');
  const { dictionary } = useModel('localization');
  const [isVisualizerStarting, setIsVisualizerStarting] = useState(false);
  const [visualizerPrompt, setVisualizerPrompt] = useState('');
  const [visualizerMaxNode, setVisualizerMaxNode] = useState<string | number | null>('3');
  const [visualizerSystemEnv, setVisualizerSystemEnv] = useState<string | null>(
    SystemEnv.SERVER_LOCAL,
  );

  const handleCancel = () => {
    setBeautifierInspectedNodeId(null);
  };

  const launchVisualizer = async (nodeId) => {
    setIsVisualizerStarting(true);
    try {
      const computationResourceConfigure = {
        ram: 120,
        vcpu: 16,
        timeout: 21600,
        gpu: 0,
        system_env: visualizerSystemEnv,
      };
      const createResponse = await requestCreateVisualizer(
        nodeId,
        visualizerMaxNode,
        visualizerPrompt,
        computationResourceConfigure,
      );
      console.log('Visualizer Creation response:', createResponse);
      if (createResponse.code !== 200) {
        throw new Error(createResponse.message || 'Please try again later.');
      }
      const visualizerId = createResponse.data.id;
      const launchResponse = await requestLaunchingVisualizer(visualizerId);
      console.log('Visualizer Launch response:', launchResponse);
      if (launchResponse.code !== 200) {
        throw new Error(launchResponse.message || 'Please try again later.');
      }
    } catch (error: any) {
      message.error(`Failed to launch visualizer: ${error.message || 'Please try again later.'}`);
      console.error('Error launching visualizer:', error);
    } finally {
      setIsVisualizerStarting(false);
      setBeautifierInspectedNodeId(null);
      setVisualizerPrompt('');
    }
  };

  return (
    <Modal
      title={<div style={{ textAlign: 'center', width: '100%' }}> {dictionary.BEAUTIFY} </div>}
      visible={!!beautifierInspectedNodeId}
      confirmLoading={isVisualizerStarting}
      onCancel={handleCancel}
      footer={null}
      width={740}
      centered
      bodyStyle={{
        maxHeight: 'calc(100vh - 150px)',
        overflowY: 'auto',
        overflowX: 'hidden',
      }}
    >
      <div
        className={styles.modalContent}
        onClick={(e) => {
          e.stopPropagation(); // Stop propagation so clicks do not close the Modal
        }}
      >
        <div>
          <div className={styles.modalHeader}>
            <span className={styles.labelRequired}>*</span> How do you want to beautify the figures?
          </div>
          <Input.TextArea
            placeholder="e.g. I want to get a dark background ..."
            autoSize={{ minRows: 4, maxRows: 10 }}
            onChange={(e) => setVisualizerPrompt(e.target.value)}
          />
        </div>

        <div>
          <div className={styles.modalHeader}>Where do you want to run the computations?</div>
          <Select
            defaultValue={SystemEnv.SERVER_LOCAL}
            style={{ width: '100%' }}
            onChange={(value) => setVisualizerSystemEnv(value)}
          >
            <Select.Option value={SystemEnv.SERVER_LOCAL}>Server Local</Select.Option>
            <Select.Option value={SystemEnv.AWS_BATCH}>AWS Batch</Select.Option>
          </Select>
        </div>

        <div style={{ marginTop: 5 }}>
          <div className={styles.maxInputContainer}>
            <label className={styles.inputLabel}>
              Max try count:
              <Popover content="Maximum number of attempts allowed.">
                <QuestionCircleOutlined style={{ marginLeft: 8 }} />
              </Popover>
            </label>
            <InputNumber
              placeholder="Max try count"
              min={1}
              max={10}
              value={visualizerMaxNode}
              onChange={setVisualizerMaxNode}
              className={styles.maxInput}
            />
          </div>
        </div>

        <div className={styles.buttonContainer}>
          <button
            className={styles.generateButton}
            onClick={() => launchVisualizer(beautifierInspectedNodeId)}
            disabled={!visualizerPrompt || isVisualizerStarting}
          >
            {isVisualizerStarting && <LoadingOutlined style={{ marginRight: '8px' }} />}
            <CustomImage
              name={customIconNames.AIICONSTARWHITE}
              style={{ height: '16px', marginRight: '8px', cursor: 'pointer' }}
            />
            {dictionary.BEAUTIFY}
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default BeautfierModal;
