import { useState, useEffect } from 'react';
import { Modal, Button, message, Divider, Input, Select } from 'antd';
import { useModel } from 'umi';
import { EditOutlined, QuestionCircleOutlined, RedoOutlined } from '@ant-design/icons';
import CustomRadio from '@/components/common/customRadio';
import CustomImage from '@/components/common/customImage';
import * as customIconNames from '@/assets/customIconNames';
import {
  requestImportPipelineTemplate,
  requestPublicPTGroupList,
  requestPublicPtList,
} from '@/request/pipeline';
import { requestGeneratePipeline } from '@/request/gptPipeline';
import { findHeadNodes } from '@/util/flowTool';
import { requestCreateNode } from '@/request/node';
import { NodeType } from '@/constants/node';
import { requestCreateEdge } from '@/request/edge';

type BasicInfoProps = {
  goNext: () => void;
};
const BasicInfo = (props: BasicInfoProps) => {
  const {
    selectedDataId,
    setSelectedDataId,
    setSelectedDataInfo,
    setRequests,
    requests,
    dataOptions,
    setRequestsTemplateModelOpen,
  } = useModel('workflowHelper');
  const { goNext } = props;

  const [reqValue, setReqValue] = useState<string | null>(null);

  useEffect(() => {
    setReqValue(requests);
  }, [requests]);

  return (
    <div
      style={{
        padding: '1em',
        display: 'flex',
        justifyContent: 'flex-start',
        flexDirection: 'column',
        alignItems: 'stretch',
        minHeight: '100%',
        gap: '20px',
        backgroundColor: 'rgb(245,245,247)',
      }}
    >
      <div>
        <div
          style={{
            fontSize: '1.1em',
            fontWeight: 'bold',
            marginBottom: '0.5em',
          }}
        >
          Selected Data:{' '}
        </div>
        <Select
          value={selectedDataId}
          options={dataOptions}
          style={{ width: '100%' }}
          onSelect={(value: any) => {
            setSelectedDataId(value);
            const selectedData = dataOptions.find((item) => item.value === value);
            setSelectedDataInfo(selectedData);
          }}
        />
      </div>
      <div
        style={{
          height: '1em',
        }}
      />
      <div>
        <div
          style={{
            fontSize: '1.1em',
            fontWeight: 'bold',
            marginBottom: '0.5em',
            display: 'flex',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <span style={{ color: 'red' }}>*</span>Requests:{' '}
          </div>
          <Button type="primary" onClick={() => setRequestsTemplateModelOpen(true)}>
            Request Templates
          </Button>
        </div>
        <Input.TextArea
          value={reqValue}
          autoSize={{ minRows: 8, maxRows: 15 }}
          onChange={(e: any) => {
            console.log(e.target.value);
            setReqValue(e.target.value);
          }}
        />
      </div>
      <div
        style={{
          flex: 1,
        }}
      />
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        <Button
          type="primary"
          onClick={() => {
            setRequests(reqValue);
            goNext();
          }}
        >
          Next
        </Button>
      </div>
    </div>
  );
};

const RequestTemplatesModal = () => {
  const { requestsTemplateModelOpen, setRequestsTemplateModelOpen, setRequests } =
    useModel('workflowHelper');

  const [pTGroupList, setePTGroupList] = useState<any[]>([]);

  const loadPtList = async () => {
    const { data: pTGroupList } = await requestPublicPTGroupList();
    const filledPtGroupList = await Promise.all(
      pTGroupList.map(async (ptGroupName: string) => {
        const { data: ptList } = await requestPublicPtList(ptGroupName);
        return {
          ptGroupName,
          ptList,
        };
      }),
    );
    setePTGroupList(filledPtGroupList);
  };

  useEffect(() => {
    loadPtList();
  }, []);

  return (
    <Modal
      title="Request Templates"
      open={requestsTemplateModelOpen}
      onCancel={() => setRequestsTemplateModelOpen(false)}
      footer={null}
      width="40vw"
      centered
    >
      <div
        style={{
          width: '100%',
          overflow: 'auto',
          height: '55vh',
          backgroundColor: 'rgb(245,245,247)',
        }}
      >
        {(!pTGroupList || pTGroupList.length === 0) && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
              fontSize: '0.9em',
              color: 'gray',
              lineHeight: '2em',
            }}
          >
            -- No data --
          </div>
        )}
        {pTGroupList &&
          pTGroupList.length > 0 &&
          pTGroupList.map((ptGroup: any) => {
            const { ptList, ptGroupName } = ptGroup;
            return (
              <div key={ptGroupName}>
                <Divider orientation="left">{ptGroup.ptGroupName}</Divider>
                <div>
                  {ptList.map((pt: any) => {
                    if (!pt?.description) {
                      return null;
                    }
                    return (
                      <div
                        key={pt.id}
                        style={{
                          backgroundColor: 'white',
                          borderRadius: '1em',
                          margin: '0.5em',
                          padding: '1em',
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            fontWeight: 'bold',
                          }}
                        >
                          <div>{pt.name}</div>
                          <Button
                            type="primary"
                            onClick={() => {
                              setRequestsTemplateModelOpen(false);
                              setRequests(pt.description);
                            }}
                          >
                            Use
                          </Button>
                        </div>
                        <pre
                          style={{
                            color: 'gray',
                            fontSize: '0.9em',
                            padding: '0.5em',
                            whiteSpace: 'pre-wrap' /* or use 'pre-line' */,
                            wordWrap: 'break-word',
                          }}
                        >
                          {pt.description}
                        </pre>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
      </div>
    </Modal>
  );
};

type OptimizeInfoProps = {
  goPre: () => void;
  goNext: () => void;
};
const OptimizeInfo = (props: OptimizeInfoProps) => {
  const { goPre, goNext } = props;

  const { isRefreshingOptimization, requests, setRequests } = useModel('workflowHelper');

  const [useOptimized, setUseOptimized] = useState<boolean>(false);

  const [optimizedRequests, setOptimizedRequests] = useState<string | null>(null);

  useEffect(() => {
    setOptimizedRequests(requests);
  }, [requests]);

  return (
    <div
      style={{
        height: '100%',
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
        alignItems: 'stretch',
      }}
    >
      <div
        style={{
          padding: '1em',
          display: 'flex',
          flexDirection: 'row',
          justifyContent: 'flex-start',
          alignItems: 'stretch',
          flex: 1,
          gap: '1em',
          backgroundColor: 'rgb(245,245,247)',
        }}
      >
        <div
          style={{
            height: '100%',
            width: '50%',
            backgroundColor: 'white',
            borderRadius: '1em',
            border: !useOptimized ? '1px solid #1890ff' : 'none',
          }}
        >
          <div
            style={{
              fontSize: '1.2em',
              fontWeight: 'bold',
              padding: '1em',
              display: 'flex',
              justifyContent: 'flex-start',
              alignItems: 'center',
              // gap: '0.5em',
            }}
          >
            <span>User Request</span>
            <div
              style={{
                flex: 1,
              }}
            />
            <Button type="text" icon={<EditOutlined />} size="default" />
            <Button
              type="text"
              onClick={() => setUseOptimized(false)}
              icon={<CustomRadio value={!useOptimized} />}
            />
          </div>
          <div
            style={{
              height: '40vh',
              overflow: 'auto',
            }}
          >
            <pre
              style={{
                padding: '1em',
                whiteSpace: 'pre-wrap' /* or use 'pre-line' */,
                wordWrap: 'break-word',
              }}
            >
              {requests}
            </pre>
          </div>
        </div>
        <div
          style={{
            height: '100%',
            width: '50%',
            backgroundColor: 'white',
            borderRadius: '1em',
            border: useOptimized ? '1px solid #1890ff' : 'none',
          }}
        >
          <div
            style={{
              fontSize: '1.2em',
              fontWeight: 'bold',
              padding: '1em',
              display: 'flex',
              justifyContent: 'flex-start',
              alignItems: 'center',
              // gap: '0.5em',
            }}
          >
            <span>Augmented Request</span>
            <div
              style={{
                flex: 1,
              }}
            />
            <Button
              type="text"
              loading={isRefreshingOptimization}
              icon={
                <RedoOutlined
                  style={{
                    transform: 'rotate(-90deg)',
                  }}
                />
              }
              size="default"
            />
            <Button type="text" icon={<EditOutlined />} size="default" />
            <Button
              type="text"
              onClick={() => setUseOptimized(true)}
              icon={<CustomRadio value={useOptimized} />}
            />
          </div>
          <div
            style={{
              height: '40vh',
              overflow: 'auto',
            }}
          >
            <pre
              style={{
                padding: '1em',
                whiteSpace: 'pre-wrap' /* or use 'pre-line' */,
                wordWrap: 'break-word',
              }}
            >
              {optimizedRequests}
            </pre>
          </div>
        </div>
      </div>
      <div
        style={{
          display: 'flex',
          flexDirection: 'row',
          justifyContent: 'flex-start',
          gap: '1em',
          padding: '1em',
        }}
      >
        <div
          style={{
            flex: 1,
          }}
        />
        <Button onClick={goPre}>Previous</Button>
        <Button
          onClick={() => {
            setRequests(useOptimized ? optimizedRequests : requests);
            goNext();
          }}
          type="primary"
        >
          Confirm
        </Button>
      </div>
    </div>
  );
};

type SelectOperationProps = {
  goPre: () => void;
};
const SelectOperation = (props: SelectOperationProps) => {
  const { goPre } = props;

  const { setShowIntroduction, fetchSimilarPT, fetchGeneratedPT } = useModel('workflowHelper');

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
        alignItems: 'stretch',
        height: '100%',
      }}
    >
      <div
        style={{
          padding: '1em',
          display: 'flex',
          flexDirection: 'row',
          justifyContent: 'flex-start',
          alignItems: 'center',
          gap: '1em',
          flex: 1,
          backgroundColor: 'rgb(245,245,247)',
        }}
      >
        <div
          style={{
            height: '70%',
            width: '50%',
            borderRadius: '1em',
            backgroundColor: 'white',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '2em',
            cursor: 'pointer',
          }}
          onClick={(e: any) => {
            // Prevent event bubbling
            e.stopPropagation();
            fetchSimilarPT();
          }}
        >
          <div
            style={{
              fontSize: '1em',
              fontWeight: 'bold',
              padding: '0.5em',
            }}
          >
            Find Similar Pipeline Templates
          </div>
          <CustomImage
            style={{
              width: '9vh',
            }}
            name={customIconNames.WORKFLOW_SEARCH}
          />
        </div>
        <div
          style={{
            height: '70%',
            width: '50%',
            borderRadius: '1em',
            backgroundColor: 'white',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '2em',
            cursor: 'pointer',
          }}
          onClick={(e: any) => {
            // Prevent event bubbling
            e.stopPropagation();
            fetchGeneratedPT();
          }}
        >
          <div
            style={{
              fontSize: '1em',
              fontWeight: 'bold',
              padding: '1em',
            }}
          >
            AI Generated Workflow{' '}
            <Button
              icon={<QuestionCircleOutlined />}
              type="text"
              onClick={() => {
                setShowIntroduction(true);
              }}
            />
          </div>
          <CustomImage
            style={{
              width: '9vh',
            }}
            name={customIconNames.WORKFLOW_ROBOT}
          />
        </div>
      </div>
      <div
        style={{
          display: 'flex',
          flexDirection: 'row',
          justifyContent: 'flex-start',
          gap: '1em',
          padding: '0.5em',
        }}
      >
        <div
          style={{
            flex: 1,
          }}
        />
        <Button onClick={goPre}>Previous</Button>
      </div>
    </div>
  );
};

const FindingSimilarPrompt = () => {
  const { isFindingSimilar } = useModel('workflowHelper');

  return (
    <Modal
      open={isFindingSimilar}
      footer={null}
      title={null}
      closeIcon={<></>}
      maskClosable={false}
      centered
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '1em',
        }}
      >
        <div
          style={{
            fontSize: '1.2em',
            fontWeight: 'bold',
          }}
        >
          Identifying closest match for pipeline template
        </div>
        <CustomImage
          name={customIconNames.WORKFLOW_LOADING}
          style={{
            width: '10vh',
          }}
        />
      </div>
    </Modal>
  );
};

const GeneraingPrompt = () => {
  const { isGenerating } = useModel('workflowHelper');

  return (
    <Modal
      open={isGenerating}
      closeIcon={<></>}
      footer={null}
      title={null}
      maskClosable={false}
      centered
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '1em',
        }}
      >
        <div
          style={{
            fontSize: '1.2em',
            fontWeight: 'bold',
          }}
        >
          Generating AI pipeline
        </div>
        <CustomImage
          name={customIconNames.WORKFLOW_LOADING}
          style={{
            width: '10vh',
          }}
        />
      </div>
    </Modal>
  );
};

