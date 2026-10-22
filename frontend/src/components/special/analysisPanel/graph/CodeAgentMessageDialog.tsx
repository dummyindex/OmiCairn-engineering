import React, { useState, useEffect, useRef } from 'react';
import { Modal, Spin, Empty, message as antMessage, Button } from 'antd';
import {
  RobotOutlined,
  UserOutlined,
  ToolOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { requestGetCodeAgentMessageList, requestGetMessageContent } from '@/request/codeAgent';
import { downloadJsonText } from '@/util/saveHelpers';
import './CodeAgentMessageDialog.less';

interface Message {
  message_uuid: string;
  s3_key: string;
  last_modified: string;
  size: number;
  presigned_url: string;
  content?: MessageContent;
}

interface MessageContent {
  message_uuid: string;
  computation_id: string;
  timestamp: string;
  message: {
    role: 'assistant' | 'user' | 'tool' | 'system';
    content?: string;
    tool_calls?: any[];
    tool_call_id?: string;
    sequence?: number;
  };
}

interface CodeAgentMessageDialogProps {
  visible: boolean;
  computationId: string;
  onClose: () => void;
}

const CodeAgentMessageDialog: React.FC<CodeAgentMessageDialogProps> = ({
  visible,
  computationId,
  onClose,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const limit = 5;
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const isLoadingRef = useRef(false);
  const lastScrollHeightRef = useRef(0);

  // Fetch message list
  const fetchMessages = async (isLoadMore: boolean = false) => {
    if (isLoadingRef.current) return;

    try {
      isLoadingRef.current = true;
      setLoading(true);

      const currentOffset = isLoadMore ? offset : 0;

      const result = await requestGetCodeAgentMessageList({
        computation_id: computationId,
        offset: currentOffset,
        limit,
      });

      if (result.code !== 200) {
        throw new Error(result.message || 'Failed to fetch messages');
      }

      const newMessages = result.data.messages || [];

      // Fetch content for each message
      const messagesWithContent = await Promise.all(
        newMessages.map(async (msg: Message) => {
          try {
            const content = await requestGetMessageContent(msg.presigned_url);
            return { ...msg, content };
          } catch (error) {
            console.error('Failed to fetch message content:', error);
            return msg;
          }
        }),
      );

      // Sort by sequence number if available, otherwise by timestamp
      messagesWithContent.sort((a, b) => {
        const seqA = a.content?.message?.sequence;
        const seqB = b.content?.message?.sequence;

        if (seqA !== undefined && seqB !== undefined) {
          return seqA - seqB; // Sort by sequence (ascending)
        }

        // Fallback to timestamp
        const timeA = a.content?.timestamp || a.last_modified;
        const timeB = b.content?.timestamp || b.last_modified;
        return timeA > timeB ? 1 : -1;
      });

      if (isLoadMore) {
        // Store scroll height before adding messages at the top
        if (scrollContainerRef.current) {
          lastScrollHeightRef.current = scrollContainerRef.current.scrollHeight;
        }

        // Add old messages at the beginning
        setMessages((prev) => [...messagesWithContent, ...prev]);

        // Restore scroll position after messages are added
        setTimeout(() => {
          if (scrollContainerRef.current) {
            const newScrollHeight = scrollContainerRef.current.scrollHeight;
            scrollContainerRef.current.scrollTop = newScrollHeight - lastScrollHeightRef.current;
          }
        }, 0);
      } else {
        setMessages(messagesWithContent);
        // Scroll to bottom on initial load
        setTimeout(() => {
          if (scrollContainerRef.current) {
            scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
          }
        }, 0);
      }

      setHasMore(result.data.has_more);
      setOffset(currentOffset + limit);
    } catch (error) {
      console.error('Error fetching messages:', error);
      antMessage.error('Failed to load messages');
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
    }
  };

  // Initial load
  useEffect(() => {
    if (visible && computationId) {
      setOffset(0);
      setMessages([]);
      setHasMore(true);
      fetchMessages(false);
    }
  }, [visible, computationId]);

  // Handle scroll for lazy loading (load more on scroll to top)
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    if (loading || !hasMore || isLoadingRef.current) return;

    // Check if scrolled to top (with 100px threshold)
    if (container.scrollTop < 100) {
      fetchMessages(true);
    }
  };

  const handleDownloadMessages = async () => {
    if (!computationId) return;

    try {
      setDownloading(true);
      antMessage.loading({ content: 'Fetching all messages...', key: 'download-messages' });

      const result = await requestGetCodeAgentMessageList({
        computation_id: computationId,
        offset: 0,
        limit: 10000, // allow large limit to get all messages
      });

      if (result.code !== 200) {
        throw new Error(result.message || 'Failed to fetch messages');
      }

      const allMessages = result.data.messages || [];

      antMessage.loading({
        content: `Fetching content for ${allMessages.length} messages...`,
        key: 'download-messages',
      });

      // Fetch content for all messages
      const messagesWithContent = await Promise.all(
        allMessages.map(async (msg: Message) => {
          try {
            const content = await requestGetMessageContent(msg.presigned_url);
            return { ...msg, content };
          } catch (error) {
            console.error('Failed to fetch message content:', error);
            return msg;
          }
        }),
      );

      // Sort by sequence number if available, otherwise by timestamp
      messagesWithContent.sort((a, b) => {
        const seqA = a.content?.message?.sequence;
        const seqB = b.content?.message?.sequence;

        if (seqA !== undefined && seqB !== undefined) {
          return seqA - seqB;
        }

        const timeA = a.content?.timestamp || a.last_modified;
        const timeB = b.content?.timestamp || b.last_modified;
        return timeA > timeB ? 1 : -1;
      });

      const downloadData = {
        computation_id: computationId,
        export_time: new Date().toISOString(),
        total_messages: messagesWithContent.length,
        messages: messagesWithContent.map((msg) => ({
          message_uuid: msg.message_uuid,
          timestamp: msg.content?.timestamp || msg.last_modified,
          role: msg.content?.message?.role,
          sequence: msg.content?.message?.sequence,
          content: msg.content?.message?.content,
          tool_calls: msg.content?.message?.tool_calls,
          tool_call_id: msg.content?.message?.tool_call_id,
        })),
      };

      downloadJsonText(downloadData, `code_agent_messages_${computationId}`);
      antMessage.success({ content: 'Messages downloaded successfully', key: 'download-messages' });
    } catch (error) {
      console.error('Error downloading messages:', error);
      antMessage.error({ content: 'Failed to download messages', key: 'download-messages' });
    } finally {
      setDownloading(false);
    }
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;

    return (
      date.toLocaleDateString() +
      ' ' +
      date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      })
    );
  };

  // Render message content based on role
  const renderMessageContent = (msg: Message) => {
    if (!msg.content || !msg.content.message) {
      return (
        <div className="message-bubble error-message">
          <div className="bubble-content">Failed to load message content</div>
        </div>
      );
    }

    const { role, content, tool_calls } = msg.content.message;
    const timestamp = msg.content.timestamp || msg.last_modified;

    // Assistant message
    if (role === 'assistant') {
      return (
        <div className="message-row assistant-row">
          <div className="message-avatar">
            <RobotOutlined />
          </div>
          <div className="message-content">
            <div className="message-meta">
              <span className="sender-name">Assistant</span>
              <span className="message-time">{formatTime(timestamp)}</span>
            </div>
            {content && (
              <div className="message-bubble assistant-bubble">
                <div className="bubble-content">{content}</div>
              </div>
            )}
            {tool_calls && tool_calls.length > 0 && (
              <div className="message-bubble tool-calls-bubble">
                <div className="tool-calls-header">
                  <ToolOutlined /> Calling {tool_calls.length} tool
                  {tool_calls.length > 1 ? 's' : ''}
                </div>
                {tool_calls.map((tc, idx) => (
                  <div key={idx} className="tool-call-item">
                    <div className="tool-name">
                      {tc.function?.name || tc.name || 'Unknown Tool'}
                    </div>
                    {tc.function?.arguments && (
                      <pre className="tool-args">
                        {typeof tc.function.arguments === 'string'
                          ? tc.function.arguments
                          : JSON.stringify(tc.function.arguments, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      );
    }

    // User message
    if (role === 'user') {
      return (
        <div className="message-row user-row">
          <div className="message-content">
            <div className="message-meta">
              <span className="sender-name">You</span>
              <span className="message-time">{formatTime(timestamp)}</span>
            </div>
            <div className="message-bubble user-bubble">
              <div className="bubble-content">{content || '(No content)'}</div>
            </div>
          </div>
          <div className="message-avatar user-avatar">
            <UserOutlined />
          </div>
        </div>
      );
    }

    // Tool message - display on the right like user messages
    if (role === 'tool') {
      let toolResult;
      try {
        toolResult = content ? JSON.parse(content) : {};
      } catch {
        toolResult = { raw: content };
      }

      return (
        <div className="message-row tool-row">
          <div className="message-content">
            <div className="message-meta">
              <span className="sender-name">Tool Result</span>
              <span className="message-time">{formatTime(timestamp)}</span>
            </div>
            <div className="message-bubble tool-bubble">
              <pre className="tool-result">{JSON.stringify(toolResult, null, 2)}</pre>
            </div>
          </div>
          <div className="message-avatar tool-avatar">
            <ToolOutlined />
          </div>
        </div>
      );
    }

    // System message - display on the right like user messages
    if (role === 'system') {
      return (
        <div className="message-row system-row">
          <div className="message-content">
            <div className="message-meta">
              <span className="sender-name">System</span>
              <span className="message-time">{formatTime(timestamp)}</span>
            </div>
            <div className="message-bubble system-bubble">
              <div className="bubble-content">{content || '(No content)'}</div>
            </div>
          </div>
          <div className="message-avatar system-avatar">
            <InfoCircleOutlined />
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Code Agent Conversation</span>
          <div style={{ marginRight: 24 }}>
            <Button
              type="text"
              icon={<DownloadOutlined />}
              onClick={handleDownloadMessages}
              disabled={loading || downloading}
              loading={downloading}
            >
              Download
            </Button>
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={() => {
                setOffset(0);
                setMessages([]);
                setHasMore(true);
                fetchMessages(false);
              }}
              disabled={loading}
            >
              Refresh
            </Button>
          </div>
        </div>
      }
      open={visible}
      onCancel={onClose}
      width={800}
      footer={null}
      className="code-agent-message-dialog"
    >
      <div className="messages-container" ref={scrollContainerRef} onScroll={handleScroll}>
        {loading && messages.length === 0 && (
          <div className="loading-container">
            <Spin size="large" tip="Loading messages..." />
          </div>
        )}

        {!loading && messages.length === 0 && <Empty description="No messages yet" />}

        {messages.length > 0 && (
          <>
            {loading && hasMore && (
              <div className="loading-more">
                <Spin size="small" /> Loading earlier messages...
              </div>
            )}
            {!hasMore && messages.length > 0 && (
              <div className="no-more-messages">
                <span>— Beginning of conversation —</span>
              </div>
            )}
            <div className="messages-list">
              {messages.map((msg) => (
                <div key={msg.message_uuid} className="message-wrapper">
                  {renderMessageContent(msg)}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};

export default CodeAgentMessageDialog;
