// import * as customIconNames from '@/assets/customIconNames';
// import CustomImage from '@/components/common/customImage';
import { useEffect, useState } from 'react';
import {
  Modal,
  Input,
  Button,
  message,
  Upload,
  Select,
  Tag,
  Popover,
  InputNumber,
  Radio,
  Space,
  Form,
  Switch,
} from 'antd';
import { useModel } from 'umi';
import styles from './modals.less';
import { FlowTool } from '@/util/flowTool';
import { GenerationMode } from '@/constants/dynamicGeneration';
import { SystemEnv } from '@/constants/computation';
import {
  requestCreateDynamicGenerationPlan,
  requestDynamicGenerationPlanGet,
  requestCreateCustomPlan,
} from '@/request/node';
import { PlusOutlined, QuestionCircleOutlined, UploadOutlined } from '@ant-design/icons';
import { LLMModel, LLMModelList, ClaudeModel, ClaudeModelList } from '@/constants/ai';
import { requestTempUploadInfo } from '@/request/sss';
import { uploadFileToS3 } from '@/request/awsOperation';

// Mode constants
const MODE_PIPELINE = 'pipeline';
const MODE_NOTEBOOK = 'notebook';
const MODE_CLAUDE_CODE = 'claude_code';

const AutoGenieModal = () => {
  const {
    selectedBlocks,
    setSelectedBlocks,
    setIsSelectFbModalOpen,
    autoGenieInspectedNodeId,
    setAutoGenieInspectedNodeId,
    instance,
    currentSelectedNodes,
  } = useModel('analysis');
  const { setIsModalVisible, setSelectedPlan } = useModel('autoGenieProgress');
  const { functionBlockList } = useModel('functionBlock');
  const { dictionary } = useModel('localization');
  const [mode, setMode] = useState(MODE_PIPELINE);
  const [isPlanGenerating, setIsPlanGenerating] = useState(false);
  const [fileList, setFileList] = useState<any[]>([]);
  const [reqContent, setReqContent] = useState('');
  const [generationMode, setGenerationMode] = useState(GenerationMode.MIXED);
  const [systemEnv, setSystemEnv] = useState<string | null>(SystemEnv.SERVER_LOCAL);
  const [dynamicFbMaxNode, setDynamicFbMaxNode] = useState<string | number | null>('1');
  const [dynamicFbMaxBranch, setDynamicFbMaxBranch] = useState<string | number | null>('1');
  const [dynamicFbMaxTry, setdynamicFbMaxTry] = useState<string | number | null>('3');
  const [replanCountLimit, setReplanCountLimit] = useState<string | number | null>('2');
  const [nodeSourceName, setNodeSourceName] = useState('');
  const [llmModel, setLlmModel] = useState(LLMModel.GPT_4O_MINI);
  const [claudeModel, setClaudeModel] = useState(ClaudeModel.SONNET_4_5);
  const [maxIterations, setMaxIterations] = useState<number>(500);
  const [vcpu, setVcpu] = useState<number>(2);
  const [ram, setRam] = useState<number>(8);
  const [large, setLarge] = useState<boolean>(false);
  const [jobTimeout, setJobTimeout] = useState<number>(7200);
  const [isCustomPlanMode, setIsCustomPlanMode] = useState(false);
  const [customPlanName, setCustomPlanName] = useState('');
  const [customPlanSteps, setCustomPlanSteps] = useState('');
  const [isCustomPlanSaving, setIsCustomPlanSaving] = useState(false);
  const [computeType, setComputeType] = useState<string>('fargate');
  const [form] = Form.useForm();

  const COMPUTE_TYPE_OPTIONS = [
    {
      value: 'fargate',
      label: 'Fargate',
    },
    {
      value: 'ec2',
      label: 'EC2',
    },
  ];

  // Get available RAM options based on vCPU selection (AWS Fargate rules)
  const getRamOptions = (vcpuValue: number): number[] => {
    switch (vcpuValue) {
      case 0.25:
        return [0.5, 1, 2];
      case 0.5:
        return [1, 2, 3, 4];
      case 1:
        return [2, 3, 4, 5, 6, 7, 8];
      case 2:
        return Array.from({ length: 13 }, (_, i) => i + 4); // 4-16 GB
      case 4:
        return Array.from({ length: 23 }, (_, i) => i + 8); // 8-30 GB
      case 8:
        return Array.from({ length: 12 }, (_, i) => 16 + i * 4); // 16-60 GB (4 GB increments)
      case 16:
        return Array.from({ length: 12 }, (_, i) => 32 + i * 8); // 32-120 GB (8 GB increments)
      default:
        return [120];
    }
  };

  // Handle vCPU change and update RAM to a valid value
  const handleVcpuChange = (newVcpu: number) => {
    setVcpu(newVcpu);
    const availableRamOptions = getRamOptions(newVcpu);
    // If current RAM is not valid for new vCPU, set to the maximum available
    if (!availableRamOptions.includes(ram)) {
      setRam(availableRamOptions[availableRamOptions.length - 1]);
    }
  };

  useEffect(() => {
    if (autoGenieInspectedNodeId && instance) {
      const flowTool = new FlowTool(instance);
      const source = flowTool.checkNodeSource(autoGenieInspectedNodeId);
      setNodeSourceName(source || '');
    }
  }, [autoGenieInspectedNodeId, instance]);

  useEffect(() => {
    if (autoGenieInspectedNodeId) {
      form.resetFields();
      setMode(MODE_PIPELINE);
      setReqContent('');
      setGenerationMode(GenerationMode.MIXED);
      setSystemEnv(SystemEnv.SERVER_LOCAL);
      setDynamicFbMaxNode('1');
      setDynamicFbMaxBranch('1');
      setdynamicFbMaxTry('3');
      setReplanCountLimit('2');
      setLlmModel(LLMModel.GPT_4O_MINI);
      setClaudeModel(ClaudeModel.SONNET_4_5);
      setMaxIterations(100);
      setVcpu(2);
      setRam(8);
      setJobTimeout(7200);
      setFileList([]);
      setIsCustomPlanMode(false);
      setCustomPlanName('');
      setCustomPlanSteps('');
      setComputeType('fargate');
      setSelectedBlocks([]);
    }
  }, [autoGenieInspectedNodeId, form, setSelectedBlocks]);

  useEffect(() => {
    if (mode === MODE_CLAUDE_CODE) {
      setSystemEnv(SystemEnv.AWS_BATCH);
      setVcpu(4);
      setRam(16);
      setJobTimeout(computeType === 'ec2' ? 259200 : 129600);
      setMaxIterations(500);
    } else {
      setJobTimeout(7200);
    }
  }, [mode]);

  useEffect(() => {
    if (mode === MODE_CLAUDE_CODE) {
      if (computeType === 'ec2') {
        setJobTimeout(259200); // 3 days for EC2
      } else {
        setJobTimeout(86400); // 24 hours for Fargate
      }
    }
  }, [computeType, mode]);

  useEffect(() => {
    const handleOpenAutoGenie = () => {
      if (currentSelectedNodes.length === 0) {
        // No nodes selected
        message.info(
          'Please select a node first. Click on a node to select it, then try Auto Genie again.',
        );
      } else if (currentSelectedNodes.length === 1) {
        // Open modal with the selected node
        setAutoGenieInspectedNodeId(currentSelectedNodes[0].id);
      } else {
        // Multiple nodes selected
        message.info(
          'Please select only one node. Deselect the extra nodes by clicking on them, then try Auto Genie again.',
        );
      }
    };

    window.addEventListener('openAutoGenieModal', handleOpenAutoGenie);

    return () => {
      window.removeEventListener('openAutoGenieModal', handleOpenAutoGenie);
    };
  }, [currentSelectedNodes, setAutoGenieInspectedNodeId]);

  const handleCancel = () => {
    form.resetFields();
    setIsCustomPlanMode(false);
    setCustomPlanName('');
    setCustomPlanSteps('');
    setMode(MODE_PIPELINE);
    setAutoGenieInspectedNodeId(null);
  };

  const openProgressModalWithPlan = async (
    generationId: string,
    nodeId: string,
    totalStart?: number,
    timings?: Record<string, number>,
    generationMode?: string,
  ) => {
    const pollingStart = performance.now();
    try {
      let planData = null;
      const maxRetries = 5;
      const retryDelay = 5000;

      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          const response = await requestDynamicGenerationPlanGet(nodeId, generationId);

          if (response.code === 200 && response.data?.presigned_url) {
            const fetchStart = performance.now();
            const planResponse = await fetch(response.data.presigned_url);
            if (planResponse.ok) {
              planData = await planResponse.json();

              // Log timing data
              if (timings) {
                timings['F4_presignedFetch'] = performance.now() - fetchStart;
                timings['F3_polling'] = performance.now() - pollingStart;
                if (totalStart) {
                  timings['F1_total'] = performance.now() - totalStart;
                }
                console.log('[PlanGen Timing] Frontend stages:');
                Object.entries(timings)
                  .sort(([a], [b]) => a.localeCompare(b))
                  .forEach(([key, value]) => {
                    console.log(`  ${key}: ${value.toFixed(2)}ms`);
                  });
              }

              setSelectedPlan({
                generationId: generationId,
                nodeId: nodeId,
                status: 'generated',
                name: planData.name,
                steps: planData.steps,
                generationMode: generationMode,
              });
              setIsModalVisible(true);

              break;
            }
          }

          if (attempt < maxRetries) {
            await new Promise((resolve) => setTimeout(resolve, retryDelay));
          }
        } catch (error) {
          if (attempt < maxRetries) {
            await new Promise((resolve) => setTimeout(resolve, retryDelay));
          }
        }
      }

      if (!planData) {
        console.warn('Failed to fetch plan data');
        // Log timing data on failure
        if (timings) {
          timings['F3_polling'] = performance.now() - pollingStart;
          if (totalStart) {
            timings['F1_total'] = performance.now() - totalStart;
          }
          console.log('[PlanGen Timing] Frontend stages (plan fetch failed):');
          Object.entries(timings)
            .sort(([a], [b]) => a.localeCompare(b))
            .forEach(([key, value]) => {
              console.log(`  ${key}: ${value.toFixed(2)}ms`);
            });
        }
        setSelectedPlan({
          generationId: generationId,
          nodeId: nodeId,
          status: 'Generation Failed',
          generationMode: generationMode,
        });
      }
    } catch (error) {
      console.error('Error opening progress modal:', error);
      message.error('Failed to open progress modal');
    }
  };

  const planGeneration = async (nodeId) => {
    const timings: Record<string, number> = {};
    const totalStart = performance.now();

    try {
      setIsPlanGenerating(true);

      const computationResourceConfigure = {
        ram: ram,
        vcpu: vcpu,
        timeout: jobTimeout,
        large: large,
        gpu: 0,
        system_env: systemEnv,
        compute_type: mode === MODE_CLAUDE_CODE ? computeType : 'fargate',
      };

      let promiseObj: Promise<any> | null = null;
      if (mode === MODE_PIPELINE) {
        promiseObj = requestCreateDynamicGenerationPlan(
          nodeId,
          dynamicFbMaxNode,
          dynamicFbMaxBranch,
          dynamicFbMaxTry,
          reqContent,
          computationResourceConfigure,
          generationMode,
          llmModel,
          null,
          replanCountLimit,
          fileList.map((item) => item.uploadInfo),
        );
      } else if (mode === MODE_NOTEBOOK) {
        promiseObj = requestCreateDynamicGenerationPlan(
          nodeId,
          parseInt(dynamicFbMaxNode as string, 10),
          1,
          0,
          reqContent,
          computationResourceConfigure,
          'notebook',
          llmModel,
          'v3',
          null,
          fileList.map((item) => item.uploadInfo),
        );
      } else if (mode === MODE_CLAUDE_CODE) {
        promiseObj = requestCreateDynamicGenerationPlan(
          nodeId,
          parseInt(dynamicFbMaxNode as string, 10),
          1,
          0,
          reqContent,
          computationResourceConfigure,
          'claude_code',
          llmModel,
          null,
          null,
          claudeModel,
          maxIterations,
        );
      } else {
        throw new Error('Invalid mode selected');
      }

      // Log timing data for api request
      const apiStart = performance.now();
      const creationResponse = await promiseObj;
      timings['F2_apiRequest'] = performance.now() - apiStart;

      if (creationResponse.code !== 200) {
        message.error(
          `Failed to create dynamic FB plan: ${
            creationResponse.message || 'Please try again later.'
          }`,
        );
        // Log timing data on failure
        timings['F1_total'] = performance.now() - totalStart;
        console.log('[PlanGen Timing] Frontend stages (API error):');
        Object.entries(timings)
          .sort(([a], [b]) => a.localeCompare(b))
          .forEach(([key, value]) => {
            console.log(`  ${key}: ${value.toFixed(2)}ms`);
          });
        return;
      }

      message.success('Plan generation was created successfully');

      setAutoGenieInspectedNodeId(null);
      setReqContent('');
      form.resetFields(['reqContent']);

      const generationId =
        creationResponse.data?.generationId || creationResponse.data?.generation_id;
      if (generationId) {
        const currentGenerationMode =
          mode === MODE_CLAUDE_CODE
            ? 'claude_code'
            : mode === MODE_NOTEBOOK
            ? 'notebook'
            : generationMode;
        setTimeout(() => {
          openProgressModalWithPlan(
            generationId,
            nodeId,
            totalStart,
            timings,
            currentGenerationMode,
          );
        }, 100);
      } else {
        console.warn('No generation ID found in response:', creationResponse);
      }
    } catch (error: any) {
      console.error('Error generating plan:', error);
      // Log timing data on exception
      timings['F1_total'] = performance.now() - totalStart;
      console.log('[PlanGen Timing] Frontend stages (exception):');
      Object.entries(timings)
        .sort(([a], [b]) => a.localeCompare(b))
        .forEach(([key, value]) => {
          console.log(`  ${key}: ${value.toFixed(2)}ms`);
        });
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
      setIsPlanGenerating(false);
      handleCancel();
    }
  };

  const saveCustomPlan = async () => {
    if (!autoGenieInspectedNodeId) {
      message.error('No node selected');
      return;
    }

    setIsCustomPlanSaving(true);
    try {
      const computationResourceConfigure = {
        ram: ram,
        vcpu: vcpu,
        timeout: jobTimeout,
        large: large,
        gpu: 0,
        system_env: systemEnv,
        compute_type: mode === MODE_CLAUDE_CODE ? computeType : 'fargate',
      };

      const response = await requestCreateCustomPlan(
        autoGenieInspectedNodeId,
        mode === MODE_NOTEBOOK || mode === MODE_CLAUDE_CODE
          ? parseInt(dynamicFbMaxNode as string, 10)
          : dynamicFbMaxNode,
        mode === MODE_NOTEBOOK || mode === MODE_CLAUDE_CODE ? 1 : dynamicFbMaxBranch,
        mode === MODE_NOTEBOOK || mode === MODE_CLAUDE_CODE ? 0 : dynamicFbMaxTry,
        reqContent,
        computationResourceConfigure,
        mode === MODE_NOTEBOOK
          ? 'notebook'
          : mode === MODE_CLAUDE_CODE
          ? 'claude_code'
          : generationMode,
        llmModel,
        mode === MODE_NOTEBOOK ? 'v3' : null,
        mode === MODE_NOTEBOOK || mode === MODE_CLAUDE_CODE ? null : replanCountLimit,
        customPlanName,
        customPlanSteps,
        mode === MODE_CLAUDE_CODE ? claudeModel : undefined,
        mode === MODE_CLAUDE_CODE ? maxIterations : undefined,
      );

      if (response.code === 200) {
        message.success('Custom plan created successfully');
        setIsCustomPlanMode(false);
        setCustomPlanName('');
        setCustomPlanSteps('');

        const generationId = response.data?.generation_id;
        if (generationId) {
          setSelectedPlan({
            generationId,
            nodeId: autoGenieInspectedNodeId,
            status: 'generated',
            name: customPlanName,
            steps: customPlanSteps,
            generationMode:
              mode === MODE_CLAUDE_CODE
                ? 'claude_code'
                : mode === MODE_NOTEBOOK
                ? 'notebook'
                : generationMode,
          });
          setIsModalVisible(true);
        }
        setAutoGenieInspectedNodeId(null);
      } else {
        message.error(response.message || 'Failed to create custom plan');
      }
    } catch (error: any) {
      console.error('Error creating custom plan:', error);
      message.error('Failed to create custom plan');
    } finally {
      setIsCustomPlanSaving(false);
    }
  };

  const handleFileChange = async ({ fileList: newFileList }) => {
    // Find newly added files
    const newFiles = newFileList.filter((file) => !fileList.find((f) => f.uid === file.uid));

    // Update the displayed file list first
    setFileList(newFileList);

    if (newFiles.length > 0) {
      // Process newly uploaded files
      for (const file of newFiles) {
        if (file.originFileObj && !file.url) {
          try {
            // Set file status to uploading
            file.status = 'uploading';
            setFileList([...newFileList]);

            // 1. Call requestTempUploadInfo to get upload info
            const { data: uploadInfo } = await requestTempUploadInfo(file.name, file.size);

            // 2. Call uploadFileToS3 to upload the file
            await uploadFileToS3(file.originFileObj, uploadInfo, (progress) => {
              file.percent = progress;
              setFileList([...newFileList]);
            });

            // Upload succeeded; save the upload info
            file.status = 'done';
            file.uploadInfo = uploadInfo;
            file.url = uploadInfo.presigned_url || uploadInfo.object_key;
            setFileList([...newFileList]);

            message.success(`${file.name} uploaded successfully`);
          } catch (error: any) {
            console.error('File upload error:', error);
            file.status = 'error';
            file.response = error.message || 'Upload failed';
            setFileList([...newFileList]);
            message.error(`${file.name} upload failed`);
          }
        }
      }
    }
  };

  // Delete a file
  const handleRemove = (file) => {
    const newFileList = fileList.filter((item) => item.uid !== file.uid);
    setFileList(newFileList);
    message.success(`${file.name} removed`);
    return true;
  };

  const getBlockName = (blockId: number) => {
    for (const group of functionBlockList) {
      const block = group.functionBlockList.find((b) => b.id === blockId);
      if (block) {
        return block.name;
      }
    }
    return '';
  };

  const handleTagDelete = (blockId: number) => {
    setSelectedBlocks((prev) => prev.filter((id) => id !== blockId));
  };

  const renderSelectedBlocksTags = () => {
    return selectedBlocks.map((blockId) => (
      <Tag
        key={blockId}
        closable
        onClose={() => handleTagDelete(blockId)}
        style={{ margin: '2px 4px', padding: '2px 8px' }}
      >
        {getBlockName(blockId)}
      </Tag>
    ));
  };

  return (
    <Modal
      title={<div style={{ textAlign: 'center', width: '100%' }}> {dictionary.AUTO_GENIE} </div>}
      visible={!!autoGenieInspectedNodeId}
      confirmLoading={isPlanGenerating}
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
      <Form form={form} layout="vertical" className={styles.modalContent} scrollToFirstError>
        <div>
          <div className={styles.modalHeader}>
            <span className={styles.labelRequired}>*</span> Select Mode:
          </div>
          <Radio.Group
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            style={{ width: '100%' }}
          >
            <Radio.Button value={MODE_PIPELINE} style={{ width: '33.33%', textAlign: 'center' }}>
              Pipeline Mode
            </Radio.Button>
            <Radio.Button value={MODE_NOTEBOOK} style={{ width: '33.33%', textAlign: 'center' }}>
              Notebook Mode
            </Radio.Button>
            <Radio.Button value={MODE_CLAUDE_CODE} style={{ width: '33.33%', textAlign: 'center' }}>
              Agent Mode
            </Radio.Button>
          </Radio.Group>
        </div>

        <div>
          <div className={styles.modalHeader}>
            <span className={styles.labelRequired}>*</span> Selected Data Source:
          </div>
          <Input value={nodeSourceName} className={styles.preFilledInput} readOnly />
        </div>

        <div>
          <div className={styles.modalHeader}>
            <span className={styles.labelRequired}>*</span> Select LLM Model:
          </div>
          <Select
            defaultValue={LLMModel.GPT_4O_MINI}
            value={llmModel}
            style={{ width: '100%' }}
            onChange={(value) => {
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

        {mode === MODE_CLAUDE_CODE && (
          <div>
            <div className={styles.modalHeader}>
              <span className={styles.labelRequired}>*</span> Select Model (for execution):
            </div>
            <Select
              defaultValue={ClaudeModel.SONNET_4_5}
              value={claudeModel}
              style={{ width: '100%' }}
              onChange={(value) => {
                setClaudeModel(value);
              }}
            >
              {ClaudeModelList.map((modelOption) => {
                return (
                  <Select.Option key={modelOption.id} value={modelOption.value}>
                    {modelOption.label}
                  </Select.Option>
                );
              })}
            </Select>
          </div>
        )}

        {mode === MODE_CLAUDE_CODE && (
          <div className={styles.maxInputContainer}>
            <label className={styles.inputLabel}>
              Max iterations:
              <Popover content="Maximum number of turns the agent can take to complete the task.">
                <QuestionCircleOutlined style={{ marginLeft: 8 }} />
              </Popover>
            </label>
            <InputNumber
              placeholder="Max iterations"
              min={10}
              max={500}
              value={maxIterations}
              onChange={(value) => setMaxIterations(value || 100)}
              className={styles.maxInput}
            />
          </div>
        )}

        <Form.Item
          name="reqContent"
          label={<span> What do you want to achieve by analysis?</span>}
          rules={[{ required: true, message: 'Please describe what you want to achieve' }]}
        >
          <Input.TextArea
            placeholder="e.g. I want to get a graph ..."
            autoSize={{ minRows: 4, maxRows: 10 }}
            onChange={(e) => setReqContent(e.target.value)}
          />
        </Form.Item>

        {mode === MODE_PIPELINE && (
          <div>
            <div className={styles.modalHeader}>Any files you want to include?</div>
            <div className="file-upload-container">
              {/* File upload area */}
              <Upload
                fileList={fileList}
                showUploadList={{
                  showDownloadIcon: false,
                  showRemoveIcon: true,
                  showPreviewIcon: false,
                }}
                onChange={handleFileChange}
                onRemove={handleRemove}
                beforeUpload={() => false} // Prevent the default upload behaviour
                multiple // Allow selecting multiple files
                accept=".txt,.csv,.json,.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif" // Restrict file types
              >
                <Button icon={<UploadOutlined />}>Select Files</Button>
              </Upload>
            </div>
          </div>
        )}

        {/* Only show in pipeline mode */}
        {mode === MODE_PIPELINE && (
          <div>
            <div className={styles.modalHeader}>Any particular steps you want to include?</div>
            <Select
              value={generationMode}
              style={{ width: '100%' }}
              onChange={(value) => setGenerationMode(value)}
            >
              <Select.Option value={GenerationMode.MIXED}>Mixed</Select.Option>
              <Select.Option value={GenerationMode.ONLY_NEW}>Only New</Select.Option>
              <Select.Option value={GenerationMode.ONLY_EXISTING}>Only Existing</Select.Option>
            </Select>
          </div>
        )}

        {/* Only show in pipeline mode */}
        {mode === MODE_PIPELINE && (
          <div>
            <div
              className={styles.modalHeader}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <span>Any particular steps you want to include by AI analysis?</span>
              <Button
                type="default"
                size="small"
                onClick={() => {
                  setIsSelectFbModalOpen(true);
                }}
              >
                <span>
                  <PlusOutlined /> Add Function Block
                </span>
              </Button>
            </div>
            <div
              style={{
                border: '1px solid #d9d9d9',
                borderRadius: '2px',
                padding: '4px',
                minHeight: '70px',
              }}
            >
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {renderSelectedBlocksTags()}
              </div>
              {selectedBlocks.length === 0 ? (
                <Input.TextArea
                  placeholder="e.g. xx specific sample ..."
                  autoSize={{ minRows: 2, maxRows: 8 }}
                  style={{ border: 'none' }}
                />
              ) : null}
            </div>
          </div>
        )}

        <div>
          <div className={styles.modalHeader}>Where do you want to run the computations?</div>
          <Select
            value={systemEnv}
            style={{ width: '100%' }}
            onChange={(value) => setSystemEnv(value)}
          >
            <Select.Option value={SystemEnv.SERVER_LOCAL} disabled={mode === MODE_CLAUDE_CODE}>
              Server Local
            </Select.Option>
            <Select.Option value={SystemEnv.AWS_BATCH}>Cloud Compute</Select.Option>
          </Select>
        </div>

        {systemEnv === SystemEnv.AWS_BATCH && (
          <div>
            <div className={styles.modalHeader}>
              Computation Resources:
              <Popover content="Configure vCPU, RAM, and timeout for the computation task based on AWS Fargate specifications.">
                <QuestionCircleOutlined style={{ marginLeft: 8 }} />
              </Popover>
            </div>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
              {mode === MODE_CLAUDE_CODE && (
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>
                    Compute Type:
                  </label>
                  <Select
                    value={computeType}
                    style={{ width: '100%' }}
                    onChange={(value) => setComputeType(value)}
                  >
                    {COMPUTE_TYPE_OPTIONS.map((option) => (
                      <Select.Option key={option.value} value={option.value}>
                        {option.label}
                      </Select.Option>
                    ))}
                  </Select>
                </div>
              )}
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>
                  vCPU:
                </label>
                <Select value={vcpu} style={{ width: '100%' }} onChange={handleVcpuChange}>
                  <Select.Option value={0.25}>0.25 vCPU</Select.Option>
                  <Select.Option value={0.5}>0.5 vCPU</Select.Option>
                  <Select.Option value={1}>1 vCPU</Select.Option>
                  <Select.Option value={2}>2 vCPU</Select.Option>
                  <Select.Option value={4}>4 vCPU</Select.Option>
                  <Select.Option value={8}>8 vCPU</Select.Option>
                  <Select.Option value={16}>16 vCPU</Select.Option>
                </Select>
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>
                  RAM (GB):
                </label>
                <Select value={ram} style={{ width: '100%' }} onChange={(value) => setRam(value)}>
                  {getRamOptions(vcpu).map((ramOption) => (
                    <Select.Option key={ramOption} value={ramOption}>
                      {ramOption} GB
                    </Select.Option>
                  ))}
                </Select>
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>
                  Large Task:
                </label>
                <Switch checked={large} onChange={setLarge} />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>
                  Timeout (s):
                </label>
                <InputNumber
                  value={jobTimeout}
                  min={300}
                  max={604800}
                  step={1}
                  style={{ width: '100%' }}
                  onChange={(value) => setJobTimeout(value || 300)}
                />
              </div>
            </div>
          </div>
        )}

        <div style={{ marginTop: 5 }}>
          {mode !== MODE_CLAUDE_CODE && (
            <div className={styles.maxInputContainer}>
              <label className={styles.inputLabel}>
                Max {mode === MODE_PIPELINE ? 'nodes' : 'cells'}:
                <Popover content="Maximum number of nodes to be analyzed. A lower value will limit the number of steps generated in the plan.">
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Popover>
              </label>
              <InputNumber
                placeholder={`Max ${mode === MODE_PIPELINE ? 'nodes' : 'cells'}`}
                min={1}
                max={1000}
                value={dynamicFbMaxNode}
                onChange={setDynamicFbMaxNode}
                className={styles.maxInput}
              />
            </div>
          )}
          {mode === MODE_PIPELINE && (
            <div className={styles.maxInputContainer}>
              <label className={styles.inputLabel}>
                Max branching:
                <Popover content="Maximum number of branches that can be generated from the current node. A lower value will reduce the number of steps generated in plan.">
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Popover>
              </label>
              <InputNumber
                placeholder="Max branch"
                min={1}
                max={1000}
                value={dynamicFbMaxBranch}
                onChange={setDynamicFbMaxBranch}
                className={styles.maxInput}
              />
            </div>
          )}

          {mode === MODE_PIPELINE && (
            <div className={styles.maxInputContainer}>
              <label className={styles.inputLabel}>
                Max debug:
                <Popover content="Maximum number of attempts allowed.">
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Popover>
              </label>
              <InputNumber
                placeholder="Max debug"
                min={1}
                max={1000}
                value={dynamicFbMaxTry}
                onChange={setdynamicFbMaxTry}
                className={styles.maxInput}
              />
            </div>
          )}

          {mode === MODE_PIPELINE && (
            <div className={styles.maxInputContainer}>
              <label className={styles.inputLabel}>
                Max replan:
                <Popover content="Maximum number of replanning attempts allowed.">
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Popover>
              </label>
              <InputNumber
                placeholder="Max replan"
                min={1}
                max={1000}
                value={replanCountLimit}
                onChange={setReplanCountLimit}
                className={styles.maxInput}
              />
            </div>
          )}
        </div>

        {/* Custom Plan Form */}
        {isCustomPlanMode && (
          <div style={{ width: '100%' }}>
            <Form.Item
              name="customPlanName"
              label="Plan Name"
              rules={[{ required: true, message: 'Please enter a plan name' }]}
              style={{ marginBottom: 10 }}
            >
              <Input
                placeholder="Enter plan name"
                onChange={(e) => setCustomPlanName(e.target.value)}
              />
            </Form.Item>
            <Form.Item
              name="customPlanSteps"
              label="Plan Steps (markdown checklist format)"
              rules={[{ required: true, message: 'Please enter plan steps' }]}
              style={{ marginBottom: 10 }}
            >
              <Input.TextArea
                placeholder={`Enter your plan steps in markdown format:\n- [ ] Step 1: Load and preprocess data\n- [ ] Step 2: Quality control\n- [ ] Step 3: Run analysis`}
                rows={6}
                onChange={(e) => setCustomPlanSteps(e.target.value)}
              />
            </Form.Item>
          </div>
        )}

        <div className={styles.buttonContainer}>
          {!isCustomPlanMode ? (
            <Space>
              <Button
                type="primary"
                onClick={() => {
                  form
                    .validateFields(['reqContent'])
                    .then(() => {
                      planGeneration(autoGenieInspectedNodeId);
                    })
                    .catch(() => {
                      form.scrollToField('reqContent', { behavior: 'smooth', block: 'center' });
                    });
                }}
                disabled={isPlanGenerating || isCustomPlanSaving}
                loading={isPlanGenerating}
              >
                Plan
              </Button>
              <Button
                onClick={() => setIsCustomPlanMode(true)}
                disabled={isPlanGenerating || isCustomPlanSaving}
              >
                Custom Plan
              </Button>
            </Space>
          ) : (
            <Space>
              <Button
                onClick={() => {
                  setIsCustomPlanMode(false);
                  setCustomPlanName('');
                  setCustomPlanSteps('');
                  form.resetFields(['customPlanName', 'customPlanSteps']);
                }}
              >
                Cancel
              </Button>
              <Button
                type="primary"
                onClick={() => {
                  form
                    .validateFields(['customPlanName', 'customPlanSteps'])
                    .then(() => {
                      saveCustomPlan();
                    })
                    .catch((errorInfo) => {
                      const firstErrorField = errorInfo.errorFields?.[0]?.name?.[0];
                      if (firstErrorField) {
                        form.scrollToField(firstErrorField, {
                          behavior: 'smooth',
                          block: 'center',
                        });
                      }
                    });
                }}
                loading={isCustomPlanSaving}
                disabled={isCustomPlanSaving}
              >
                Save Plan
              </Button>
            </Space>
          )}
        </div>
      </Form>
    </Modal>
  );
};

export default AutoGenieModal;