const SimilarTemplateBox = () => {
  const {
    similarTemplate,
    setShowSimilarTemplate,
    showSimilarTemplate,
    fetchSimilarPT,
    setIsImporting,
    requests,
    selectedDataId,
    selectedDataInfo,
  } = useModel('workflowHelper');
  const { analysisId } = useModel('analysis');
  const { id, description } = similarTemplate || {};

  const importPT = async (e: any) => {
    e.stopPropagation();
    setShowSimilarTemplate(false);
    setIsImporting(true);
    try {
      const {
        data: { newNodeList, newEdgeList },
      } = await requestImportPipelineTemplate(id, analysisId);
      if (!selectedDataId) {
        console.warn('No data selected');
        return;
      }
      const headNodes = findHeadNodes(newEdgeList, newNodeList);
      console.log('headNodes', headNodes);
      const { label: name } = selectedDataInfo || {};
      const nodesCreatedResult = await Promise.all(
        headNodes.map(async (node: any) => {
          console.log('node', node);
          const { data: nodeEntity } = await requestCreateNode(
            NodeType.DATA_NODE,
            node.x - 300,
            node.y,
            analysisId,
            selectedDataId + '',
            null,
            name,
          );
          const { id: dataNodeId } = nodeEntity;
          const { data: edgeEntity } = await requestCreateEdge(dataNodeId, node.id, analysisId);
          return {
            nodeEntity,
            edgeEntity,
          };
        }),
      );
      console.log('nodesCreatedResult', nodesCreatedResult);
      message.success('Pipeline template imported successfully');
    } catch (e) {
      console.error(e);
      message.error('Failed to import pipeline template');
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <Modal
      open={showSimilarTemplate}
      onCancel={() => setShowSimilarTemplate(false)}
      title="Similar Pipeline Template"
      footer={null}
      centered
    >
      {!similarTemplate && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '20vh',
            fontSize: '0.9em',
            color: 'gray',
          }}
        >
          -- Find Failed --
        </div>
      )}
      {similarTemplate && (
        <div
          style={{
            padding: '1em',
          }}
        >
          <div
            style={{
              fontSize: '1.1em',
              fontWeight: 'bold',
              marginBottom: '1em',
            }}
          >
            Pipeline ID: {id}
          </div>
          <pre
            style={{
              whiteSpace: 'pre-wrap' /* or use 'pre-line' */,
              wordWrap: 'break-word',
              maxHeight: '40vh',
            }}
          >
            {description}
          </pre>
        </div>
      )}
      <Divider />
      {requests && (
        <div
          style={{
            padding: '1em',
          }}
        >
          <div
            style={{
              fontSize: '1.1em',
              fontWeight: 'bold',
              marginBottom: '10px',
            }}
          >
            Requests:
          </div>
          <div
            style={{
              height: '15vh',
              overflow: 'auto',
              padding: '1em',
              backgroundColor: 'white',
            }}
          >
            <pre
              style={{
                whiteSpace: 'pre-wrap' /* or use 'pre-line' */,
                wordWrap: 'break-word',
              }}
            >
              {requests}
            </pre>
          </div>
        </div>
      )}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '1em',
        }}
      >
        <div style={{ flex: 1 }} />
        <Button
          type="primary"
          onClick={(e: any) => {
            // Prevent event bubbling
            e.stopPropagation();
            setShowSimilarTemplate(false);
            fetchSimilarPT();
          }}
        >
          Retry
        </Button>
        <Button type="primary" onClick={importPT} disabled={!similarTemplate}>
          Import
        </Button>
      </div>
    </Modal>
  );
};

