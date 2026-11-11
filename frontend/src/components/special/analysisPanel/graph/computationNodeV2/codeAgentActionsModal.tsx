import React, { useState, useEffect } from 'react';
import { Modal, Spin, Empty, message as antMessage, Button, Collapse, Tag } from 'antd';
import {
  ReloadOutlined,
  ToolOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { requestCodeAgentToolRecord } from '@/request/codeAgent';
import { downloadJsonText } from '@/util/saveHelpers';
import './codeAgentActionsModal.less';

const { Panel } = Collapse;

interface ToolCallRecord {
  tool_call_name: string;
  parameters: any;
  result: any;
  batch_id?: string;
  batch_index?: number;
  batch_total?: number;
  llm_tokens?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    reasoning_tokens?: number;
  } | null;
  timestamp: string;
  duration_seconds?: number;
  _type?: string;
  fix_uuid?: string;
  message?: string;
}

interface CodeAgentActionsModalProps {
  visible: boolean;
  computationId: string;
  onClose: () => void;
}

const CodeAgentActionsModal: React.FC<CodeAgentActionsModalProps> = ({
  visible,
  computationId,
  onClose,
}) => {
  const [records, setRecords] = useState<ToolCallRecord[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch tool call records
  const fetchRecords = async () => {
    if (!computationId) return;

    try {
      setLoading(true);
      const result = await requestCodeAgentToolRecord({
        computation_id: computationId,
      });

      if (result.code !== 200) {
        throw new Error(result.message || 'Failed to fetch action records');
      }

      const recordsData = result.data || [];
      setRecords(recordsData);
    } catch (error) {
      console.error('Error fetching action records:', error);
      antMessage.error('Failed to load action records');
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    if (visible && computationId) {
      fetchRecords();
    }
  }, [visible, computationId]);

  // Format timestamp
  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return timestamp;
    }
  };

  // Render round separator
  const renderRoundSeparator = (record: ToolCallRecord, index: number) => {
    return (
      <div key={`separator-${index}`} className="round-separator">
        <div className="separator-line" />
        <div className="separator-content">
          <ThunderboltOutlined /> {record.message}
        </div>
        <div className="separator-line" />
        <div className="separator-meta">
          <span>Fix UUID: {record.fix_uuid}</span>
          <span>{formatTime(record.timestamp)}</span>
        </div>
      </div>
    );
  };

  // Render tool call record
  const renderToolCallRecord = (record: ToolCallRecord, index: number) => {
    const hasBatchInfo = record.batch_id !== undefined;
    const hasTokens = record.llm_tokens !== null && record.llm_tokens !== undefined;
    const duration = record.duration_seconds || 0;

    return (
      <Panel
        key={`tool-${index}`}
        header={
          <div className="tool-call-header">
            <div className="tool-call-title">
              <ToolOutlined />
              <span className="tool-name">{record.tool_call_name}</span>
              {hasBatchInfo && (
                <Tag color="blue">
                  Batch {record.batch_index}/{record.batch_total}
                </Tag>
              )}
              {duration > 0 && (
                <Tag icon={<ClockCircleOutlined />} color="green">
                  {duration.toFixed(3)}s
                </Tag>
              )}
            </div>
            <div className="tool-call-time">{formatTime(record.timestamp)}</div>
          </div>
        }
        className="tool-call-panel"
      >
        {hasBatchInfo && (
          <div style={{ marginBottom: 16 }}>
            <strong>Batch ID:</strong> <code>{record.batch_id}</code>
          </div>
        )}

        <Collapse size="small" bordered={false} className="detail-collapse">
          {/* Parameters */}
          <Panel
            key="params"
            header={
              <span>
                <strong>Parameters</strong>{' '}
                <Tag color="blue">{Object.keys(record.parameters || {}).length} field(s)</Tag>
              </span>
            }
          >
            <pre className="json-content">{JSON.stringify(record.parameters, null, 2)}</pre>
          </Panel>

          {/* Result */}
          <Panel
            key="result"
            header={
              <span>
                <strong>Result</strong>{' '}
                {typeof record.result === 'string' && (
                  <Tag color="green">{record.result.length} chars</Tag>
                )}
              </span>
            }
          >
            <pre className="json-content">{JSON.stringify(record.result, null, 2)}</pre>
          </Panel>

          {/* Token Usage */}
          {hasTokens && (
            <Panel
              key="tokens"
              header={
                <span>
                  <strong>LLM Token Usage</strong>{' '}
                  <Tag color="purple">{record.llm_tokens!.total_tokens} total</Tag>
                </span>
              }
            >
              <div className="token-usage">
                <Tag color="blue">Prompt: {record.llm_tokens!.prompt_tokens}</Tag>
                <Tag color="green">Completion: {record.llm_tokens!.completion_tokens}</Tag>
                <Tag color="purple">Total: {record.llm_tokens!.total_tokens}</Tag>
                {record.llm_tokens!.reasoning_tokens !== undefined &&
                  record.llm_tokens!.reasoning_tokens > 0 && (
                    <Tag color="orange">Reasoning: {record.llm_tokens!.reasoning_tokens}</Tag>
                  )}
              </div>
            </Panel>
          )}
        </Collapse>
      </Panel>
    );
  };

  // Render individual record (without wrapper div)
  const renderRecord = (record: ToolCallRecord, index: number) => {
    if (record._type === 'round_separator') {
      return renderRoundSeparator(record, index);
    }
    return renderToolCallRecord(record, index);
  };

  // Calculate statistics
  const statistics = React.useMemo(() => {
    const toolCalls = records.filter((r) => r._type !== 'round_separator');
    const roundSeparators = records.filter((r) => r._type === 'round_separator');

    const totalDuration = toolCalls.reduce((sum, r) => sum + (r.duration_seconds || 0), 0);

    const totalTokens = toolCalls.reduce((sum, r) => {
      return sum + (r.llm_tokens?.total_tokens || 0);
    }, 0);

    return {
      totalRecords: toolCalls.length,
      totalRounds: roundSeparators.length,
      totalDuration: totalDuration.toFixed(2),
      totalTokens,
    };
  }, [records]);

  const handleDownloadRecords = () => {
    if (records.length === 0) {
      antMessage.warning('No action records to download');
      return;
    }

    const downloadData = {
      computation_id: computationId,
      export_time: new Date().toISOString(),
      statistics: {
        total_tool_calls: statistics.totalRecords,
        total_rounds: statistics.totalRounds,
        total_duration_seconds: parseFloat(statistics.totalDuration),
        total_tokens: statistics.totalTokens,
      },
      records: records,
    };

    downloadJsonText(downloadData, `code_agent_actions_${computationId}`);
    antMessage.success('Action records downloaded successfully');
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Code Agent Actions</span>
          <div style={{ marginRight: 24 }}>
            <Button
              type="text"
              icon={<DownloadOutlined />}
              onClick={handleDownloadRecords}
              disabled={loading || records.length === 0}
            >
              Download
            </Button>
            <Button type="text" icon={<ReloadOutlined />} onClick={fetchRecords} disabled={loading}>
              Refresh
            </Button>
          </div>
        </div>
      }
      open={visible}
      onCancel={onClose}
      width={900}
      footer={null}
      className="code-agent-actions-modal"
    >
      {loading ? (
        <div className="loading-container">
          <Spin size="large" tip="Loading action records..." />
        </div>
      ) : (
        <>
          {/* Statistics */}
          {records.length > 0 && (
            <div className="statistics-bar">
              <div className="stat-item">
                <ToolOutlined /> {statistics.totalRecords} Tool Calls
              </div>
              <div className="stat-item">
                <ThunderboltOutlined /> {statistics.totalRounds} Rounds
              </div>
              <div className="stat-item">
                <ClockCircleOutlined /> {statistics.totalDuration}s Total Time
              </div>
              {statistics.totalTokens > 0 && (
                <div className="stat-item">
                  <CheckCircleOutlined /> {statistics.totalTokens} Tokens
                </div>
              )}
            </div>
          )}

          {/* Records List */}
          <div className="records-container">
            {records.length === 0 ? (
              <Empty description="No action records available" />
            ) : (
              <Collapse accordion className="records-list">
                {records.map((record, index) => renderRecord(record, index))}
              </Collapse>
            )}
          </div>
        </>
      )}
    </Modal>
  );
};

export default CodeAgentActionsModal;
