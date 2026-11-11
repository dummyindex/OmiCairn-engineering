import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { NodeType } from '@/constants/node';
import type { ChatMessage, ChatSession } from '@/services/chatbotService';
import chatbotService from '@/services/chatbotService';
import {
  ArrowUpOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  CloseOutlined,
  DatabaseOutlined,
  DownOutlined,
  FileOutlined,
  FileTextOutlined,
  FullscreenExitOutlined,
  FullscreenOutlined,
  LoadingOutlined,
  NodeIndexOutlined,
  PaperClipOutlined,
  PlusOutlined,
  UpOutlined,
} from '@ant-design/icons';
import type { UploadFile } from 'antd';
import { Button, Input, message } from 'antd';
import React, { useEffect, useRef, useState } from 'react';
import { useModel } from 'umi';
import ChatHistoryPanel from './chatHistoryPanel';
import SimpleNodeMap from './simpleNodeMap';

interface LocalChatMessage extends ChatMessage {
  files?: UploadFile[];
  chatContext?: string;
  // deepResearch?: boolean;
  importRecommendation?: {
    title: string;
    description: string;
    reason: string;
  }[];
  recommendedFunctionalities?: {
    id: string;
    name: string;
    description: string;
    category: string;
    relevance_score?: number;
  }[];
}

interface NodeTag {
  tag: string;
  id: any;
  startPos: number;
  endPos: number;
}

