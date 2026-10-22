import { useState } from 'react';

const useAIUI = () => {
  const POSITION_OFFSET_X = -window.innerWidth * (1 / 20);
  const POSITION_OFFSET_Y = -window.innerHeight * (1 / 20);

  const [chatbotVisible, setChatbotVisible] = useState<boolean>(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [aiAssistantButtonPosition, setAiAssistantButtonPosition] = useState({
    x: POSITION_OFFSET_X,
    y: POSITION_OFFSET_Y,
  });
  const [aiAssistantPosition, setAiAssistantPosition] = useState({
    x: POSITION_OFFSET_X,
    y: POSITION_OFFSET_Y,
  });
  const [chatbotMaximized, setChatbotMaximized] = useState<boolean>(false);

  return {
    chatbotVisible,
    setChatbotVisible,
    selectedNodeId,
    setSelectedNodeId,
    aiAssistantButtonPosition,
    setAiAssistantButtonPosition,
    aiAssistantPosition,
    setAiAssistantPosition,
    chatbotMaximized,
    setChatbotMaximized,
  };
};

export default useAIUI;
