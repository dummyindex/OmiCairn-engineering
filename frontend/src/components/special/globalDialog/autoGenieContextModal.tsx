import { Modal, Typography, message, Switch, Empty, Spin } from 'antd';
import { useModel } from 'umi';
import { requestDynamicGenerationContext } from '@/request/node';
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

const { Text } = Typography;

interface ContextDetails {
  output: string;
  prompt: string;
}

const AutoGenieContextModal = () => {
  const { dictionary } = useModel('localization');
  const { autoGenieContextInspectedNodeId, setAutoGenieContextInspectedNodeId, nodeList } =
    useModel('analysis');
  const [loading, setLoading] = useState(false);
  const [selectedContext, setSelectedContext] = useState<ContextDetails | null>(null);
  const [markdownMode, setMarkdownMode] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      if (!autoGenieContextInspectedNodeId) return;

      setLoading(true);
      try {
        const node = nodeList.find(
          (n) => n.id.toString() === autoGenieContextInspectedNodeId.toString(),
        );
        if (!node.dynamicGenerationId) {
          setLoading(false);
          setSelectedContext(null);
          return;
        }
        const response = await requestDynamicGenerationContext(
          node.dynamicGenerationId,
          autoGenieContextInspectedNodeId,
        );

        if (response.code === 200) {
          setSelectedContext(response.data);
        } else {
          message.error('Failed to fetch context data');
          setSelectedContext(null);
        }
      } catch (error) {
        message.error('Failed to fetch context data');
        setSelectedContext(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [autoGenieContextInspectedNodeId]);

  const handleClose = () => {
    setAutoGenieContextInspectedNodeId(null);
    setSelectedContext(null);
  };

  return (
    <Modal
      width={window.innerWidth * 0.9}
      centered
      title="Auto Genie Context"
      open={!!autoGenieContextInspectedNodeId}
      onCancel={handleClose}
      cancelText={dictionary.CLOSE}
      okButtonProps={{ style: { display: 'none' } }}
      footer={null}
      loading={loading}
      bodyStyle={{
        height: window.innerHeight * 0.8,
        overflowY: 'auto',
        position: 'relative',
      }}
      style={{
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {loading ? (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%',
            minHeight: '200px',
          }}
        >
          <Spin size="large" tip="Loading context data..." />
        </div>
      ) : selectedContext ? (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '16px',
              paddingBottom: '8px',
              borderBottom: '1px solid #f0f0f0',
            }}
          >
            <Text>Plain Text</Text>
            <Switch checked={markdownMode} onChange={setMarkdownMode} size="small" />
            <Text>Markdown</Text>
          </div>

          <div
            style={{
              flex: 1,
              display: 'flex',
              gap: '16px',
              minHeight: 0,
            }}
          >
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                minWidth: 0,
              }}
            >
              <Text strong style={{ marginBottom: '8px' }}>
                Input Prompt:
              </Text>
              <div
                style={{
                  flex: 1,
                  padding: '12px',
                  backgroundColor: '#f8f9fa',
                  border: '1px solid #e9ecef',
                  borderRadius: '6px',
                  overflowX: 'auto',
                  overflowY: 'auto',
                  fontSize: '13px',
                  fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                  lineHeight: '1.5',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {markdownMode ? (
                  selectedContext.prompt ? (
                    <ReactMarkdown>{selectedContext.prompt}</ReactMarkdown>
                  ) : (
                    <Empty description="No input prompt available" />
                  )
                ) : (
                  <pre
                    style={{
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      fontFamily: 'inherit',
                    }}
                  >
                    {selectedContext.prompt || <Empty description="No input prompt available" />}
                  </pre>
                )}
              </div>
            </div>
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                minWidth: 0,
              }}
            >
              <Text strong style={{ marginBottom: '8px' }}>
                Response:
              </Text>
              <div
                style={{
                  flex: 1,
                  padding: '12px',
                  backgroundColor: '#f8f9fa',
                  border: '1px solid #e9ecef',
                  borderRadius: '6px',
                  overflowX: 'auto',
                  overflowY: 'auto',
                  fontSize: '13px',
                  fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                  lineHeight: '1.5',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {markdownMode ? (
                  selectedContext.output ? (
                    <ReactMarkdown>{selectedContext.output}</ReactMarkdown>
                  ) : (
                    <Empty description="No output data available" />
                  )
                ) : (
                  <pre
                    style={{
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      fontFamily: 'inherit',
                    }}
                  >
                    {selectedContext.output || <Empty description="No output data available" />}
                  </pre>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <Empty description="No context data available" />
      )}
    </Modal>
  );
};

export default AutoGenieContextModal;
