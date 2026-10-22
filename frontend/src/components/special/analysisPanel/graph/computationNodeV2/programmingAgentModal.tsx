import { useEffect, useState, useRef } from 'react';
import { Modal, Tabs, Spin, Empty, message } from 'antd';
import { requestLatestComputation, requestProgrammingAgentMessages } from '@/request/computation';
import styles from './programmingAgentModal.less';

const { TabPane } = Tabs;

interface ProgrammingAgentModalProps {
  visible: boolean;
  nodeId: string;
  computationId?: string;
  onClose: () => void;
}

interface MessageItem {
  uuid: string;
  timestamp: number;
  messages: any[];
}

interface PaginationInfo {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_more: boolean;
}

const ProgrammingAgentModal: React.FC<ProgrammingAgentModalProps> = ({
  visible,
  nodeId,
  computationId: propComputationId,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState('messages');
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [messagesList, setMessagesList] = useState<MessageItem[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [computationId, setComputationId] = useState<string | null>(propComputationId || null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Fetch latest computation if computationId is not provided
  const fetchComputationId = async () => {
    if (!nodeId) return;

    try {
      const { data: latestComputation } = await requestLatestComputation(nodeId);
      if (latestComputation?.id) {
        setComputationId(latestComputation.id.toString());
      }
    } catch (error) {
      console.error('Failed to fetch latest computation:', error);
      message.error('Failed to fetch computation information');
    }
  };

  // Fetch messages with pagination
  const fetchMessages = async (page: number = 1, append: boolean = false) => {
    if (!computationId) return;

    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      const { data: result } = await requestProgrammingAgentMessages(
        computationId,
        page,
        20, // page_size
      );

      console.log('Programming Agent Messages response:', result);

      if (result) {
        const newMessages = result.data || [];
        if (append) {
          setMessagesList((prev) => [...prev, ...newMessages]);
        } else {
          setMessagesList(newMessages);
        }
        setPagination(result.pagination);
      }
    } catch (error) {
      console.error('Failed to fetch programming agent messages:', error);
      message.error('Failed to load messages');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  // Handle scroll for lazy loading
  const handleScroll = () => {
    const container = scrollContainerRef.current;
    if (!container || loadingMore || !pagination?.has_more) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    // Load more when scrolled to bottom (with 100px threshold)
    if (scrollTop + clientHeight >= scrollHeight - 100) {
      const nextPage = pagination.page + 1;
      fetchMessages(nextPage, true);
    }
  };

  useEffect(() => {
    if (visible) {
      if (!computationId && nodeId) {
        fetchComputationId();
      }
    } else {
      // Reset state when modal closes
      setMessagesList([]);
      setPagination(null);
      setActiveTab('messages');
    }
  }, [visible, nodeId]);

  useEffect(() => {
    if (visible && computationId && activeTab === 'messages') {
      fetchMessages(1, false);
    }
  }, [visible, computationId, activeTab]);

  const renderMessageItem = (item: MessageItem) => {
    const date = new Date(item.timestamp * 1000);
    const formattedDate = date.toLocaleString();

    return (
      <div key={`${item.uuid}-${item.timestamp}`} className={styles.messageItem}>
        <div className={styles.messageHeader}>
          <span className={styles.messageUuid}>Session: {item.uuid}</span>
          <span className={styles.messageTime}>{formattedDate}</span>
        </div>
        <div className={styles.messageContent}>
          {item.messages && item.messages.length > 0 ? (
            <div className={styles.messagesContainer}>
              {item.messages.map((msg: any, index: number) => (
                <div key={index} className={styles.singleMessage}>
                  <div className={styles.messageRole}>
                    <strong>{msg.role || 'unknown'}:</strong>
                  </div>
                  <div className={styles.messageText}>
                    {typeof msg.content === 'string' ? (
                      <pre className={styles.messageContentPre}>{msg.content}</pre>
                    ) : (
                      <pre className={styles.messageContentPre}>
                        {JSON.stringify(msg.content, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyMessages}>No messages in this session</div>
          )}
        </div>
      </div>
    );
  };

  const renderMessagesTab = () => {
    if (loading) {
      return (
        <div className={styles.loadingContainer}>
          <Spin size="large" />
          <div className={styles.loadingText}>Loading messages...</div>
        </div>
      );
    }

    if (messagesList.length === 0) {
      return (
        <div className={styles.emptyContainer}>
          <Empty description="No programming agent messages found" />
        </div>
      );
    }

    return (
      <div
        className={styles.messagesScrollContainer}
        ref={scrollContainerRef}
        onScroll={handleScroll}
      >
        {messagesList.map((item) => renderMessageItem(item))}
        {loadingMore && (
          <div className={styles.loadingMoreContainer}>
            <Spin size="small" />
            <span className={styles.loadingMoreText}>Loading more...</span>
          </div>
        )}
        {pagination && !pagination.has_more && messagesList.length > 0 && (
          <div className={styles.noMoreData}>No more messages</div>
        )}
      </div>
    );
  };

  const renderNotebookTab = () => {
    return (
      <div className={styles.notebookContainer}>
        <Empty description="Notebook view coming soon..." />
      </div>
    );
  };

  return (
    <Modal
      open={visible}
      title={<div className={styles.modalTitle}>Programming Agent</div>}
      onCancel={onClose}
      footer={null}
      width={900}
      centered
      className={styles.programmingAgentModal}
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab} className={styles.tabsContainer}>
        <TabPane tab="Programming Agent Messages" key="messages">
          {renderMessagesTab()}
        </TabPane>
        <TabPane tab="Notebook" key="notebook">
          {renderNotebookTab()}
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default ProgrammingAgentModal;
