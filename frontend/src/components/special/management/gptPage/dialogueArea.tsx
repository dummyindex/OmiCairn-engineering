import type { FileMap } from '@/interfaces/file';
import { requestGetFigureInfo } from '@/request/attachedData';
import { requestV3CreateChat, requestV3UpdateChat } from '@/request/chat';
import Icon, {
  BugOutlined,
  CheckOutlined,
  CloudUploadOutlined,
  DeleteOutlined,
  FileOutlined,
  FolderOpenOutlined,
  HistoryOutlined,
  ImportOutlined,
  LoadingOutlined,
  PlusOutlined,
  ReloadOutlined,
  RightOutlined,
  SearchOutlined,
  SendOutlined,
  ShareAltOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { Button, Card, Divider, Input, message, Modal, Select, Spin, Tree } from 'antd';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import ReactMarkdown from 'react-markdown';
import { useModel } from 'umi';
import CurrentNodeInfoCard from './currentNodeInfoCard';
import SelectedFilesCard from './selectedFilesCard';
import ToolCallEntries from './toolCallEntries';
import WelcomeCard from './WelcomeCard';

const { Option } = Select;

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const convertFileMapToTreeData = (fileMap: FileMap | null, keyPrefix: string = ''): any[] => {
  if (!fileMap) return [];

  return Object.keys(fileMap).map((key) => {
    const fileItem = fileMap[key];
    const fullKey = keyPrefix ? `${keyPrefix}/${key}` : key;

    if (fileItem.type === 'folder') {
      return {
        title: (
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <FolderOpenOutlined style={{ marginRight: 8, color: '#1890ff', flexShrink: 0 }} />
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {key}
            </span>
          </div>
        ),
        key: fullKey,
        children: convertFileMapToTreeData(fileItem.children, fullKey),
      };
    } else {
      return {
        title: (
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <FileOutlined style={{ marginRight: 8, color: '#666', flexShrink: 0 }} />
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {key}
            </span>
          </div>
        ),
        key: fullKey,
        isLeaf: true,
      };
    }
  });
};

// Memoized component to prevent unnecessary re-renders
const ProcessedMarkdownContent = React.memo(
  ({ content, cacheKey }: { content: string; cacheKey: string }) => {
    const [processedContent, setProcessedContent] = useState<string>('');
    const [isProcessing, setIsProcessing] = useState(true);
    const [contentCache, setContentCache] = useState<Map<string, string>>(new Map());

    useEffect(() => {
      const processContent = async () => {
        // Check cache first
        if (contentCache.has(cacheKey)) {
          setProcessedContent(contentCache.get(cacheKey)!);
          setIsProcessing(false);
          return;
        }

        setIsProcessing(true);
        try {
          // Process figure references
          const figureRegex = /\[\[FIGURE:([a-fA-F0-9]{32}\.(png|jpg|jpeg|gif|svg|webp))\]\]/g;
          const matches = Array.from(content.matchAll(figureRegex));

          if (matches.length === 0) {
            setProcessedContent(content);
            setContentCache((prev) => new Map(prev.set(cacheKey, content)));
            return;
          }

          let processedContent = content;

          // Process each figure reference
          for (const match of matches) {
            const [fullMatch, figureUuid] = match;
            console.log('Processing figure:', figureUuid);

            try {
              // Get figure URL from the API
              const figureUrl = await requestGetFigureInfo(figureUuid);

              if (figureUrl) {
                // Replace [[FIGURE:{uuid}]] with ![figureuuid](url)
                const markdownImage = `![${figureUuid}](${figureUrl})`;
                processedContent = processedContent.replace(fullMatch, markdownImage);
              } else {
                // If no URL found, replace with a placeholder
                const placeholder = `![${figureUuid}](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2UgTm90IEZvdW5kPC90ZXh0Pjwvc3ZnPg==)`;
                processedContent = processedContent.replace(fullMatch, placeholder);
              }
            } catch (error) {
              console.error(`Failed to fetch figure ${figureUuid}:`, error);
              // Replace with error placeholder
              const errorPlaceholder = `![${figureUuid}](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2ZmZWJlZSIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEwIiBmaWxsPSIjZGMyNjI2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+RXJyb3IgTG9hZGluZzwvdGV4dD48L3N2Zz4=)`;
              processedContent = processedContent.replace(fullMatch, errorPlaceholder);
            }
          }

          setProcessedContent(processedContent);

          // Update cache
          setContentCache((prev) => new Map(prev.set(cacheKey, processedContent)));
        } catch (error) {
          console.error('Error processing content:', error);
          setProcessedContent(content); // Fallback to original content
        } finally {
          setIsProcessing(false);
        }
      };

      processContent();
    }, [content, cacheKey]);

    if (isProcessing) {
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#666' }}>
          <Spin size="small" />
          <span style={{ fontSize: '12px' }}>Processing images...</span>
        </div>
      );
    }

    return (
      <ReactMarkdown
        components={{
          p: ({ children }) => (
            <div style={{ margin: '8px 0', wordWrap: 'break-word' }}>{children}</div>
          ),
          br: () => <br />,
          code: ({ children }) => (
            <code style={{ wordWrap: 'break-word', whiteSpace: 'pre-wrap' }}>{children}</code>
          ),
          pre: ({ children }) => (
            <pre
              style={{
                wordWrap: 'break-word',
                whiteSpace: 'pre-wrap',
                overflowX: 'auto',
              }}
            >
              {children}
            </pre>
          ),
          img: ({ src, alt }) => (
            <img
              src={src}
              alt={alt}
              style={{
                maxWidth: '100%',
                height: 'auto',
                borderRadius: '4px',
                margin: '8px 0',
              }}
              onError={(e) => {
                // Handle image loading errors
                const target = e.target as HTMLImageElement;
                target.src =
                  'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2ZmZWJlZSIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEwIiBmaWxsPSIjZGMyNjI2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2UgRXJyb3I8L3RleHQ+PC9zdmc+';
              }}
            />
          ),
        }}
      >
        {processedContent}
      </ReactMarkdown>
    );
  },
);