const GeneratedTemplateBox = () => {
  const {
    generatedTemplate,
    setShowGeneratedTemplate,
    showGeneratedTemplate,
    fetchGeneratedPT,
    setIsImporting,
    requests,
    selectedDataId,
    selectedDataInfo,
  } = useModel('workflowHelper');
  const { analysisId } = useModel('analysis');
  const { data: pTStructureStr, message: description } = generatedTemplate || {};

  const pTStructure = pTStructureStr ? JSON.parse(pTStructureStr) : {};

  const keys = pTStructure ? Object.keys(pTStructure).sort((a, b) => Number(a) - Number(b)) : [];

  const importPT = async (e: any) => {
    // Prevent event bubbling
    e.stopPropagation();
    setShowGeneratedTemplate(false);
    setIsImporting(true);
    try {
      const {
        data: { nodes, edges },
      } = await requestGeneratePipeline(pTStructure, analysisId);
      if (!selectedDataId) {
        console.warn('No data selected');
        return;
      }
      const headNodes = findHeadNodes(edges, nodes);
      const { label: name } = selectedDataInfo || {};
      const nodesCreatedResult = await Promise.all(
        headNodes.map(async (node: any) => {
          const { data: nodeEntity } = await requestCreateNode(
            NodeType.DATA_NODE,
            node.x - 300,
            node.y,
            analysisId,
            selectedDataId + '',
            null,
            name,
          );
          const { id: dataNodeId } = nodeEntity;
          const { data: edgeEntity } = await requestCreateEdge(dataNodeId, node.id, analysisId);
          return {
            nodeEntity,
            edgeEntity,
          };
        }),
      );
      console.log('nodesCreatedResult', nodesCreatedResult);
      message.success('Pipeline template imported successfully');
    } catch (e) {
      console.error(e);
      message.error('Failed to import pipeline template');
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <Modal
      open={showGeneratedTemplate}
      onCancel={() => setShowGeneratedTemplate(false)}
      title="Generated Pipeline Template"
      footer={null}
      centered
    >
      {!generatedTemplate && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '20vh',
            fontSize: '0.9em',
            color: 'gray',
          }}
        >
          -- Generate Failed --
        </div>
      )}
      {generatedTemplate && (
        <div
          style={{
            padding: '1em',
          }}
        >
          <div
            style={{
              fontSize: '1.1em',
              fontWeight: 'bold',
              marginBottom: '1em',
            }}
          >
            Pipeline Structure:
          </div>
          <div>
            {keys.map((key) => {
              return (
                <div key={key}>
                  <div>
                    {key}: {pTStructure[key]}
                  </div>
                </div>
              );
            })}
          </div>
          <Divider />
          <div
            style={{
              fontSize: '1.1em',
              fontWeight: 'bold',
              marginBottom: '1em',
            }}
          >
            Pipeline Description:
          </div>
          <pre
            style={{
              whiteSpace: 'pre-wrap' /* or use 'pre-line' */,
              wordWrap: 'break-word',
              maxHeight: '40vh',
            }}
          >
            {description}
          </pre>
        </div>
      )}
      <Divider />
      {requests && (
        <div
          style={{
            padding: '1em',
          }}
        >
          <div
            style={{
              fontSize: '1.1em',
              fontWeight: 'bold',
              marginBottom: '10px',
            }}
          >
            Requests:
          </div>
          <div
            style={{
              height: '15vh',
              overflow: 'auto',
              padding: '1em',
              backgroundColor: 'white',
            }}
          >
            <pre
              style={{
                whiteSpace: 'pre-wrap' /* or use 'pre-line' */,
                wordWrap: 'break-word',
              }}
            >
              {requests}
            </pre>
          </div>
        </div>
      )}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '1em',
        }}
      >
        <div style={{ flex: 1 }} />
        <Button
          type="default"
          onClick={(e: any) => {
            // Prevent event bubbling
            e.stopPropagation();
            setShowGeneratedTemplate(false);
            fetchGeneratedPT();
          }}
        >
          Retry
        </Button>
        <Button type="primary" onClick={importPT} disabled={!generatedTemplate}>
          Import
        </Button>
      </div>
    </Modal>
  );
};

