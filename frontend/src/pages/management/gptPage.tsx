import ActionsResultArea from '@/components/special/management/gptPage/actionsResultArea';
import AnalysisTree from '@/components/special/management/gptPage/analysisTree';
import ChatShareModal from '@/components/special/management/gptPage/chatShareModal';
import DialogueArea from '@/components/special/management/gptPage/dialogueArea';
import FileDrawer from '@/components/special/management/gptPage/fileDrawer';
import HistoryChatListDrawer from '@/components/special/management/gptPage/historyChatListDrawer';
import NodeRealTimeDetails from '@/components/special/management/gptPage/nodeRealTimeDetails';
import type { FileMap } from '@/interfaces/file';
import {
  requestAnalysisCreate,
  requestAnalysisList,
  requestAnalysisUserRelation,
} from '@/request/analysis';
import {
  requestV3ChatHeartbeat,
  requestV3CreateChat,
  requestV3GetChatInfo,
  requestV3GetChatMessages,
  requestV3GetSubTaskList,
  requestV3ListChats,
  requestV3SendMessage,
  requestV3UpdateChat,
} from '@/request/chat';
import { requestUploadFile } from '@/request/fileManagement';
import { requestNodeInfo } from '@/request/node';
import { Button, Result } from 'antd';
import { useEffect, useRef, useState } from 'react';
import { history } from 'umi';