// Define static styles outside component to prevent re-creation
const messageContainerStyle = { marginBottom: '16px' };
const assistantContentStyle = {
  flex: 1,
  background: '#f8f9fa',
  padding: '12px',
  borderRadius: '12px',
  maxWidth: '85%',
};
const toolContentStyle = {
  flex: 1,
  background: '#eff0f8ff',
  color: '#000',
  padding: '12px',
  borderRadius: '12px',
  marginRight: '12px',
  maxWidth: '70%',
};
const contentWrapperStyle = {
  maxWidth: '100%',
  wordWrap: 'break-word' as const,
  whiteSpace: 'pre-wrap' as const,
  overflowWrap: 'break-word' as const,
};

const UserAvatarSvg = () => (
  <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="40" height="40" rx="2" fill="#E8ECF9" />
    <g clipPath="url(#clip0_4017_3215)">
      <path
        d="M22.6406 13.625H24.1406V21.3203C24.1406 22.1745 23.9505 22.8854 23.5703 23.4531C23.1901 24.0208 22.6849 24.4479 22.0547 24.7344C21.4297 25.0156 20.75 25.1562 20.0156 25.1562C19.2448 25.1562 18.5469 25.0156 17.9219 24.7344C17.3021 24.4479 16.8099 24.0208 16.4453 23.4531C16.0859 22.8854 15.9062 22.1745 15.9062 21.3203V13.625H17.3984V21.3203C17.3984 21.9141 17.5078 22.4036 17.7266 22.7891C17.9453 23.1745 18.25 23.4609 18.6406 23.6484C19.0365 23.8359 19.4948 23.9297 20.0156 23.9297C20.5417 23.9297 21 23.8359 21.3906 23.6484C21.7865 23.4609 22.0938 23.1745 22.3125 22.7891C22.5312 22.4036 22.6406 21.9141 22.6406 21.3203V13.625Z"
        fill="#364578"
      />
    </g>
    <defs>
      <clipPath id="clip0_4017_3215">
        <rect width="40" height="40" fill="white" />
      </clipPath>
    </defs>
  </svg>
);

const AssistantAvatarSvg = () => (
  <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="40" height="40" rx="2" fill="#364578" />
    <rect x="11" y="14" width="18" height="14" rx="3" fill="white" />
    <rect x="19" y="9" width="2" height="5" fill="white" />
    <circle cx="16" cy="21" r="2" fill="#364578" />
    <circle cx="24" cy="21" r="2" fill="#364578" />
  </svg>
);

const UserAvatarIcon = (props: any) => <Icon component={UserAvatarSvg} {...props} />;
const AssistantAvatarIcon = (props: any) => <Icon component={AssistantAvatarSvg} {...props} />;

const loadingIcon = (
  <LoadingOutlined
    style={{
      fontSize: 24,
    }}
    spin
  />
);