const Introduction = () => {
  const { showIntroduction, setShowIntroduction } = useModel('workflowHelper');
  return (
    <Modal
      open={showIntroduction}
      onCancel={() => setShowIntroduction(false)}
      title={null}
      footer={null}
      centered
    >
      <div
        style={{
          padding: '1em',
        }}
      >
        <div
          style={{
            fontSize: '1.5em',
            fontWeight: 'bold',
            marginBottom: '1em',
            textAlign: 'center',
          }}
        >
          What is AI Generated Workflow?
        </div>
        <div
          style={{
            fontSize: '1em',
            textIndent: '2em',
            textAlign: 'justify',
          }}
        >
          A Large Language Model (LLM) based workflow generator uses advanced AI algorithms to
          create, optimize, and suggest workflows or processes. It analyzes data and your inputs to
          generate efficient procedural steps, improving productivity and decision-making in various
          tasks you may want to achieve.
        </div>
      </div>
    </Modal>
  );
};

export const ImportingPrompt = () => {
  const { isImporting } = useModel('workflowHelper');

  return (
    <Modal
      open={isImporting}
      closeIcon={<></>}
      footer={null}
      title={null}
      maskClosable={false}
      centered
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '1em',
        }}
      >
        <div
          style={{
            fontSize: '1.2em',
            fontWeight: 'bold',
          }}
        >
          Importing AI pipeline
        </div>
        <CustomImage
          name={customIconNames.WORKFLOW_LOADING}
          style={{
            width: '10vh',
          }}
        />
      </div>
    </Modal>
  );
};