const ChatbotPanel: React.FC = () => {
  const { chatbotState, setChatbotState, chatContext, setChatContext } =
    useModel('visualPanelControl');
  const { currentSelectedNodes, findSubCompleteNode, instance, analysisId } = useModel('analysis');
  const { isGuest } = useModel('user');
  const [currentModel, setCurrentModel] = useState<string>('gpt4o-mini');
  const [showHistory, setShowHistory] = useState<boolean>(false);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatSession[]>([]);
  const [pipelineMapData, setPipelineMapData] = useState<any>(null);
  const [nodeTags, setNodeTags] = useState<NodeTag[]>([]);

  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // const [isDeepResearchActive, setIsDeepResearchActive] = useState<boolean>(false);
  const [userInput, setUserInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isInitializing, setIsInitializing] = useState<boolean>(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);
  const [isLoadingSession, setIsLoadingSession] = useState<boolean>(false);

  const getCategoryIcon = (category: string) => {
    const iconMap = {
      data: <DatabaseOutlined style={{ color: '#1890ff' }} />,
      ai: <NodeIndexOutlined style={{ color: '#722ed1' }} />,
      visualization: <BarChartOutlined style={{ color: '#fa8c16' }} />,
      analysis: <FileTextOutlined style={{ color: '#52c41a' }} />,
    };
    return iconMap[category] || <FileTextOutlined />;
  };

  const handleFunctionalityClick = (functionality: any) => {
    // Import quickLinks and execute the functionality
    import('@/utils/quickLinks').then(({ quickLinks }) => {
      quickLinks.executeQuickLink(functionality.id, analysisId || undefined, currentSelectedNodes);
    });
  };

  const [messages, setMessages] = useState<LocalChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const getChatbotPanelStyle = () => {
    if (!chatbotState.isVisible) return { display: 'none' };

    const baseStyle: React.CSSProperties = {
      display: 'flex',
      position: 'absolute',
      bottom: 0,
      left: 0,
      right: 0,
      background: '#fff',
      borderTop: '1px solid rgba(236, 236, 236, 1)',
      borderLeft: '1px solid rgba(236, 236, 236, 1)',
      borderTopLeftRadius: '10px',
      borderTopRightRadius: '10px',
      boxShadow: '0px 4px 16px 4px rgba(76, 123, 247, 0.3)',
      flexDirection: 'column',
      transition: 'all 0.3s ease',
    };

    switch (chatbotState.mode) {
      case 'minimized':
        return {
          ...baseStyle,
          height: '42px',
        };
      case 'expanded':
        return {
          ...baseStyle,
          height: '49vh',
        };
      case 'maximized':
        return {
          ...baseStyle,
          height: 'calc(95vh)',
        };
      default:
        return baseStyle;
    }
  };

  const initializeChatbot = async () => {
    try {
      setIsInitializing(true);
      const historyResponse = await chatbotService.getSessionHistory(analysisId);
      const history = (historyResponse as any).data || historyResponse;
      const historyArray = Array.isArray(history) ? history : [];
      setChatHistory(historyArray);

      if (historyArray.length > 0) {
        // Load the most recent session
        const mostRecentSession = historyArray[0];
        setCurrentSession(mostRecentSession);

        const messagesResponse = await chatbotService.getMessages(mostRecentSession.id);
        const sessionMessages = (messagesResponse as any).data || messagesResponse;
        const messagesArray = Array.isArray(sessionMessages) ? sessionMessages : [];
        setMessages(
          messagesArray.map((msg) => ({
            ...msg,
            files: msg.files || [],
            chatContext: 'analysis',
            // deepResearch: false
          })),
        );
        setCurrentModel('gpt4o-mini');
        setChatContext('analysis');
      }
    } catch (error) {
      console.error('Failed to initialize chatbot:', error);
    } finally {
      setIsInitializing(false);
    }
  };

  useEffect(() => {
    if (chatbotState.isVisible && analysisId && !currentSession && !isGuest()) {
      initializeChatbot();
    }
  }, [chatbotState.isVisible, analysisId, isGuest]);

  const loadChatHistory = async () => {
    if (!analysisId) return;

    try {
      setIsLoadingHistory(true);
      const historyResponse = await chatbotService.getSessionHistory(analysisId);
      const history = (historyResponse as any).data || historyResponse;
      setChatHistory(Array.isArray(history) ? history : []);
    } catch (error) {
      message.error('Failed to load chat history');
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const startNewChat = async () => {
    if (!analysisId || isGuest()) return null;

    try {
      setCurrentSession(null);
      setMessages([]);
      setUserInput('');
      setFileList([]);
      // setIsDeepResearchActive(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      setShowHistory(false);

      const defaultContext =
        currentSelectedNodes.length === 1
          ? currentSelectedNodes[0].type in [NodeType.DATA_NODE, NodeType.DATA_NODE_V2]
            ? 'pipeline'
            : 'node'
          : currentSelectedNodes.length > 1
          ? 'multinodes'
          : 'analysis';

      setChatContext(defaultContext);

      const sessionData = {
        title: `New Chat - ${new Date().toLocaleString()}`,
      };

      const response = await chatbotService.createSession(analysisId, sessionData);
      const newSession = (response as any).data || response;
      setCurrentSession(newSession);

      loadChatHistory();

      return newSession;
    } catch (error) {
      console.error('Failed to create new chat session:', error);
      message.error('Failed to create new chat session');
      return null;
    }
  };

  const toggleChatHistory = () => {
    if (!showHistory) {
      loadChatHistory();
    }
    setShowHistory(!showHistory);
  };

  const loadSelectedChat = async (sessionId: string) => {
    try {
      setIsLoadingSession(true);
      const session = chatHistory.find((s) => s.id === sessionId);
      if (session) {
        setCurrentSession(session);
        const messagesResponse = await chatbotService.getMessages(sessionId);
        const sessionMessages = (messagesResponse as any).data || messagesResponse;
        const messagesArray = Array.isArray(sessionMessages) ? sessionMessages : [];
        setMessages(
          messagesArray.map((msg) => ({
            ...msg,
            files: msg.files || [],
            chatContext: 'analysis',
            // deepResearch: false
          })),
        );
        setCurrentModel('gpt4o-mini');
        setChatContext('analysis');
      }
      setShowHistory(false);
    } catch (error) {
      message.error('Failed to load chat session');
    } finally {
      setIsLoadingSession(false);
    }
  };

  const toggleMaximize = () => {
    setChatbotState((prev) => ({
      ...prev,
      mode: prev.mode === 'maximized' ? 'expanded' : 'maximized',
    }));
  };

  const toggleMinimize = () => {
    setChatbotState((prev) => ({
      ...prev,
      mode: prev.mode === 'minimized' ? 'expanded' : 'minimized',
    }));
  };

  const handleContextChange = () => {
    if (currentSelectedNodes.length === 1) {
      if (currentSelectedNodes[0].type in [NodeType.DATA_NODE, NodeType.DATA_NODE_V2]) {
        setChatContext('pipeline');
        setPipelineMapData(findSubCompleteNode(currentSelectedNodes[0].id, instance));
      } else if (currentSelectedNodes[0].type === 'computation node') {
        setChatContext('node');
      }
    } else if (currentSelectedNodes.length > 1) {
      setChatContext('multinodes');
    }
  };

  useEffect(() => {
    if (chatbotState.isVisible) {
      if (currentSelectedNodes.length > 0) {
        handleContextChange();
      } else {
        setChatContext('analysis');
      }
    }
  }, [currentSelectedNodes]);

  const handleNodeClick = (node) => {
    const nodeTag = `#${node.data.label}`;
    const nodeId = node.id;

    setUserInput((prevInput) => {
      if (!prevInput.includes(nodeTag)) {
        const newInput = prevInput ? `${prevInput} ${nodeTag}` : nodeTag;

        setNodeTags((prev) => [
          ...prev,
          {
            tag: nodeTag,
            id: nodeId,
            startPos: newInput.indexOf(nodeTag),
            endPos: newInput.indexOf(nodeTag) + nodeTag.length,
          },
        ]);

        return newInput;
      }
      return prevInput;
    });
  };

  useEffect(() => {
    setNodeTags(
      (prev) =>
        prev
          .map((tagInfo) => {
            const newStartPos = userInput.indexOf(tagInfo.tag);
            if (newStartPos === -1) {
              return null;
            }
            return {
              ...tagInfo,
              startPos: newStartPos,
              endPos: newStartPos + tagInfo.tag.length,
            };
          })
          .filter(Boolean) as NodeTag[],
    );
  }, [userInput]);

  const handleFileUpload = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newFiles: UploadFile[] = Array.from(files).map((file, index) => ({
      uid: `-${fileList.length + index + 1}`,
      name: file.name,
      status: 'done',
      size: file.size,
      type: file.type,
      originFileObj: file as any,
    }));

    setFileList((prev) => [...prev, ...newFiles]);

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (uid: string) => {
    setFileList((prev) => prev.filter((file) => file.uid !== uid));
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // const toggleDeepResearch = () => {
  //   setIsDeepResearchActive(!isDeepResearchActive);
  // };

  const handleSend = async () => {
    if (userInput.trim() === '' && fileList.length === 0) return;
    if (isGuest()) return;

    let activeSession = currentSession;
    if (!activeSession) {
      try {
        activeSession = await startNewChat();
        if (!activeSession) {
          message.error('Failed to create chat session');
          return;
        }
      } catch (error) {
        message.error('Failed to create chat session');
        return;
      }
    }

    try {
      setIsLoading(true);

      let processedInput = userInput;
      let offset = 0;

      const sortedTags = [...nodeTags].sort((a, b) => a.startPos - b.startPos);

      sortedTags.forEach((tagInfo) => {
        const adjustedStartPos = tagInfo.startPos + offset;
        const adjustedEndPos = tagInfo.endPos + offset;
        const replacement = `#${tagInfo.id}`;

        processedInput =
          processedInput.substring(0, adjustedStartPos) +
          replacement +
          processedInput.substring(adjustedEndPos);

        offset += replacement.length - (tagInfo.endPos - tagInfo.startPos);
      });

      const userMessage: LocalChatMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: userInput,
        timestamp: Date.now(),
        files: fileList.length > 0 ? [...fileList] : undefined,
        model: currentModel,
        chatContext: chatContext,
        // deepResearch: isDeepResearchActive,
      };

      setMessages((prev) => [...prev, userMessage]);
      setUserInput('');
      setFileList([]);

      const requestData: any = {
        content: processedInput,
        files: fileList,
        model: currentModel,
        contextType: chatContext,
      };

      if (
        chatContext === 'pipeline' &&
        currentSelectedNodes.length === 1 &&
        currentSelectedNodes[0].type in [NodeType.DATA_NODE, NodeType.DATA_NODE_V2]
      ) {
        requestData.dataNodeId = currentSelectedNodes[0].id;
      } else if (chatContext === 'node' && currentSelectedNodes.length === 1) {
        requestData.nodeId = currentSelectedNodes[0].id;
      } else if (chatContext === 'multinodes' && currentSelectedNodes.length > 1) {
        requestData.nodeIds = currentSelectedNodes.map((node) => node.id);
      }
      const assistantResponse = await chatbotService.sendMessage(activeSession.id, requestData);

      const messageData = (assistantResponse as any).data || assistantResponse;
      const assistantMessage: LocalChatMessage = {
        ...messageData,
        files: [],
        chatContext: chatContext,
        // deepResearch: false,
        recommendedFunctionalities: messageData.recommendedFunctionalities || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      message.error('Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessages = () => {
    if (messages.length === 0) return null;

    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          paddingBottom: '4px',
          paddingRight: '5px',
        }}
      >
        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              alignItems: message.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                background: message.role === 'user' ? 'rgba(245, 246, 248, 1)' : 'transparent',
                color: 'black',
                padding: '8px',
                borderRadius: '12px',
                maxWidth: '97%',
                wordBreak: 'break-word',
                border: message.role === 'user' ? '1px solid #eaecf0' : 'none',
                fontSize: '14px',
                lineHeight: '22px',
                marginLeft: message.role === 'user' ? '25px' : '0',
              }}
            >
              {message.content}

              {message.files && message.files.length > 0 && (
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '4px',
                    marginTop: '4px',
                    maxWidth: '90%',
                    alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  {message.files.map((file) => (
                    <div
                      key={file.uid}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        background: '#F1F1F1',
                        padding: '4px 10px',
                        borderRadius: '12px',
                        fontSize: '13px',
                        border: '1px solid #e8e8e8',
                      }}
                    >
                      <FileOutlined style={{ fontSize: '14px', color: '#666' }} />
                      {file.name}
                    </div>
                  ))}
                </div>
              )}

              {message.importRecommendation && message.importRecommendation.length > 0 && (
                <div style={{ marginTop: '12px' }}>
                  {message.importRecommendation.map((dataset) => (
                    <div
                      key={dataset.title}
                      style={{
                        backgroundColor: 'rgba(240, 245, 255, 1)',
                        borderRadius: '10px',
                        padding: '8px 8px 12px 8px',
                        border: '1px solid rgba(240, 245, 255, 1)',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          marginBottom: '12px',
                          background: 'white',
                          border: '1px solid rgba(217, 217, 217, 1)',
                          borderRadius: '8px',
                          padding: '4px',
                          gap: '2px',
                        }}
                      >
                        <div
                          style={{
                            padding: '4px',
                            gap: '10px',
                          }}
                        >
                          <DatabaseOutlined style={{ fontSize: '16px' }} />
                        </div>
                        <div
                          style={{
                            fontWeight: 400,
                            fontSize: '14px',
                            lineHeight: '22px',
                            paddingTop: '1.5px',
                          }}
                        >
                          {dataset.title}
                        </div>
                      </div>

                      <div>
                        <div style={{ marginBottom: '8px' }}>
                          <div style={{ fontWeight: 550, fontSize: '13px', marginBottom: '4px' }}>
                            Description:
                          </div>
                          <div style={{ fontSize: '13px' }}>{dataset.description}</div>
                        </div>
                        <div>
                          <div style={{ fontWeight: 550, fontSize: '13px', marginBottom: '4px' }}>
                            Reason:
                          </div>
                          <div style={{ fontSize: '13px' }}>{dataset.reason}</div>
                        </div>
                      </div>

                      <div
                        style={{
                          marginTop: '12px',
                          display: 'flex',
                          justifyContent: 'flex-end',
                        }}
                      >
                        <Button
                          size="small"
                          style={{
                            backgroundColor: 'white',
                            borderColor: '#d9d9d9',
                            borderRadius: '4px',
                            fontSize: '13px',
                          }}
                          disabled
                        >
                          Import
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {message.recommendedFunctionalities &&
                message.recommendedFunctionalities.length > 0 && (
                  <div style={{ marginTop: '12px' }}>
                    <div
                      style={{
                        fontSize: '13px',
                        fontWeight: 500,
                        marginBottom: '8px',
                        color: '#666',
                      }}
                    >
                      💡 You might find these OmiCairn features helpful:
                    </div>
                    {message.recommendedFunctionalities.map((functionality) => (
                      <div
                        key={functionality.id}
                        style={{
                          backgroundColor: 'rgba(245, 249, 255, 1)',
                          borderRadius: '8px',
                          padding: '8px 12px',
                          border: '1px solid rgba(230, 238, 255, 1)',
                          marginBottom: '8px',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                        }}
                        onClick={() => handleFunctionalityClick(functionality)}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(240, 245, 255, 1)';
                          e.currentTarget.style.borderColor = 'rgba(64, 169, 255, 0.5)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(245, 249, 255, 1)';
                          e.currentTarget.style.borderColor = 'rgba(230, 238, 255, 1)';
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                          }}
                        >
                          <div style={{ fontSize: '14px' }}>
                            {getCategoryIcon(functionality.category)}
                          </div>
                          <div style={{ flex: 1 }}>
                            <div
                              style={{
                                fontWeight: 500,
                                fontSize: '13px',
                                color: '#1a1a1a',
                                marginBottom: '2px',
                              }}
                            >
                              {functionality.name}
                            </div>
                            <div
                              style={{
                                fontSize: '12px',
                                color: '#666',
                                lineHeight: '1.4',
                              }}
                            >
                              {functionality.description}
                            </div>
                          </div>
                          <div
                            style={{
                              fontSize: '11px',
                              color: '#999',
                              textTransform: 'uppercase',
                              fontWeight: 500,
                            }}
                          >
                            {functionality.category}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={getChatbotPanelStyle()}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '10px 8px 5px 10px',
          background: '#fff',
          zIndex: 5,
          position: 'sticky',
          top: 0,
          borderRadius: '10px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <CustomImage
            name={customIconNames.AIICONSTAR}
            style={{
              height: '15px',
              cursor: 'default',
              marginBottom: '2px',
            }}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontWeight: 500, cursor: 'default' }}>Chat</span>
            <span
              style={{
                display: 'flex',
                width: '100px',
                height: '22px',
                borderRadius: '17px',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 12px',
                gap: '4px',
                fontSize: '12px',
                cursor: 'default',
                border: '1px solid rgba(240, 240, 240, 1)',
              }}
            >
              GPT-4o-mini
            </span>
          </div>
        </div>

        <div style={{ display: 'flex' }}>
          <Button
            type="text"
            icon={<PlusOutlined />}
            size="small"
            onClick={startNewChat}
            disabled={isGuest()}
          />
          <Button
            type="text"
            icon={isLoadingHistory ? <LoadingOutlined /> : <ClockCircleOutlined />}
            size="small"
            onClick={toggleChatHistory}
            disabled={isLoadingHistory || isGuest()}
            style={{
              backgroundColor: showHistory ? '#dcedff' : 'transparent',
              borderRadius: '5px',
            }}
          />
          <Button
            type="text"
            icon={
              chatbotState.mode === 'maximized' ? (
                <FullscreenExitOutlined />
              ) : (
                <FullscreenOutlined />
              )
            }
            size="small"
            onClick={toggleMaximize}
          />
          <Button
            type="text"
            icon={
              chatbotState.mode === 'maximized' || chatbotState.mode === 'expanded' ? (
                <DownOutlined />
              ) : (
                <UpOutlined />
              )
            }
            size="small"
            onClick={toggleMinimize}
          />
        </div>
      </div>

      {chatbotState.mode !== 'minimized' && (
        <div
          style={{
            position: 'relative',
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflowY: 'auto',
          }}
        >
          <div
            style={{
              display: showHistory ? 'none' : 'flex',
              flexGrow: 1,
              padding: '10px',
              flexDirection: 'column',
              gap: '12px',
              overflowY: 'auto',
            }}
          >
            {!currentSession && !isInitializing && (
              <div
                style={{
                  textAlign: 'center',
                  padding: '40px 20px',
                  color: '#666',
                }}
              >
                {isGuest() ? (
                  <>
                    <div style={{ marginBottom: '16px', fontSize: '16px', fontWeight: 500 }}>
                      Chatbot Unavailable
                    </div>
                    <div style={{ marginBottom: '20px', fontSize: '14px' }}>
                      The Chatbot feature is not available for guest users. Please log in to access
                      this feature.
                    </div>
                    <Button
                      type="primary"
                      onClick={() => (window.location.href = '/login/byPassword')}
                    >
                      Login to Continue
                    </Button>
                  </>
                ) : (
                  <>
                    <div style={{ marginBottom: '16px', fontSize: '16px', fontWeight: 500 }}>
                      Welcome to Chatbot
                    </div>
                    <div style={{ marginBottom: '20px', fontSize: '14px' }}>
                      Start a new conversation to get help with your analysis
                    </div>
                    <Button type="primary" icon={<PlusOutlined />} onClick={startNewChat}>
                      Start New Chat
                    </Button>
                  </>
                )}
              </div>
            )}

            {isInitializing && (
              <div
                style={{
                  textAlign: 'center',
                  padding: '40px 20px',
                  color: '#666',
                }}
              >
                <div
                  style={{
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                  }}
                >
                  <LoadingOutlined style={{ color: '#1890ff' }} />
                  <span style={{ fontSize: '16px', fontWeight: 500 }}>Initializing Chat...</span>
                </div>
                <div style={{ fontSize: '14px' }}>Loading your previous conversations</div>
              </div>
            )}

            {currentSession && renderMessages()}

            {isLoading && currentSession && (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  alignItems: 'flex-start',
                  paddingBottom: '4px',
                  paddingRight: '5px',
                }}
              >
                <div
                  style={{
                    background: 'transparent',
                    color: 'black',
                    padding: '8px',
                    borderRadius: '12px',
                    maxWidth: '97%',
                    wordBreak: 'break-word',
                    border: 'none',
                    fontSize: '14px',
                    lineHeight: '22px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <LoadingOutlined style={{ color: '#1890ff' }} />
                  <span style={{ color: '#666', fontStyle: 'italic' }}>AI is thinking...</span>
                </div>
              </div>
            )}

            {currentSession && messages.length === 0 && !isLoading && (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: '15px',
                      fontWeight: 500,
                      padding: '6px 0 6px 8px',
                      cursor: 'default',
                    }}
                  >
                    {chatContext === 'analysis' && 'How can I help you today?'}
                    {chatContext === 'pipeline' &&
                      'What questions do you have about this pipeline?'}
                    {chatContext === 'node' && 'What questions do you have about this node?'}
                    {chatContext === 'multinodes' &&
                      'What questions do you have about these nodes?'}
                  </div>
                  {chatContext === 'pipeline' && pipelineMapData && (
                    <SimpleNodeMap
                      nodes={pipelineMapData}
                      onNodeClick={handleNodeClick}
                      chatContext={chatContext}
                    />
                  )}
                  {chatContext === 'multinodes' && currentSelectedNodes && (
                    <SimpleNodeMap
                      nodes={currentSelectedNodes}
                      onNodeClick={handleNodeClick}
                      chatContext={chatContext}
                    />
                  )}
                </div>
              </div>
            )}
          </div>

          {showHistory && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: '#fff',
                zIndex: 10,
              }}
            >
              <ChatHistoryPanel
                onClose={toggleChatHistory}
                onChatSelect={loadSelectedChat}
                chatHistory={chatHistory}
                isLoadingSession={isLoadingSession}
                onSessionDeleted={(sessionId) => {
                  setChatHistory((prev) => prev.filter((s) => s.id !== sessionId));
                  if (currentSession?.id === sessionId) {
                    setCurrentSession(null);
                    setMessages([]);
                  }
                }}
              />
            </div>
          )}
        </div>
      )}

      {chatbotState.mode !== 'minimized' && !showHistory && currentSession && !isGuest() && (
        <div
          style={{
            padding: '4px 12px',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {fileList.length > 0 && (
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '10px',
                margin: '4px 0 8px 0',
                maxHeight: '9vh',
                overflowY: 'auto',
              }}
            >
              {fileList.map((file) => (
                <div
                  key={file.uid}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '3px',
                    background: '#F1F1F1',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    border: '1px solid #e8e8e8',
                    maxWidth: '10vw',
                    width: '9vw',
                  }}
                >
                  <FileOutlined style={{ fontSize: '12px', color: '#666', flexShrink: 0 }} />
                  <span
                    style={{
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      flexGrow: 1,
                      cursor: 'default',
                    }}
                  >
                    {file.name}
                  </span>
                  <CloseOutlined
                    style={{ fontSize: '10px', cursor: 'pointer', color: '#666' }}
                    onClick={() => removeFile(file.uid)}
                  />
                </div>
              ))}
            </div>
          )}

          <div
            style={{
              backgroundColor: '#fff',
              position: 'sticky',
              bottom: 0,
              zIndex: 5,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                backgroundColor: '#f7f7f7',
                borderRadius: '8px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', cursor: 'default' }}>
                <span style={{ color: '#666', marginRight: '4px', fontSize: '12px' }}>Asking</span>
                {chatContext === 'analysis' && (
                  <span style={{ fontWeight: 500, fontSize: '14px' }}>Analysis</span>
                )}
                {chatContext === 'pipeline' && (
                  <div
                    style={{
                      maxWidth: '15vw',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    <span style={{ fontWeight: 500, fontSize: '14px' }}>
                      Pipeline {'>'} {currentSelectedNodes[0]?.data.label}
                    </span>
                  </div>
                )}
                {chatContext === 'node' && (
                  <div
                    style={{
                      maxWidth: '14vw',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    <span style={{ fontWeight: 500, fontSize: '14px' }}>
                      Node {'>'} {currentSelectedNodes[0]?.data.label}
                    </span>
                  </div>
                )}
                {chatContext === 'multinodes' && (
                  <div
                    style={{
                      maxWidth: '14vw',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    <span style={{ fontWeight: 500, fontSize: '14px' }}>Multiple Nodes</span>
                  </div>
                )}
              </div>
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-end',
                gap: '8px',
                marginBottom: '4px',
              }}
            >
              <div
                style={{
                  flex: 1,
                  borderRadius: '10px',
                  background: '#fff',
                  padding: '3px 8px',
                  display: 'flex',
                  flexDirection: 'column',
                  border: '1px solid rgb(111, 163, 219)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <Input.TextArea
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder="Ask AI anything..."
                    autoSize={{ minRows: 2, maxRows: 5 }}
                    style={{
                      border: 'none',
                      boxShadow: 'none',
                      resize: 'none',
                      padding: '3px 6px',
                      flex: 1,
                      backgroundColor: 'transparent',
                      overflowY: 'auto',
                    }}
                  />
                </div>

                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: '4px',
                  }}
                >
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <input
                      type="file"
                      ref={fileInputRef}
                      style={{ display: 'none' }}
                      onChange={handleFileChange}
                      multiple
                    />
                    <Button
                      shape="circle"
                      size="small"
                      icon={<PaperClipOutlined />}
                      type="text"
                      onClick={handleFileUpload}
                      style={{
                        border: '1px solid rgba(240, 240, 240, 1)',
                      }}
                    />
                    {/* <Button
                      shape="round"
                      type="text"
                      size="small"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        padding: '0 8px',
                        height: 'auto',
                        background: isDeepResearchActive ? '#f0f4ff' : 'transparent',
                        border: isDeepResearchActive
                          ? '1px solid rgba(240, 245, 255, 1)'
                          : '1px solid rgba(240, 240, 240, 1)',
                        borderRadius: '16px',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = isDeepResearchActive
                          ? '#e6eeff'
                          : '#f8f8f8';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = isDeepResearchActive
                          ? '#f0f4ff'
                          : 'transparent';
                      }}
                      onClick={toggleDeepResearch}
                    >
                      <span
                        style={{
                          color: isDeepResearchActive ? 'rgba(47, 84, 235, 1)' : 'black',
                          fontSize: '12px',
                          lineHeight: '20px',
                          fontWeight: 400,
                        }}
                      >
                        <GlobalOutlined /> Deep research
                      </span>
                    </Button> */}
                  </div>
                  <Button
                    type="text"
                    size="small"
                    shape="circle"
                    icon={
                      isLoading ? (
                        <LoadingOutlined style={{ color: 'white' }} />
                      ) : (
                        <ArrowUpOutlined style={{ color: 'white' }} />
                      )
                    }
                    style={{
                      background:
                        (userInput || fileList.length > 0) && !isLoading
                          ? 'linear-gradient(to right, rgba(136, 194, 255, 1) 0%, rgba(33, 73, 255, 1) 100%)'
                          : 'rgba(191, 191, 191, 1)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: 'none',
                    }}
                    onClick={handleSend}
                    disabled={isLoading || (userInput === '' && fileList.length === 0)}
                  />
                </div>

                <div
                  style={{
                    fontSize: '11px',
                    color: '#999',
                    marginTop: '4px',
                    textAlign: 'center',
                  }}
                >
                  Press Enter to send, Shift+Enter for new line
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatbotPanel;
