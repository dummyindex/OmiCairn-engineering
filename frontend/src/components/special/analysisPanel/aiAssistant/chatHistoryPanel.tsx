import React, { useState } from 'react';
import { Button, List, Typography, Divider, message } from 'antd';
import { DeleteOutlined, LoadingOutlined } from '@ant-design/icons';
import type { ChatSession } from '@/services/chatbotService';
import chatbotService from '@/services/chatbotService';

const { Text } = Typography;

interface ChatHistoryPanelProps {
  onClose: () => void;
  onChatSelect: (chatId: string) => void;
  chatHistory: ChatSession[];
  onSessionDeleted: (sessionId: string) => void;
  isLoadingSession?: boolean;
}

const ChatHistoryPanel: React.FC<ChatHistoryPanelProps> = ({
  onChatSelect,
  chatHistory,
  onSessionDeleted,
  isLoadingSession = false,
}) => {
  const [hoveredItemId, setHoveredItemId] = useState<string | null>(null);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    try {
      setDeletingSessionId(sessionId);
      await chatbotService.deleteSession(sessionId);
      onSessionDeleted(sessionId);
      message.success('Chat session deleted successfully');
    } catch (error) {
      message.error('Failed to delete chat session');
    } finally {
      setDeletingSessionId(null);
    }
  };

  const groupChatsByTime = (sessions: ChatSession[]) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

    const groups: Record<string, ChatSession[]> = {
      Today: [],
      Yesterday: [],
      'Last 7 days': [],
      Older: [],
    };

    sessions.forEach((session) => {
      const sessionDate = new Date(session.updatedTime);

      if (sessionDate >= today) {
        groups.Today.push(session);
      } else if (sessionDate >= yesterday) {
        groups.Yesterday.push(session);
      } else if (sessionDate >= weekAgo) {
        groups['Last 7 days'].push(session);
      } else {
        groups.Older.push(session);
      }
    });

    // Remove empty groups
    Object.keys(groups).forEach((key) => {
      if (groups[key].length === 0) {
        delete groups[key];
      }
    });

    return groups;
  };

  const groupedHistory = groupChatsByTime(chatHistory);

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#fff',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {isLoadingSession && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <LoadingOutlined style={{ color: '#1890ff', fontSize: '16px' }} />
            <span style={{ color: '#666', fontSize: '14px' }}>Loading chat session...</span>
          </div>
        </div>
      )}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '0 5px',
        }}
      >
        {Object.keys(groupedHistory).length > 0 ? (
          Object.entries(groupedHistory).map(([period, sessions]) => (
            <div key={period}>
              <Divider orientation="left" style={{ margin: '8px 5px 6px' }}>
                <Text type="secondary" style={{ fontSize: '14px' }}>
                  {period}
                </Text>
              </Divider>
              <List
                itemLayout="vertical"
                dataSource={sessions}
                renderItem={(session) => (
                  <List.Item
                    style={{
                      padding: '10px 16px',
                      cursor: 'pointer',
                      backgroundColor: hoveredItemId === session.id ? '#F5F5F5' : 'transparent',
                      borderRadius: '8px',
                      marginBottom: '8px',
                      transition: 'background-color 0.2s ease',
                    }}
                    onClick={() => !isLoadingSession && onChatSelect(session.id)}
                    onMouseEnter={() => setHoveredItemId(session.id)}
                    onMouseLeave={() => setHoveredItemId(null)}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                      }}
                    >
                      <div style={{ flex: 1 }}>
                        <div
                          style={{
                            color: 'rgba(31, 31, 31, 1)',
                            fontWeight: 400,
                            font: 'Roboto',
                            fontSize: '14px',
                            lineHeight: '22px',
                          }}
                        >
                          {session.title}
                        </div>
                        <div
                          style={{
                            color: 'rgba(89, 89, 89, 1)',
                            fontWeight: 400,
                            font: 'Roboto',
                            fontSize: '12px',
                            lineHeight: '20px',
                            marginTop: '4px',
                          }}
                        >
                          {session.messageCount} messages •{' '}
                          {new Date(session.updatedTime).toLocaleString()}
                        </div>
                      </div>
                      <Button
                        type="text"
                        icon={<DeleteOutlined />}
                        size="small"
                        loading={deletingSessionId === session.id}
                        style={{
                          marginLeft: '8px',
                          opacity: hoveredItemId === session.id ? 1 : 0.6,
                        }}
                        onClick={(e) => handleDeleteSession(session.id, e)}
                      />
                    </div>
                  </List.Item>
                )}
              />
            </div>
          ))
        ) : (
          <div
            style={{
              textAlign: 'center',
              padding: '20px',
              color: '#999',
            }}
          >
            No chat history available.
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatHistoryPanel;