enum Step {
  BasicInfo = 'basicInfo',
  OptimizeRequest = 'optimizeRequest',
  SelectOperation = 'selectOperation',
  FindSimilar = 'findSimilar',
  Generate = 'generate',
}

const stepOrderMap = new Map()
  .set(Step.BasicInfo, {
    pre: null,
    next: Step.OptimizeRequest,
  })
  .set(Step.OptimizeRequest, {
    pre: Step.BasicInfo,
    next: Step.SelectOperation,
  })
  .set(Step.SelectOperation, {
    pre: Step.OptimizeRequest,
    next: null,
  })
  .set(Step.FindSimilar, {
    pre: Step.SelectOperation,
    next: null,
  })
  .set(Step.Generate, {
    pre: Step.SelectOperation,
    next: null,
  });

const WorkflowGenerator = () => {
  const [step, setStep] = useState(Step.BasicInfo);

  const nextStep = () => {
    const nextStep = stepOrderMap.get(step)?.next;
    if (!nextStep) {
      return;
    }
    setStep(nextStep);
  };

  const preStep = () => {
    const preStep = stepOrderMap.get(step)?.pre;
    if (!preStep) {
      return;
    }
    setStep(preStep);
  };

  return (
    <div
      style={{
        width: '100%',
        overflow: 'auto',
        height: '60vh',
      }}
    >
      {step === Step.BasicInfo && <BasicInfo goNext={nextStep} />}
      {step === Step.OptimizeRequest && <OptimizeInfo goPre={preStep} goNext={nextStep} />}
      {step === Step.SelectOperation && <SelectOperation goPre={preStep} />}
      <RequestTemplatesModal />
      <Introduction />
      <FindingSimilarPrompt />
      <GeneraingPrompt />
      <ImportingPrompt />
      <SimilarTemplateBox />
      <GeneratedTemplateBox />
    </div>
  );
};

export default WorkflowGenerator;
