import * as customIconNames from '@/assets/customIconNames';
import { AnalysisType } from '@/constants/analysis';
import { NodeType } from '@/constants/node';
import { requestGetDataStructure } from '@/request/attachedData';
import { requestComputationTrail, requestLatestComputation } from '@/request/computation';
import { requestGetFBInformation } from '@/request/functionBlock';
import {
  requestEditNodeParams,
  requestFillParams,
  requestNodeParams,
  requestRestore,
} from '@/request/node';
import { FlowTool } from '@/util/flowTool';
import { WarningOutlined } from '@ant-design/icons';
import { Button, Dropdown, Form, message, Modal, Result, Spin } from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';

import CustomImage from '@/components/common/customImage';
import FBParameterForm from '@/components/highReuse/fBParameterForm';

import Markdown from 'react-markdown';

const UpdateParameterModal = ({
  style,
  runNode,
  instance,
  onClose,
  paramEditedNodeId,
  paramEditedFbId,
  openPreviousParameter,
}) => {
  const { dictionary } = useModel('localization');
  const { setSelectedNodeId } = useModel('aiUI');
  const { analysisAccessType } = useModel('analysis');

  const [editConfirm, setEditConfirm] = useState(false);
  const [resettingConfirm, setResettingConfirm] = useState(false);
  const [resettingToOriginalConfirm, setResettingToOriginalConfirm] = useState(false);
  const [editAndRunConfirm, setEditAndRunConfirm] = useState(false);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [dataStructure, setDataStructure] = useState({});
  const [error, setError] = useState(null as null | string);
  const [paramsList, setParamsList] = useState([]);
  const [aiParameterLoading, setAiParameterLoading] = useState(false);
  const [locked, setLocked] = useState(false);

  // const [fillingReasonDict, setFillingReasonDict] = useState({});
  const [fillingReason, setFillingReason] = useState<string | null>('');
  const [fillingReasonVisible, setFillingReasonVisible] = useState(false);

  const [recommendedParamDict, setRecommendedParamDict] = useState<any>({});

  const loadFormLoadInfo = async () => {
    setError(null);
    setLoading(true);
    try {
      if (paramEditedNodeId && paramEditedFbId) {
        const [{ data: paramsValueDict }, { data: information }] = await Promise.all([
          requestNodeParams(paramEditedNodeId),
          requestGetFBInformation(paramEditedFbId),
        ]);
        const flattenParamsValueDict = paramsValueDict;
        setParamsList(information.currentVersionInformation.args);
        form.setFieldsValue(flattenParamsValueDict);
      }
    } catch (e: any) {
      setError(e);
    } finally {
      setLoading(false);
    }
  };
  const { setDataId } = useModel('cellSelect');

  const loadList = async () => {
    try {
      const flowTool = new FlowTool(instance);
      const currentNode = flowTool.getNode(paramEditedNodeId);
      if (currentNode.type === NodeType.COMPUTATION_NODE_V2) {
        return;
      }
      const result = flowTool.checkPreDataNode(paramEditedNodeId);
      const node = flowTool.getNode(result);
      if (node.type in [NodeType.DATA_NODE, NodeType.DATA_NODE_V2]) {
        const dataStructure = await requestGetDataStructure(node.data.dataId);
        setDataId(node.data.dataId);
        setDataStructure(dataStructure);
        return dataStructure;
      } else if (node.type === NodeType.COMPUTATION_NODE) {
        const { data: latestComputation } = await requestLatestComputation(result);
        const dataStructure = await requestGetDataStructure(latestComputation.resultDataId);
        setDataId(latestComputation.resultDataId);
        setDataStructure(dataStructure);
        return dataStructure;
      }
    } catch (e: any) {
      message.error(e.message);
      setDataStructure({});
      // setCellDataStructure(null);
    }
  };

  const editParameters = async () => {
    try {
      // const values = form.getFieldsValue();
      const values = await form.validateFields();
      const valueKeys = Object.keys(values);
      for (const key of valueKeys) {
        if (values[key] === 'None' || JSON.stringify(values[key]) === '["None"]') {
          values[key] = null;
        } else if (values[key] === undefined) {
          values[key] = null;
        } else if (key.indexOf('#.?_') !== -1) {
          const [outKey, innerkey] = key.split('#.?_');
          if (values[outKey] !== undefined) {
            values[outKey][innerkey] = values[key];
          } else {
            values[outKey] = {
              [innerkey]: values[key],
            };
          }
          delete values[key];
        }
      }

      if (paramEditedNodeId) {
        await requestEditNodeParams(paramEditedNodeId, values);
      }
      message.success('Update parameters successfully!');
    } catch (e) {
      message.error('Update parameters failed!');
    }
  };

  const editParametersAndRun = async () => {
    if (paramEditedNodeId) {
      try {
        const values = await form.validateFields();
        const valueKeys = Object.keys(values);
        for (const key of valueKeys) {
          if (values[key] === 'None' || JSON.stringify(values[key]) === '["None"]') {
            values[key] = null;
          }
          if (key.indexOf('#.?_') !== -1) {
            const [outKey, innerkey] = key.split('#.?_');
            if (values[outKey] !== undefined) {
              values[outKey][innerkey] = values[key];
            } else {
              values[outKey] = {
                [innerkey]: values[key],
              };
            }
            delete values[key];
          }
        }

        if (paramEditedNodeId) {
          await requestEditNodeParams(paramEditedNodeId, values);
        }
        runNode(paramEditedNodeId, instance);
        message.success('Update parameters and running successfully!');
      } catch {
        message.error('Update parameters failed!');
      }
    }
  };

  const updateParameter = () => {
    setEditConfirm(true);
  };

  const resetParameter = () => {
    setResettingConfirm(true);
  };

  const resetToOriginal = () => {
    setResettingToOriginalConfirm(true);
  };

  useEffect(() => {
    if (!!paramEditedNodeId) {
      setDataId(null);
      loadList();
      loadFormLoadInfo();
      setSelectedNodeId(paramEditedNodeId);
    }
  }, [paramEditedNodeId]);

  useEffect(() => {
    if (!!paramEditedNodeId) {
      const flowTool = new FlowTool(instance);
      const resultSub = flowTool.getNode(paramEditedNodeId);
      if (resultSub) {
        setLocked(resultSub.data.locked);
      } else {
        setLocked(false);
      }
    }
  }, [paramEditedNodeId, instance]);

  const fillParamsByAI = async (paramsDict: any, computationTrail: any) => {
    const { data: fillResult, message: fillingReason } = await requestFillParams(
      paramEditedNodeId,
      paramsDict,
      computationTrail,
    );
    try {
      const filledValues = JSON.parse(fillResult.extracted_result);
      return {
        newValues: filledValues,
        fillingReason,
      };
    } catch (e) {
      throw new Error('Format error');
    }
  };

  const fillByAI = async (key: string) => {
    if (!paramEditedNodeId) return;
    try {
      setAiParameterLoading(true);
      const { data: computationTrail } = await requestComputationTrail(paramEditedNodeId);
      const paramsValueDict = await form.getFieldsValue();
      let paramNameList = paramsList.map((param) => param.name);
      if (key === 'fill-unfinished') {
        paramNameList = paramNameList.filter(
          (param) =>
            !paramsValueDict[param] ||
            paramsValueDict[param] === 'None' ||
            (Array.isArray(paramsValueDict[param]) && paramsValueDict[param].length === 0),
        );
      }
      const paramsDict: any = {};
      for (const param of paramNameList) {
        paramsDict[param] = paramsValueDict[param];
      }
      const { newValues, fillingReason } = await fillParamsByAI(paramsDict, computationTrail);
      const oldValues = {};
      for (const key in newValues) {
        oldValues[key] = paramsValueDict[key];
      }
      const newParamsValueDict = { ...paramsValueDict, ...newValues };
      form.setFieldsValue(newParamsValueDict);
      // setFillingReasonDict(fillingReasonDict);
      setFillingReason(fillingReason);
      setRecommendedParamDict(newValues);
      openPreviousParameter(oldValues);
      setFillingReasonVisible(true);
      message.success('AI parameter success');
    } catch (e: any) {
      message.error('AI parameter failed: ' + e.message || 'Unknown error');
    } finally {
      setAiParameterLoading(false);
    }
  };

  useEffect(() => {
    setFillingReason(null);
  }, [paramEditedNodeId]);

  return (
    <div
      onKeyDown={(e) => {
        e.stopPropagation();
      }}
      onKeyUp={(e: any) => {
        e.stopPropagation();
      }}
    >
      <Modal
        style={style || {}}
        centered
        destroyOnClose
        title={dictionary.UPDATE_PARAMETER}
        open={!!paramEditedNodeId}
        onOk={editParameters}
        onCancel={onClose}
        bodyStyle={{
          height: '60vh',
          overflowY: 'auto',
        }}
        maskClosable={false} // Do not close the modal when the mask is clicked
        width="50vw"
        keyboard={false}
        // mask={false}
        zIndex={99}
        footer={[
          <>
            {aiParameterLoading ? (
              <Button type="link" loading>
                Running AI Parameter
              </Button>
            ) : (
              <Dropdown
                key="ai parameter"
                disabled={locked || analysisAccessType === AnalysisType.PUBLIC}
                menu={{
                  items: [
                    {
                      label: 'Fill in all the parameters',
                      key: 'fill-all',
                    },
                    {
                      label: 'Complete unfinished parameters',
                      key: 'fill-unfinished',
                    },
                    {
                      label: 'Show parameter update history',
                      key: 'show-history',
                    },
                  ],
                  onClick: (selectedItem: any) => {
                    const { key } = selectedItem;
                    if (key === 'fill-all' || key === 'fill-unfinished') {
                      fillByAI(key);
                    } else if (key === 'show-history') {
                      openPreviousParameter();
                    }
                  },
                }}
              >
                <button
                  style={{
                    border: 'none',
                    background: 'white',
                    marginRight: '5px',
                  }}
                  disabled={locked || analysisAccessType === AnalysisType.PUBLIC}
                >
                  <CustomImage
                    name={customIconNames.AIICONSTAR}
                    style={{
                      height: '18px',
                      marginRight: '4px',
                      marginBottom: '3px',
                      cursor:
                        locked || analysisAccessType === AnalysisType.PUBLIC
                          ? 'not-allowed'
                          : 'pointer',
                    }}
                  />
                  <span
                    className="gradient-text"
                    style={{
                      cursor:
                        locked || analysisAccessType === AnalysisType.PUBLIC
                          ? 'not-allowed'
                          : 'pointer',
                    }}
                  >
                    AI Parameter
                  </span>
                </button>
              </Dropdown>
            )}
          </>,
          <>
            {fillingReason && (
              <Button
                key="fillingReason"
                onClick={() => {
                  setFillingReasonVisible(true);
                }}
              >
                {dictionary.FILLING_REASON}
              </Button>
            )}
          </>,
          <Button
            disabled={locked || analysisAccessType === AnalysisType.PUBLIC}
            key="resetToOriginal"
            onClick={(e) => {
              e.stopPropagation();
              resetToOriginal();
            }}
          >
            {dictionary.SET_DEFAULT}
          </Button>,
          <Button
            key="reset"
            disabled={locked || analysisAccessType === AnalysisType.PUBLIC}
            onClick={(e) => {
              e.stopPropagation();
              resetParameter();
            }}
          >
            {dictionary.RESET}
          </Button>,
          <Button key="cancel" onClick={onClose}>
            {dictionary.CANCEL}
          </Button>,
          <Button
            key="Update and Run"
            type="primary"
            disabled={locked || analysisAccessType === AnalysisType.PUBLIC}
            onClick={async (e) => {
              e.stopPropagation();
              await form.validateFields();
              setEditAndRunConfirm(true);
            }}
          >
            {dictionary.UPDATE_AND_RUN}
          </Button>,
          <Button
            key="ok"
            type="primary"
            disabled={locked || analysisAccessType === AnalysisType.PUBLIC}
            onClick={async (e) => {
              e.stopPropagation();
              await form.validateFields();
              updateParameter();
            }}
          >
            {dictionary.UPDATE}
          </Button>,
        ]}
      >
        {loading && (
          <Spin>
            <div
              style={{
                width: '100%',
                height: '20vh',
              }}
            />
          </Spin>
        )}
        {error && <Result status="error" title="Failed to load form" subTitle={error} />}
        {!loading && !error && (
          <div
            style={{
              padding: '0 10px',
            }}
          >
            <FBParameterForm
              nodeId={paramEditedNodeId}
              onKeyDown={(e) => {
                e.stopPropagation();
              }}
              onKeyUp={(e: any) => {
                e.stopPropagation();
              }}
              form={form}
              paramsList={paramsList}
              dataStructure={dataStructure}
              layout={'horizontal'}
              disabled={false}
              recommendedParamDict={recommendedParamDict}
            />
          </div>
        )}
        <Modal
          centered
          title={
            <h1>
              <WarningOutlined />
            </h1>
          }
          open={editConfirm}
          onOk={(e) => {
            e.stopPropagation();
            editParameters();
            setEditConfirm(false);
            onClose();
            return false;
          }}
          onCancel={(e) => {
            e.stopPropagation();
            setEditConfirm(false);
            return false;
          }}
          width="22vw"
          keyboard={false}
        >
          <h3>Would you like to save your modified parameter?</h3>
          <p>
            If you save the new parameter, the data following the function block with existing
            parameter will invalidate.
          </p>
          {/* <Checkbox
          style={{ marginTop: '10px', color: '#5971C0' }}
          onChange={() => {
          }}
        >
          {' '}
          Don&#39;t show this again
        </Checkbox> */}
        </Modal>
        <Modal
          centered
          title={
            <h1>
              <WarningOutlined />
            </h1>
          }
          open={editAndRunConfirm}
          onOk={(e) => {
            e.stopPropagation();
            editParametersAndRun();
            setEditAndRunConfirm(false);
            onClose();
            return false;
          }}
          onCancel={(e) => {
            e.stopPropagation();
            setEditAndRunConfirm(false);
            return false;
          }}
          width="22vw"
          keyboard={false}
        >
          <h3>Do you want to save the modified parameters and run this node?</h3>
          <p>
            If you save the new parameter, the data following the function block with existing
            parameter will invalidate.
          </p>
        </Modal>
        <Modal
          centered
          title={
            <h1>
              <WarningOutlined />
            </h1>
          }
          open={resettingConfirm}
          onOk={async (e) => {
            e.stopPropagation();
            // setResetKey(Date.now())
            const { data: value } = await requestNodeParams(paramEditedNodeId);
            form.setFieldsValue(value);
            loadFormLoadInfo();
            setResettingConfirm(false);
            return false;
          }}
          onCancel={(e) => {
            e.stopPropagation();
            setResettingConfirm(false);
            return false;
          }}
          width="22vw"
        >
          <h3>Would you like to resetting your modified parameter?</h3>
          <p>If you want to reset this parameter, the modified parameter will be restored</p>
        </Modal>
        <Modal
          centered
          title={
            <h1>
              <WarningOutlined />
            </h1>
          }
          open={resettingToOriginalConfirm}
          onOk={async (e) => {
            e.stopPropagation();
            if (paramEditedNodeId) {
              const { data: value } = await requestRestore(paramEditedNodeId);
              form.setFieldsValue(value);
              loadFormLoadInfo();
            }
            setResettingToOriginalConfirm(false);
            return false;
          }}
          onCancel={(e) => {
            e.stopPropagation();
            setResettingToOriginalConfirm(false);
            return false;
          }}
          width="22vw"
        >
          <h3>Do you want to reset to the original state</h3>
          <p>If you want to reset, the parameters will be restored to their original state</p>
        </Modal>
        <Modal
          open={fillingReasonVisible}
          centered
          title="AI Parameter Filling Reason"
          okButtonProps={{ style: { display: 'none' } }}
          cancelText="Close"
          onCancel={() => {
            setFillingReasonVisible(false);
          }}
        >
          <div
            style={{
              height: '50vh',
              overflowY: 'auto',
            }}
          >
            <Markdown>{fillingReason}</Markdown>
          </div>
        </Modal>
      </Modal>
    </div>
  );
};
export default UpdateParameterModal;