const RecommendationCard = ({
  cardData,
}: {
  cardData: {
    title: string;
    description: string;
  };
}) => (
  <div
    style={{
      marginTop: '12px',
      padding: '12px',
      background: '#f8f9fa',
      borderRadius: '8px',
      border: '1px solid #e9ecef',
    }}
  >
    <div
      style={{
        fontSize: '13px',
        color: '#666',
        marginBottom: '8px',
        fontWeight: 'bold',
      }}
    >
      💡 Recommended Features
    </div>
    <div style={{ display: 'flex', justifyContent: 'center' }}>
      <Card
        size="small"
        hoverable
        style={{
          cursor: 'pointer',
          textAlign: 'center',
          minWidth: '200px',
          maxWidth: '300px',
          border: '1px solid #d6e4ff',
          background: '#f0f8ff',
        }}
      >
        <div style={{ fontSize: '12px', fontWeight: 'bold' }}>{cardData.title}</div>
        <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
          {cardData.description}
        </div>
      </Card>
    </div>
  </div>
);

const DialogueArea = ({
  chatId,
  setChatId,
  chatInfo,
  currentNodeInfo,
  setChatInfo,
  messageList,
  loading,
  inputMessage,
  setInputMessage,
  originalSettings,
  setOriginalSettings,
  handleSendMessage,
  isRetry,
  handleRetryMessage,
  setShowHistory,
  handleFileAttach,
  handleRemoveAttachedFile,
  attachedFiles,
  setAttachedFiles,
  attachedFolder,
  setAttachedFolder,
  setFocusedActionDetailsId,
  selectedFiles,
  isUploadingFiles,
  privateAnalysisList,
  loadPrivateAnalyses,
  loadingPrivateAnalyses,
  showImportModal,
  setShowImportModal,
  onShareChat,
  isEditable,
}) => {
  // Create a ref for the messages container
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { dictionary } = useModel('localization');

  // State for chat name editing
  const [isEditingName, setIsEditingName] = useState(false);
  const [editingName, setEditingName] = useState('');

  // State for IME composition (input-method editors)
  const [isComposing, setIsComposing] = useState(false);

  const [folderTreeData, setFolderTreeData] = useState<any[]>([]);

  // State for search functionality in import modal
  const [searchKey, setSearchKey] = useState<string>('');

  // State for import analysis loading
  const [loadingAnalysisId, setLoadingAnalysisId] = useState<string | null>(null);

  // Function to scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Auto scroll to bottom when messageList changes
  useEffect(() => {
    setTimeout(() => {
      scrollToBottom();
    }, 800);
  }, [messageList]);

  useEffect(() => {
    const newTreeData = convertFileMapToTreeData(attachedFolder);
    setFolderTreeData(newTreeData);
  }, [attachedFolder]);

  const switchModel = async (model: string) => {
    try {
      setOriginalSettings({ ...originalSettings, model });
      if (!chatId) return;
      await requestV3UpdateChat(chatId, { model });
      setChatInfo((prev: any) => ({
        ...prev,
        model,
      }));
    } catch (error) {
      console.error('Failed to switch model:', error);
    }
  };

  // Function to start editing chat name
  const startEditingName = () => {
    setEditingName(chatInfo?.name || '');
    setIsEditingName(true);
  };

  // Function to cancel editing
  const cancelEditingName = () => {
    setIsEditingName(false);
    setEditingName('');
  };

  // Function to submit chat name update
  const submitNameUpdate = async () => {
    const trimmedName = editingName.trim();

    if (!trimmedName) {
      message.error('Do not leave the chat name empty');
      return;
    }

    if (!chatId) {
      message.error('Invalid chat ID');
      return;
    }

    try {
      await requestV3UpdateChat(chatId, { name: trimmedName });
      setChatInfo((prev: any) => ({
        ...prev,
        name: trimmedName,
      }));
      setIsEditingName(false);
      setEditingName('');
      message.success('Successfully updated chat name');
    } catch (error) {
      console.error('Failed to update chat name:', error);
      message.error('Failed to update chat name');
    }
  };

  // Handle enter key press in name input
  const handleNameInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      submitNameUpdate();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEditingName();
    }
  };

  // Handle IME composition events
  const handleCompositionStart = () => {
    setIsComposing(true);
  };

  const handleCompositionEnd = () => {
    setIsComposing(false);
  };

  // Handle main input key down with IME support
  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    // Do not send the message while an IME is composing
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFolderUpload = (fileList: File[]) => {
    if (!fileList || fileList.length === 0) {
      setAttachedFolder(null);
      return;
    }

    const newFileMap: FileMap = {};
    let countedFiles = 0;

    fileList.forEach((file, index) => {
      if (!file) return;

      let filePath = '';
      if ((file as any).webkitRelativePath) {
        filePath = (file as any).webkitRelativePath as string;
      } else if (file.name) {
        filePath = file.name;
      } else {
        return;
      }

      const pathParts = filePath.split(/[\\/]/).filter((part) => part.length > 0);
      if (pathParts.length === 0) return;

      let currentLevel = newFileMap;

      for (let i = 0; i < pathParts.length - 1; i++) {
        const folderName = pathParts[i];
        if (!currentLevel[folderName]) {
          currentLevel[folderName] = {
            type: 'folder',
            file: null,
            children: {},
          };
        }
        currentLevel = currentLevel[folderName].children!;
      }

      const fileName = pathParts[pathParts.length - 1];
      currentLevel[fileName] = {
        type: 'file',
        file: file,
        children: null,
      };
      countedFiles += 1;

      const fileInfo = {
        file: {
          uid: `${Date.now()}-${index}`,
          name: file.name,
          status: 'done',
          originFileObj: file,
        },
      };
      handleFileAttach(fileInfo);
    });

    setAttachedFolder(newFileMap);

    message.success(`Successfully selected folder with ${countedFiles} files`);
  };

  const handleRemoveFolderAttachment = () => {
    setAttachedFolder(null);
    setAttachedFiles([]);
  };

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        if (attachedFolder) {
          message.warning('Please remove the attached folder first before attaching files');
          return;
        }

        acceptedFiles.forEach((file, index) => {
          const fileInfo = {
            file: {
              uid: `${Date.now()}-${index}`,
              name: file.name,
              status: 'done',
              originFileObj: file,
            },
          };
          handleFileAttach(fileInfo);
        });
      }
    },
    [handleFileAttach, attachedFolder],
  );

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    multiple: true,
    noClick: false,
    onDragEnter: undefined,
    onDragLeave: undefined,
    onDragOver: undefined,
    disabled: !isEditable,
  });

  // Function to render tool calls within messages

  const chatbotPrompts = [
    dictionary.I_NEED_DATA,
    dictionary.GENERATE_PREPROCESSING_WORKFLOW,
    dictionary.FIX_FUNCTION_BLOCK,
    dictionary.GENERATE_ANALYSIS_REPORT,
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '20px' }}>
      <div style={{ display: 'flex', gap: '16px', marginBottom: '15px', alignItems: 'stretch' }}>
        <div style={{ flex: 1 }}>
          <CurrentNodeInfoCard currentNodeInfo={currentNodeInfo} />
        </div>
        <div style={{ flex: 1 }}>
          <SelectedFilesCard selectedFiles={selectedFiles || []} />
        </div>
      </div>

      <div
        style={{
          marginBottom: '15px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        {chatInfo?.name ? (
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {isEditingName ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Input
                  value={editingName}
                  onChange={(e) => setEditingName(e.target.value)}
                  onKeyDown={handleNameInputKeyDown}
                  onBlur={cancelEditingName}
                  autoFocus
                  style={{
                    fontSize: '15px',
                    width: '150px',
                    height: '25px',
                  }}
                  placeholder="Enter chat name"
                />
                <Button
                  type="text"
                  size="small"
                  icon={<CheckOutlined />}
                  onClick={submitNameUpdate}
                  style={{
                    color: '#52c41a',
                    padding: '4px',
                  }}
                />
              </div>
            ) : (
              <>
                <span
                  onClick={isEditable ? startEditingName : undefined}
                  style={{
                    margin: 0,
                    color: '#333',
                    fontSize: '15px',
                    cursor: isEditable ? 'pointer' : 'default',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    border: '1px dashed transparent',
                    transition: isEditable ? 'all 0.2s ease' : 'none',
                  }}
                  onMouseEnter={
                    isEditable
                      ? (e) => {
                          const target = e.target as HTMLElement;
                          target.style.backgroundColor = '#f5f5f5';
                          target.style.borderColor = '#d9d9d9';
                        }
                      : undefined
                  }
                  onMouseLeave={
                    isEditable
                      ? (e) => {
                          const target = e.target as HTMLElement;
                          target.style.backgroundColor = 'transparent';
                          target.style.borderColor = 'transparent';
                        }
                      : undefined
                  }
                  title={isEditable ? 'Click to edit analysis name' : undefined}
                >
                  {chatInfo.name}
                </span>
                <Button
                  type="text"
                  onClick={() =>
                    window.open(
                      `/analysisPanel/flowPanel?analysis-id=${chatInfo?.analysisId}`,
                      '_blank',
                    )
                  }
                  style={{
                    color: '#5974CE',
                    fontSize: '12px',
                    padding: '4px',
                    height: 'auto',
                  }}
                >
                  <RightOutlined style={{ color: '#5974CE', marginRight: '-4px' }} /> View Analysis
                </Button>
              </>
            )}
          </div>
        ) : (
          <h3 style={{ margin: 0, color: '#333' }}>ChatBot</h3>
        )}
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            icon={<HistoryOutlined />}
            type="text"
            style={{ color: '#5974CE' }}
            onClick={() => setShowHistory(true)}
          >
            Chat History
          </Button>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Button
              icon={<PlusOutlined />}
              type="text"
              style={{ color: '#5974CE', marginRight: '-8px' }}
              onClick={() => setChatId(null)}
            >
              New Chat
            </Button>
            <Divider type="vertical" style={{ height: '20px' }} />
            <Button
              icon={<ImportOutlined />}
              type="text"
              style={{ color: '#5974CE', marginLeft: '-8px', marginRight: '-8px' }}
              onClick={() => {
                loadPrivateAnalyses();
                setShowImportModal(true);
              }}
            >
              Import
            </Button>
            <Divider type="vertical" style={{ height: '20px' }} />
            <Button
              icon={<ShareAltOutlined />}
              type="text"
              style={{ color: '#5974CE', marginLeft: '-8px' }}
              onClick={() => onShareChat && onShareChat()}
              disabled={!chatId || !chatInfo}
            >
              Share
            </Button>
          </div>
        </div>
      </div>

      <div
        style={{
          flex: 1,
          marginBottom: '20px',
          overflow: 'auto',
          border: '1px solid #e8e8e8',
          borderRadius: '8px',
          padding: '16px',
        }}
      >
        {chatId && (!chatInfo || messageList.length === 0) && loading ? (
          <div
            style={{
              textAlign: 'center',
              padding: '60px 20px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <span style={{ color: '#666', fontSize: '14px' }}>Loading chat...</span>
          </div>
        ) : messageList.length === 0 ? (
          <WelcomeCard />
        ) : (
          <>
            {messageList.map((item: any, index: number) => {
              const messageRole = item.role || item.type;
              // Use stable key based on message ID or index and role
              const messageKey = item.id ? `${item.id}-${messageRole}` : `${index}-${messageRole}`;

              if (messageRole === 'assistant') {
                return (
                  <div key={messageKey} style={messageContainerStyle}>
                    <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                      <AssistantAvatarIcon style={{ marginRight: '12px', flexShrink: 0 }} />
                      <div style={assistantContentStyle}>
                        <>
                          <div style={contentWrapperStyle}>
                            <ProcessedMarkdownContent
                              content={item.content}
                              cacheKey={`assistant-${item.id || index}`}
                            />
                          </div>
                          {item.hasRecommendation && (
                            <RecommendationCard cardData={item.recommendation} />
                          )}
                          {/* Display tool calls if present */}
                          {item.toolCalls && (
                            <ToolCallEntries
                              chatId={chatId}
                              toolCalls={item.toolCalls}
                              showCallButton={index === messageList.length - 1 && !loading}
                            />
                          )}
                        </>
                      </div>
                    </div>
                  </div>
                );
              } else if (messageRole === 'user') {
                return (
                  <div key={messageKey} style={messageContainerStyle}>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        justifyContent: 'flex-end',
                      }}
                    >
                      <div
                        style={{
                          flex: 1,
                          background: '#e6f7ff',
                          padding: '12px',
                          borderRadius: '12px',
                          marginRight: '12px',
                          maxWidth: '85%',
                        }}
                      >
                        <div style={contentWrapperStyle}>{item.content}</div>
                        {(() => {
                          let fileKeys = item.attachedFileS3Keys;
                          if (typeof fileKeys === 'string') {
                            try {
                              fileKeys = JSON.parse(fileKeys);
                            } catch (e) {
                              fileKeys = [];
                            }
                          }
                          if (!Array.isArray(fileKeys)) {
                            fileKeys = [];
                          }

                          const parseFileName = (objectKey: string): string => {
                            const fileName = objectKey.split('/').pop() || objectKey;
                            return fileName;
                          };

                          return fileKeys.length > 0 ? (
                            <div
                              style={{
                                marginTop: '12px',
                                padding: '8px 12px',
                                background: 'rgba(22, 119, 255, 0.05)',
                                border: '1px solid rgba(22, 119, 255, 0.15)',
                                borderRadius: '8px',
                              }}
                            >
                              <div
                                style={{
                                  fontSize: '12px',
                                  fontWeight: '500',
                                  marginBottom: '6px',
                                  display: 'flex',
                                  alignItems: 'center',
                                }}
                              >
                                <CloudUploadOutlined
                                  style={{ marginRight: '6px', fontSize: '14px' }}
                                />
                                Attachments
                              </div>
                              <div
                                style={{
                                  display: 'flex',
                                  flexDirection: 'column',
                                  gap: '4px',
                                }}
                              >
                                {fileKeys.map((fileKey: string, idx: number) => {
                                  const fileName = parseFileName(fileKey);
                                  return (
                                    <div
                                      key={idx}
                                      style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        padding: '6px 8px',
                                        background: '#ffffff',
                                        border: '1px solid #e8f4fd',
                                        borderRadius: '6px',
                                        fontSize: '12px',
                                        color: '#434343',
                                        cursor: 'default',
                                        transition: 'all 0.2s ease',
                                      }}
                                      title={`File: ${fileName}`}
                                    >
                                      <span style={{ fontWeight: '500' }}>{fileName}</span>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          ) : null;
                        })()}
                      </div>
                      <UserAvatarIcon style={{ flexShrink: 0 }} />
                    </div>
                  </div>
                );
              } else if (messageRole === 'tool') {
                return (
                  <div key={messageKey} style={messageContainerStyle}>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        justifyContent: 'flex-end',
                      }}
                    >
                      <div style={toolContentStyle}>
                        <span>
                          <b>Invoke Tool:</b>
                        </span>{' '}
                        <span>{item.toolName}</span>
                        <Button
                          type="link"
                          onClick={() => {
                            setFocusedActionDetailsId(item.toolCallId);
                          }}
                        >
                          <u>Show Details</u>
                        </Button>
                      </div>
                      <UserAvatarIcon style={{ flexShrink: 0 }} />
                    </div>
                  </div>
                );
              } else if (messageRole === 'error') {
                return (
                  <div key={messageKey} style={messageContainerStyle}>
                    <div
                      style={{
                        padding: '12px',
                        background: '#fff2f0',
                        border: '1px solid #ffccc7',
                        borderRadius: '8px',
                        color: '#cf1322',
                      }}
                    >
                      <BugOutlined style={{ marginRight: '8px' }} />
                      {item.content}
                    </div>
                  </div>
                );
              }
            })}

            {/* Scroll to bottom element */}
            <div ref={messagesEndRef} />

            {messageList.length > 0 && (
              <div
                style={{
                  marginTop: '20px',
                  padding: '16px',
                  background: '#fafafa',
                  borderRadius: '8px',
                  border: '1px dashed #d9d9d9',
                }}
              >
                <div style={{ marginBottom: '12px', color: '#666', fontSize: '14px' }}>
                  {dictionary.CONTINUE_CONVERSATION}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {chatbotPrompts.map((prompt: string, index: number) => (
                    <div
                      key={index}
                      style={{
                        padding: '6px 12px',
                        background: '#fff',
                        border: '1px solid #e8e8e8',
                        borderRadius: '16px',
                        cursor: 'pointer',
                        fontSize: '12px',
                      }}
                      onClick={() => setInputMessage(prompt)}
                    >
                      {prompt}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
        {loading && messageList.length > 0 && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin indicator={loadingIcon} />
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
              Generating response...
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Select
            value={chatId ? chatInfo?.model : originalSettings?.model}
            onChange={(value: string) => switchModel(value)}
            style={{ width: '140px' }}
            size="small"
            disabled={loading || !isEditable}
          >
            <Option value="gpt-5">GPT-5</Option>
            <Option value="gpt-5-mini">GPT-5-mini</Option>
            <Option value="gpt-5-nano">GPT-5-nano</Option>
            <Option value="gpt-4o">GPT-4o</Option>
            <Option value="gpt-4o-mini">GPT-4o-mini</Option>
            <Option value="gpt-4o-search-preview">GPT-4o-search-preview</Option>
            <Option value="gpt-4o-mini-search-preview">GPT-4o-mini-search-preview</Option>
            <Option value="gpt-5.1">GPT-5.1</Option>
            <Option value="gpt-5.2">GPT-5.2</Option>
          </Select>
          <div
            {...getRootProps()}
            style={{
              display: 'inline-block',
              cursor: 'pointer',
            }}
          >
            <input {...(getInputProps() as React.InputHTMLAttributes<HTMLInputElement>)} />
            <Button
              icon={<UploadOutlined />}
              size="small"
              style={{ borderColor: '#5974CE', color: '#5974CE' }}
              disabled={!!attachedFolder || !isEditable}
            >
              Attach Files
            </Button>
          </div>
          <Button
            icon={<FolderOpenOutlined />}
            size="small"
            style={{ borderColor: '#5974CE', color: '#5974CE' }}
            disabled={attachedFiles.length > 0 || selectedFiles.length > 0 || !isEditable}
            onClick={() => {
              if (attachedFiles.length > 0 || selectedFiles.length > 0) {
                message.warning('Please remove attached files first before attaching a folder');
                return;
              }

              const input = document.createElement('input');
              input.type = 'file';
              input.webkitdirectory = true;
              input.multiple = true;
              input.onchange = (e: any) => {
                const files = Array.from(e.target.files || []);
                if (files.length > 0) {
                  handleFolderUpload(files as File[]);
                }
              };
              input.click();
            }}
          >
            Attach Folder
          </Button>
          {(attachedFiles.length > 0 || selectedFiles.length > 0 || attachedFolder) && (
            <span style={{ fontSize: '12px', color: '#5974CE' }}>
              {attachedFiles.length > 0 &&
                `${attachedFiles.length} file${attachedFiles.length !== 1 ? 's' : ''} to upload`}
              {attachedFiles.length > 0 && selectedFiles.length > 0 && ' • '}
              {selectedFiles.length > 0 &&
                `${selectedFiles.length} workspace file${
                  selectedFiles.length !== 1 ? 's' : ''
                } selected`}
              {isUploadingFiles && (
                <Spin
                  size="default"
                  indicator={
                    <LoadingOutlined
                      style={{ fontSize: 14, color: '#5974CE', marginLeft: 8 }}
                      spin
                    />
                  }
                />
              )}
            </span>
          )}
        </div>

        {attachedFiles.length > 0 && !attachedFolder && (
          <div
            style={{
              padding: '12px',
              background: '#f8f9fa',
              border: '1px solid #e9ecef',
              borderRadius: '8px',
              marginBottom: '12px',
            }}
          >
            <div
              style={{
                fontSize: '12px',
                color: '#8c8c8c',
                marginBottom: '8px',
                fontWeight: '500',
              }}
            >
              Files to be sent with message:
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {attachedFiles.map((file: any) => (
                <div
                  key={file.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '6px 8px',
                    background: '#fff',
                    border: '1px solid #e1e5e9',
                    borderRadius: '6px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                    <FileOutlined style={{ color: '#5974CE', fontSize: '14px' }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '12px', fontWeight: '500', color: '#262626' }}>
                        {file.name}
                      </div>
                      <div style={{ fontSize: '11px', color: '#8c8c8c' }}>
                        {formatFileSize(file.size)}
                      </div>
                    </div>
                  </div>
                  <Button
                    size="small"
                    type="text"
                    icon={<DeleteOutlined />}
                    onClick={() => handleRemoveAttachedFile(file.id)}
                    style={{
                      color: '#ff4d4f',
                      padding: '4px',
                      minWidth: 'auto',
                      height: 'auto',
                    }}
                    title="Remove file"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {attachedFolder && folderTreeData.length > 0 && (
          <div
            style={{
              padding: '12px',
              background: '#f0f8ff',
              border: '1px solid #d6e4ff',
              borderRadius: '8px',
              marginBottom: '12px',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '8px',
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  color: '#1890ff',
                  fontWeight: '500',
                }}
              >
                Folder Structure:
              </div>
              <Button
                size="small"
                type="text"
                icon={<DeleteOutlined />}
                onClick={handleRemoveFolderAttachment}
                style={{
                  color: '#ff4d4f',
                  padding: '4px',
                  minWidth: 'auto',
                  height: 'auto',
                }}
                title="Remove folder"
              />
            </div>
            <div
              style={{
                maxHeight: '200px',
                overflow: 'auto',
                border: '1px solid #e8f4fd',
                borderRadius: '4px',
                padding: '8px',
                background: '#fff',
              }}
            >
              <Tree
                showLine
                defaultExpandAll
                treeData={folderTreeData}
                style={{ fontSize: '12px' }}
              />
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: '8px' }}>
          {isRetry && (
            <Button
              type="default"
              icon={<ReloadOutlined />}
              onClick={handleRetryMessage}
              style={{ borderColor: '#5974CE', color: '#5974CE' }}
            >
              Regenerate
            </Button>
          )}
          <Input
            placeholder={
              isEditable
                ? 'Input your message here...'
                : 'Read-only mode - you cannot send messages'
            }
            value={inputMessage}
            onChange={(e: any) => setInputMessage(e.target.value)}
            onKeyDown={handleInputKeyDown}
            onCompositionStart={handleCompositionStart}
            onCompositionEnd={handleCompositionEnd}
            disabled={loading || !isEditable}
            style={{ flex: 1, borderRadius: '20px' }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendMessage}
            loading={isUploadingFiles}
            disabled={!inputMessage.trim() || loading || loadingPrivateAnalyses || !isEditable}
            style={{ borderRadius: '20px' }}
          />
        </div>
      </div>

      <Modal
        title="Import from Existing Analysis"
        open={showImportModal}
        onCancel={() => {
          if (loadingAnalysisId || loadingPrivateAnalyses) return; // Prevent closing while loading
          setShowImportModal(false);
          setSearchKey('');
          setLoadingAnalysisId(null);
        }}
        footer={null}
        width={600}
        closable={!loadingAnalysisId && !loadingPrivateAnalyses}
        maskClosable={!loadingAnalysisId && !loadingPrivateAnalyses}
      >
        <div style={{ marginBottom: '16px' }}>
          <Input
            placeholder="Search analyses by name"
            allowClear
            value={searchKey}
            onChange={(e) => setSearchKey(e.target.value)}
            suffix={<SearchOutlined />}
            disabled={!!loadingAnalysisId || loadingPrivateAnalyses}
          />
        </div>
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {(() => {
            if (loadingPrivateAnalyses) {
              return (
                <div
                  style={{
                    textAlign: 'center',
                    padding: '40px 20px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '12px',
                  }}
                >
                  <Spin indicator={loadingIcon} />
                  <span style={{ color: '#666', fontSize: '14px' }}>Loading analyses...</span>
                </div>
              );
            }

            const filteredAnalyses = privateAnalysisList
              .filter((analysis: any) => analysis.permission === 'admin')
              .filter((analysis: any) => {
                if (!searchKey) return true;
                const analysisName = analysis.name || 'Untitled Analysis';
                return analysisName.toLowerCase().includes(searchKey.toLowerCase());
              });

            return filteredAnalyses.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
                {searchKey
                  ? 'No analyses found matching your search'
                  : 'No analyses available for import'}
              </div>
            ) : (
              filteredAnalyses.map((analysis: any) => (
                <Card
                  key={analysis.id}
                  size="small"
                  hoverable={loadingAnalysisId !== analysis.id}
                  style={{
                    margin: '12px',
                    border:
                      loadingAnalysisId === analysis.id ? '1px solid #1890ff' : '1px solid #e8e8e8',
                    cursor: loadingAnalysisId ? 'not-allowed' : 'pointer',
                    opacity: loadingAnalysisId && loadingAnalysisId !== analysis.id ? 0.5 : 1,
                    backgroundColor: loadingAnalysisId === analysis.id ? '#f6ffed' : 'white',
                  }}
                  onClick={async () => {
                    if (loadingAnalysisId) return;

                    try {
                      setLoadingAnalysisId(analysis.id);
                      const { data: newChat } = await requestV3CreateChat(
                        analysis.id,
                        originalSettings?.model || 'gpt-4o',
                        null,
                      );

                      setChatId(newChat.id);
                      setShowImportModal(false);
                      setSearchKey('');
                      setLoadingAnalysisId(null);
                      message.success('Chat created successfully');
                    } catch (error) {
                      console.error('Failed to create new chat from analysis:', error);
                      message.error('Failed to create new chat from analysis');
                      setLoadingAnalysisId(null);
                    }
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '14px', fontWeight: '500', marginBottom: '4px' }}>
                        {analysis.name || 'Untitled Analysis'}
                      </div>
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                        {analysis.createdTime || 'No creation time info'}
                      </div>
                      <div style={{ fontSize: '11px', color: '#999' }}>
                        {analysis.latestVisitTime && (
                          <span>
                            Last visited: {new Date(analysis.latestVisitTime).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    {loadingAnalysisId === analysis.id && (
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          marginLeft: '12px',
                        }}
                      >
                        <Spin size="small" />
                        <span style={{ fontSize: '12px', color: '#1890ff' }}>Creating...</span>
                      </div>
                    )}
                  </div>
                </Card>
              ))
            );
          })()}
        </div>
      </Modal>
    </div>
  );
};

export default DialogueArea;