export default function GptPage() {
  const [isRetry, setIsRetry] = useState<boolean>(false);
  const [chatList, setChatList] = useState<any[]>([]);
  const [chatId, setChatId] = useState<number>(null);
  const [chatInfo, setChatInfo] = useState<any>(null);
  const [originalSettings, setOriginalSettings] = useState<any>({ model: 'gpt-4o-mini' });
  const [currentNodeInfo, setCurrentNodeInfo] = useState<any>(null);
  const [messageList, setMessageList] = useState<any[]>([]);
  const [subTaskList, setSubTaskList] = useState<any[]>([]);
  const [showHistory, setShowHistory] = useState<boolean>(false);
  const [showTreeModal, setShowTreeModal] = useState<boolean>(false);
  const [showFileDrawer, setShowFileDrawer] = useState<boolean>(false);
  const [showImportModal, setShowImportModal] = useState<boolean>(false);
  const [privateAnalysisList, setPrivateAnalysisList] = useState<any[]>([]);
  const [loadingPrivateAnalyses, setLoadingPrivateAnalyses] = useState<boolean>(false);
  const [showShareModal, setShowShareModal] = useState<boolean>(false);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [attachedFiles, setAttachedFiles] = useState<any[]>([]);
  const [attachedFolder, setAttachedFolder] = useState<FileMap | null>(null);
  const [isUploadingFiles, setIsUploadingFiles] = useState<boolean>(false);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [retryMessage] = useState<string>('');
  const [chatNewestUpdatedTime, setChatNewestUpdatedTime] = useState<string | null>(null);
  const [heartbeatInterval, setHeartbeatInterval] = useState<NodeJS.Timeout | null>(null);

  const [focusedActionDetailsId, setFocusedActionDetailsId] = useState<any>(null);
  const [chatSwitchLoading, setChatSwitchLoading] = useState<boolean>(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState<boolean>(false);
  const [hasAccess, setHasAccess] = useState<boolean | null>(null);
  const [accessError, setAccessError] = useState<string | null>(null);
  const [isEditable, setIsEditable] = useState<boolean>(true);

  const loading = !!chatInfo && chatInfo?.status !== 'normal';
  const isLoadingChat = chatSwitchLoading || loading || isWaitingForResponse;

  // Use ref to store latest value for stable heartbeat function
  const chatNewestUpdatedTimeRef = useRef(chatNewestUpdatedTime);

  const loadHistoryChats = async () => {
    const response = await requestV3ListChats();
    if (response && response.data) {
      setChatList(response.data);
    }
  };

  const loadPrivateAnalyses = async () => {
    try {
      setLoadingPrivateAnalyses(true);
      const response = await requestAnalysisList();

      if (response && response.data) {
        const analyses = Array.isArray(response.data) ? response.data : [];
        setPrivateAnalysisList(analyses);
      }
    } catch (error) {
      console.error('Failed to load private analyses:', error);
      setPrivateAnalysisList([]);
    } finally {
      setLoadingPrivateAnalyses(false);
    }
  };

  const checkAnalysisAccess = async (analysisId: string) => {
    try {
      const { data: result } = await requestAnalysisUserRelation(analysisId);
      if (result && result.length > 0) {
        setHasAccess(true);
        setAccessError(null);

        const userPermission = result[0];
        const hasEditPermission =
          userPermission.permission === 'write' ||
          userPermission.permission === 'admin' ||
          userPermission.relation === 'belong-to';
        setIsEditable(hasEditPermission);
        return true;
      } else {
        setHasAccess(false);
        setAccessError('You do not have permission to access this chat.');
        setIsEditable(false);
        return false;
      }
    } catch (error: any) {
      console.error('Access check failed:', error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        setHasAccess(false);
        setAccessError(
          'You do not have permission to access this chat. Please request access from the owner.',
        );
      } else {
        setHasAccess(false);
        setAccessError('Unable to verify access permissions. Please try again later.');
      }
      setIsEditable(false);
      return false;
    }
  };

  useEffect(() => {
    loadHistoryChats();

    const urlParams = new URLSearchParams(window.location.search);
    const urlChatId = urlParams.get('chatId');
    if (urlChatId && !chatId) {
      setChatId(parseInt(urlChatId, 10));
    }
  }, []);

  useEffect(() => {
    const currentSearch = new URLSearchParams(window.location.search);
    if (chatId) {
      currentSearch.set('chatId', chatId.toString());
    } else {
      currentSearch.delete('chatId');
    }
    const newSearch = currentSearch.toString();
    const newUrl = newSearch
      ? `${window.location.pathname}?${newSearch}`
      : window.location.pathname;

    if (window.location.href !== `${window.location.origin}${newUrl}`) {
      history.replace(newUrl);
    }
  }, [chatId]);

  const loadChat = async (currentChatId, showLoading = true) => {
    try {
      if (showLoading) {
        setChatSwitchLoading(true);
      }

      const chatInfoResponse = await requestV3GetChatInfo(currentChatId);
      const analysisId = chatInfoResponse.data?.analysisId;

      if (analysisId) {
        const hasAccessToAnalysis = await checkAnalysisAccess(analysisId);
        if (!hasAccessToAnalysis) {
          return;
        }
      }

      const [messagesResponse, subTaskList] = await Promise.all([
        requestV3GetChatMessages(currentChatId, 50, 0),
        requestV3GetSubTaskList(currentChatId),
      ]);

      if (messagesResponse && messagesResponse.data && messagesResponse.data.messages) {
        const messages = messagesResponse.data.messages;
        setMessageList(messages);
        setChatInfo(chatInfoResponse.data);
        setSubTaskList(subTaskList?.data?.sub_tasks || []);
      }
    } catch (error: any) {
      console.error('Error loading chat:', error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        setHasAccess(false);
        setAccessError(
          'You do not have permission to access this chat. Please request access from the owner.',
        );
      } else {
        setAccessError('Unable to load chat. Please try again later.');
      }
    } finally {
      if (showLoading) {
        setChatSwitchLoading(false);
      }
    }
  };

  const loadCurrentNodeInfo = async (nodeId) => {
    if (!nodeId) {
      setCurrentNodeInfo(null);
      setAttachedFiles([]);
      setAttachedFolder(null);
      setSelectedFiles([]);
      return;
    }
    const response = await requestNodeInfo(nodeId);
    if (!!response) {
      setCurrentNodeInfo(response);
    } else {
      setCurrentNodeInfo(null);
      setAttachedFiles([]);
      setAttachedFolder(null);
      setSelectedFiles([]);
    }
  };

  const updateChatInfo = async (attrs: any) => {
    if (!chatId) return;
    const originalChatInfo = { ...chatInfo };
    setChatInfo({ ...chatInfo, ...attrs });
    const response = await requestV3UpdateChat(chatId, attrs);
    if (!response || response.code !== 200) {
      setChatInfo(originalChatInfo);
    }
  };

  const getChatbotMessage = async (
    chatId,
    msg: string,
    newMessageList: any,
    attachedFiles: any[] = [],
  ) => {
    if (!chatId) {
      console.error('Chat ID is not available');
      return;
    }

    try {
      setIsWaitingForResponse(true);

      // Send message to v3.0 chat API
      const response = await requestV3SendMessage(chatId, msg, attachedFiles);

      if (response && response.code === 200) {
        // Message sent successfully, heartbeat polling will automatically pick up the response
        setMessageList([...newMessageList]);
      } else {
        // Handle error response
        const errorMessage = {
          content: `Failed to send message: ${response?.message || 'Unknown error'}`,
          role: 'error',
          timestamp: new Date().toISOString(),
        };
        setMessageList([...newMessageList, errorMessage]);
        setIsWaitingForResponse(false);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        content: `Network error: ${error instanceof Error ? error.message : 'Please check your network connection'}`,
        role: 'error',
        timestamp: new Date().toISOString(),
      };
      setMessageList([...newMessageList, errorMessage]);
      setIsWaitingForResponse(false);
    } finally {
      setIsRetry(false);
    }
  };

  const handleFileAttach = (info: any) => {
    const { file } = info;
    if (file.status === 'done') {
      const fileToAdd = file.originFileObj || file;
      const newFile = {
        id: `${Date.now()}_${Math.random()}`,
        name: fileToAdd.name,
        size: fileToAdd.size,
        file: fileToAdd,
      };
      setAttachedFiles((prev) => [...prev, newFile]);
    }
  };

  const handleRemoveAttachedFile = (fileId: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const handleSendMessage = async () => {
    let _chatId = chatId;
    let _analysisId;
    if (!chatId) {
      const { data: newAnalysis } = await requestAnalysisCreate(
        'New Analysis from Chat',
        'A new analysis initiated from chat interface',
        'chatbot',
      );
      _analysisId = newAnalysis.id;
      const { data: newChat } = await requestV3CreateChat(
        newAnalysis.id,
        originalSettings?.model,
        null,
      );
      setChatId(newChat.id);
      _chatId = newChat.id;
    } else {
      const chatInfo = await requestV3GetChatInfo(_chatId);
      _analysisId = chatInfo.data.analysisId;
    }
    if (!inputMessage.trim()) return;

    try {
      setIsUploadingFiles(true);
      const uploadedFiles = [];
      for (const attachedFile of attachedFiles) {
        const uploadResult = await requestUploadFile(_analysisId, attachedFile.file);
        if (uploadResult && uploadResult.code === 200) {
          uploadedFiles.push(uploadResult.data.id);
        }
      }
      setIsUploadingFiles(false);

      const allAttachedFiles = [];
      if (attachedFolder) {
        const folderName = Object.keys(attachedFolder)[0];

        const folderS3Prefix = `v3-chat-workspace/${_analysisId}/${folderName}`;
        allAttachedFiles.push(folderS3Prefix);
      } else {
        allAttachedFiles.push(...uploadedFiles, ...selectedFiles);
      }
      const newMessageList = [...messageList, { content: inputMessage, role: 'user' }];
      setMessageList(newMessageList);
      getChatbotMessage(_chatId, inputMessage, newMessageList, allAttachedFiles);
      setInputMessage('');
      setAttachedFiles([]);
      setAttachedFolder(null);
      setSelectedFiles([]);
    } catch (error) {
      console.error('Error uploading files:', error);
      const newMessageList = [...messageList, { content: inputMessage, role: 'user' }];
      setMessageList(newMessageList);
      getChatbotMessage(_chatId, inputMessage, newMessageList);
      setInputMessage('');
    } finally {
      setIsUploadingFiles(false);
    }
  };

  const handleRetryMessage = async () => {
    if (!chatId || !retryMessage) return;
    const _chatId = chatId;
    setIsRetry(false);
    const filteredMessages = messageList.slice(0, -1);
    setMessageList(filteredMessages);
    getChatbotMessage(_chatId, retryMessage, filteredMessages);
  };

  const handleShareChat = () => {
    if (chatInfo?.analysisId) {
      setShowShareModal(true);
    }
  };

  // Update ref whenever chatNewestUpdatedTime changes
  useEffect(() => {
    chatNewestUpdatedTimeRef.current = chatNewestUpdatedTime;
  }, [chatNewestUpdatedTime]);

  useEffect(() => {
    loadCurrentNodeInfo(chatInfo?.currentNodeId);
  }, [chatInfo?.currentNodeId]);

  useEffect(() => {
    if (chatId) {
      setChatSwitchLoading(true);
    }

    setMessageList([]);
    setSubTaskList([]);
    setChatInfo(null);
    setCurrentNodeInfo(null);
    setAttachedFiles([]);
    setAttachedFolder(null);
    setSelectedFiles([]);
    setChatNewestUpdatedTime(null);
    setShowFileDrawer(false);
    setShowTreeModal(false);
    setIsWaitingForResponse(false);
    setHasAccess(null);
    setAccessError(null);
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      setHeartbeatInterval(null);
    }
    if (!chatId) {
      setChatSwitchLoading(false);
      return;
    }

    const initializeChat = async () => {
      try {
        await loadChat(chatId, false);
      } finally {
        setChatSwitchLoading(false);
      }
    };
    initializeChat();
  }, [chatId]);

  // Heart beat polling effect - only restarts when chatId changes
  useEffect(() => {
    if (!chatId) return;

    // Define heartbeat function inside useEffect using refs for latest values
    const performHeartbeat = async () => {
      const currentChatId = chatId; // Use closure chatId which is stable for this effect
      const currentNewestUpdatedTime = chatNewestUpdatedTimeRef.current; // Use ref for latest value

      if (!currentChatId) return;

      try {
        const response = await requestV3ChatHeartbeat(currentChatId, currentNewestUpdatedTime);
        if (response && response.data && response.data.updatedTime) {
          const heartbeatUpdatedTime = response.data.updatedTime;

          // Check if we need to update based on timestamp comparison
          // Update when: (local time is empty AND heartbeat time is not empty) OR (heartbeat time > local time)
          const shouldUpdate =
            (!currentNewestUpdatedTime && heartbeatUpdatedTime) ||
            (heartbeatUpdatedTime && heartbeatUpdatedTime > (currentNewestUpdatedTime || ''));

          if (shouldUpdate) {
            // Get messages and update
            await loadChat(currentChatId, false);
            setChatNewestUpdatedTime(heartbeatUpdatedTime);
            setIsWaitingForResponse(false);
          }
        }
      } catch (error) {
        console.error('Heartbeat error:', error);
      }
    };

    // Start heartbeat polling every 2.5 seconds
    const intervalId = setInterval(performHeartbeat, 2500);
    setHeartbeatInterval(intervalId);

    // Cleanup function to stop polling when component unmounts or chatId changes
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
      setHeartbeatInterval(null);
    };
  }, [chatId]); // Only depend on chatId to avoid frequent restarts

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
      }
    };
  }, []);

  if (hasAccess === false && accessError) {
    return (
      <div style={{ width: '100%', height: '99.8%', padding: '10px', backgroundColor: '#FDFEFF' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%',
            width: '85vw',
            margin: '0 auto',
          }}
        >
          <Result
            status="403"
            title="Access Denied"
            subTitle={accessError}
            extra={
              <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                <Button type="primary" onClick={() => history.push('/management/homeMain')}>
                  Back to Home
                </Button>
                <Button onClick={() => window.location.reload()}>Retry</Button>
              </div>
            }
          />
        </div>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '99.8%', padding: '10px', backgroundColor: '#FDFEFF' }}>
      <div
        style={{
          display: 'flex',
          height: '100%',
          gap: '20px',
          width: '85vw',
          minWidth: '1400px',
          margin: '0 auto',
        }}
      >
        <div
          style={{
            flex: 1,
            minWidth: '400px',
            background: '#FFFFFF',
            borderRadius: '12px',
            boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.08)',
            overflow: 'hidden',
          }}
        >
          <DialogueArea
            chatId={chatId}
            setChatId={setChatId}
            chatInfo={chatInfo}
            loading={isLoadingChat}
            currentNodeInfo={currentNodeInfo}
            setChatInfo={setChatInfo}
            originalSettings={originalSettings}
            setOriginalSettings={setOriginalSettings}
            messageList={messageList}
            inputMessage={inputMessage}
            setInputMessage={setInputMessage}
            handleFileAttach={handleFileAttach}
            handleRemoveAttachedFile={handleRemoveAttachedFile}
            handleSendMessage={handleSendMessage}
            handleRetryMessage={handleRetryMessage}
            attachedFiles={attachedFiles}
            setAttachedFiles={setAttachedFiles}
            attachedFolder={attachedFolder}
            setAttachedFolder={setAttachedFolder}
            isRetry={isRetry}
            setShowHistory={setShowHistory}
            setFocusedActionDetailsId={setFocusedActionDetailsId}
            selectedFiles={selectedFiles}
            isUploadingFiles={isUploadingFiles}
            privateAnalysisList={privateAnalysisList}
            loadPrivateAnalyses={loadPrivateAnalyses}
            loadingPrivateAnalyses={loadingPrivateAnalyses}
            showImportModal={showImportModal}
            setShowImportModal={setShowImportModal}
            onShareChat={handleShareChat}
            isEditable={isEditable}
          />
        </div>

        <div
          style={{
            flex: 1,
            minWidth: '400px',
            background: '#FFFFFF',
            borderRadius: '12px',
            boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.08)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-start',
          }}
        >
          <div
            style={{
              flex: 1,
              overflowY: 'hidden',
            }}
          >
            <ActionsResultArea
              setShowTreeModal={setShowTreeModal}
              setShowFileDrawer={setShowFileDrawer}
              subTaskList={subTaskList}
              chatInfo={chatInfo}
              focusedActionDetailsId={focusedActionDetailsId}
            />
          </div>
          <div
            style={{
              height: 'auto',
              borderTop: '1px solid #f0f0f0',
            }}
          >
            <NodeRealTimeDetails
              currentNodeInfo={currentNodeInfo}
              currentNodeId={chatInfo?.currentNodeId}
            />
          </div>
        </div>
        <AnalysisTree
          visible={showTreeModal}
          onClose={() => setShowTreeModal(false)}
          analysisId={chatInfo?.analysisId || null}
          selectedKeys={chatInfo?.currentNodeId ? [String(chatInfo.currentNodeId)] : []}
          onSelectKeys={([nodeId]) => {
            if (!!nodeId) {
              updateChatInfo({ current_node_id: Number(nodeId) });
            } else {
              updateChatInfo({ current_node_id: null });
            }
          }}
          isEditable={isEditable}
        />
        <FileDrawer
          visible={showFileDrawer}
          onClose={() => setShowFileDrawer(false)}
          selectedFiles={selectedFiles}
          onSelectFiles={setSelectedFiles}
          analysisId={chatInfo?.analysisId}
          attachedFolder={attachedFolder}
          isEditable={isEditable}
        />
        <HistoryChatListDrawer
          showHistory={showHistory}
          setShowHistory={setShowHistory}
          chatList={chatList}
          setChatId={setChatId}
        />
        <ChatShareModal
          analysisId={showShareModal ? chatInfo?.analysisId : null}
          chatId={chatId}
          setAnalysisId={(id) => setShowShareModal(!!id)}
          isEditable={isEditable}
        />
      </div>
    </div>
  );
}
