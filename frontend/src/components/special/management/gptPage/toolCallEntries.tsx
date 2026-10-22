import { requestV3CallTool } from '@/request/chat';
import { Button } from 'antd';
import { useState } from 'react';

const ToolCallEntries = ({ chatId, toolCalls, showCallButton }) => {
  const [loadingTools, setLoadingTools] = useState<Set<string>>(new Set());

  try {
    let parsedToolCalls: any[] = [];

    // Parse tool_calls if it's a string, otherwise use directly
    if (typeof toolCalls === 'string') {
      parsedToolCalls = JSON.parse(toolCalls);
    } else if (Array.isArray(toolCalls)) {
      parsedToolCalls = toolCalls;
    }

    if (!Array.isArray(parsedToolCalls) || parsedToolCalls.length === 0) {
      return null;
    }

    // Handle tool call execution
    const handleExecuteToolCall = async (toolCall: any, index: number) => {
      const toolName = toolCall.name || toolCall.function?.name || 'Unknown Tool';
      const toolId = toolCall.id || `${toolName}-${index}`;

      setLoadingTools((prev) => new Set(prev).add(toolId));

      try {
        await requestV3CallTool(chatId, toolCall.id, toolCall.name, toolCall.parameters);
      } finally {
        setLoadingTools((prev) => {
          const newSet = new Set(prev);
          newSet.delete(toolId);
          return newSet;
        });
      }
    };

    return (
      <div
        style={{
          marginTop: '12px',
          padding: '8px',
          background: '#fff9f0',
          border: '1px solid #ffe7ba',
          borderRadius: '6px',
        }}
      >
        <div
          style={{
            fontSize: '11px',
            color: '#8b6914',
            marginBottom: '6px',
            fontWeight: '500',
          }}
        >
          🔧 Tool Calls:
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {parsedToolCalls.map((toolCall: any, index: number) => {
            // Handle different tool call formats
            let toolName = 'Unknown Tool';
            let toolParams = {};

            if (toolCall.name) {
              toolName = toolCall.name;
              toolParams = toolCall.parameters || {};
            } else if (toolCall.function) {
              toolName = toolCall.function.name;
              try {
                toolParams =
                  typeof toolCall.function.arguments === 'string'
                    ? JSON.parse(toolCall.function.arguments)
                    : toolCall.function.arguments || {};
              } catch (e) {
                toolParams = {};
              }
            }

            const toolId = toolCall.id || `${toolName}-${index}`;
            const isLoading = loadingTools.has(toolId);

            return (
              <div
                key={index}
                style={{
                  padding: '8px',
                  background: '#fff',
                  border: '1px solid #e6d7b7',
                  borderRadius: '4px',
                  fontSize: '12px',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '4px',
                  }}
                >
                  <div
                    style={{
                      fontWeight: '500',
                      color: '#d46b08',
                      flex: 1,
                    }}
                  >
                    {toolName}
                  </div>
                  {showCallButton && (
                    <Button
                      size="small"
                      type="primary"
                      loading={isLoading}
                      disabled={isLoading}
                      style={{
                        fontSize: '10px',
                        height: '20px',
                        padding: '0 8px',
                        backgroundColor: isLoading ? '#d9d9d9' : '#52c41a',
                        borderColor: isLoading ? '#d9d9d9' : '#52c41a',
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleExecuteToolCall(toolCall, index);
                      }}
                    >
                      {isLoading ? 'Running...' : 'Run'}
                    </Button>
                  )}
                </div>
                {Object.keys(toolParams).length > 0 && (
                  <div
                    style={{
                      fontSize: '11px',
                      color: '#8c8c8c',
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                      marginTop: '4px',
                    }}
                  >
                    {JSON.stringify(toolParams, null, 2)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  } catch (error) {
    console.error('Error rendering tool calls:', error);
    return null;
  }
};

export default ToolCallEntries;
