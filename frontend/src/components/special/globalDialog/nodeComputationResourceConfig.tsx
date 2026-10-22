import { useEffect, useState, useRef } from 'react';
import { Modal, Form, Select, Alert, InputNumber, Switch } from 'antd';
import { useModel } from 'umi';
import {
  DefaultComputationResourceConfig,
  Vcpu2MemoryOptions,
} from '@/constants/computationResource';
import { requestEditComputationResourceConfig } from '@/request/node';

const vcpuOptions = Object.keys(Vcpu2MemoryOptions).map((vcpuOption: string) =>
  parseFloat(vcpuOption),
);

const NodeComputationResourceConfig = () => {
  const {
    computationResourceChangingNodeId,
    setComputationResourceChangingNodeId,
    computationResourceChangingInfo,
    setComputationResourceChangingInfo,
    isViewOnlyMode,
    setIsViewOnlyMode,
  } = useModel('analysis');

  const formContainerRef = useRef<HTMLDivElement>(null);
  const [form] = Form.useForm();
  const [memoryOptions, setMemoryOptions] = useState<number[]>([]);
  const [isOnLocal, setIsOnLocal] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const updateMemoryOptions = (vcpu: number) => {
    if (vcpu) {
      setMemoryOptions(Vcpu2MemoryOptions[vcpu]);
    } else {
      setMemoryOptions([]);
    }
  };

  useEffect(() => {
    if (computationResourceChangingNodeId) {
      if (computationResourceChangingInfo) {
        form.setFieldsValue(computationResourceChangingInfo);
        updateMemoryOptions(computationResourceChangingInfo.vcpu);
        setIsOnLocal(computationResourceChangingInfo.systemEnv === 'server-local');
      }
    } else {
      form.resetFields();
      setMemoryOptions([]);
      setIsOnLocal(false);
    }
  }, [computationResourceChangingNodeId, computationResourceChangingInfo]);

  const handleModalClose = () => {
    setComputationResourceChangingNodeId(null);
    setComputationResourceChangingInfo(DefaultComputationResourceConfig);
    setIsViewOnlyMode(false);
    form.resetFields();
  };

  const confirmSave = async () => {
    if (!computationResourceChangingNodeId || isViewOnlyMode) {
      handleModalClose();
      return;
    }
    try {
      setIsSaving(true);
      const values = await form.validateFields();
      const systemEnv = values.systemEnv;
      delete values.systemEnv;
      await requestEditComputationResourceConfig(
        computationResourceChangingNodeId,
        values,
        systemEnv,
      );
      setComputationResourceChangingInfo(values);
      handleModalClose();
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      centered
      title={
        isViewOnlyMode ? 'Computation Resource Information' : 'Node Computation Resource Config'
      }
      visible={!!computationResourceChangingNodeId}
      okText={isViewOnlyMode ? 'Close' : 'Save'}
      confirmLoading={isSaving}
      onOk={confirmSave}
      onCancel={handleModalClose}
      okButtonProps={{ loading: isSaving }}
      width={580}
      cancelButtonProps={{ style: { display: isViewOnlyMode ? 'none' : 'inline-block' } }}
    >
      <div style={{ marginBottom: 16 }}>
        <Alert
          message="The average runtime metrics are derived from the computation resource configuration and are automatically refreshed every 4 hours."
          type="info"
          showIcon
          closable={false}
        />
      </div>
      <div ref={formContainerRef}>
        <Form
          labelAlign="right"
          labelCol={{ span: 4 }}
          wrapperCol={{ span: 20 }}
          autoComplete="off"
          form={form}
          disabled={isViewOnlyMode}
          onFieldsChange={(changedFields) => {
            const changedField = changedFields[0];
            if (changedField?.name[0] === 'systemEnv') {
              setIsOnLocal(changedField.value === 'server-local');
            } else if (changedField?.name[0] === 'vcpu') {
              updateMemoryOptions(changedField.value);
            }
          }}
        >
          <Form.Item label="job env" key="job env" required name="systemEnv">
            <Select placeholder="AWS Batch">
              <Select.Option key="server-local" value="server-local">
                Server Local
              </Select.Option>
              <Select.Option key="aws-batch" value="aws-batch">
                AWS Batch
              </Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="vcpu" key="vcpu" required name="vcpu">
            <Select disabled={isOnLocal || isViewOnlyMode}>
              {vcpuOptions.map((vcpuOption: number) => (
                <Select.Option key={vcpuOption} value={vcpuOption}>
                  {vcpuOption}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            label="memory"
            key="memory"
            required
            name="ram"
            dependencies={['vcpu']}
            rules={[
              ({ getFieldValue }) => ({
                validator(_: any, value: number) {
                  const currentVcpuValue = getFieldValue('vcpu');
                  if (!Vcpu2MemoryOptions[currentVcpuValue]?.includes(value)) {
                    return Promise.reject('memory is not valid');
                  }
                  return Promise.resolve();
                },
              }),
            ]}
          >
            <Select disabled={isOnLocal || isViewOnlyMode}>
              {memoryOptions.map((memoryOption: number) => (
                <Select.Option key={memoryOption} value={memoryOption}>
                  {memoryOption}G
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="timeout" key="timeout" required name="timeout">
            <InputNumber
              min={0}
              placeholder="Timeout(s)"
              style={{ width: '100%' }}
              disabled={isOnLocal || isViewOnlyMode}
            />
          </Form.Item>
          <Form.Item label="large" key="large" name="large" valuePropName="checked">
            <Switch disabled={isOnLocal || isViewOnlyMode} />
          </Form.Item>
          {/* <Form.Item label="gpt" key="gpt" required name="gpt">
          <Input />
        </Form.Item> */}
        </Form>
      </div>
      {/* Form with node performance settings (vcpu, memory, timeout, gpt); the memory options change with the selected vcpu */}
    </Modal>
  );
};

export default NodeComputationResourceConfig;
