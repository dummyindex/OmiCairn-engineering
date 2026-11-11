export const ChatbotVersion = {
  SIMPLE: 'simple',
  COMPLEX: 'complex',
};

export const LLMModel = {
  GPT_4O_MINI: 'gpt-4o-mini',
  GPT_4O: 'gpt-4o',
  GPT_4O_MINI_SEARCH_REVIEW: 'gpt-4o-mini-search-preview',
  GPT_4O_SEARCH_REVIEW: 'gpt-4o-search-preview',
  GPT_5: 'gpt-5',
  GPT_5_MINI: 'gpt-5-mini',
  GPT_5_NANO: 'gpt-5-nano',
  GPT_5__1: 'gpt-5.1',
  GPT_5__2: 'gpt-5.2',
};

export const ClaudeModel = {
  SONNET_4_5: 'claude-sonnet-4-5-20250929',
  OPUS_4_5: 'claude-opus-4-5-20251101',
  HAIKU_4_5: 'claude-haiku-4-5-20251001',
};

export const ClaudeModelList = [
  {
    id: 'claude-sonnet-4-5-20250929',
    label: 'Claude Sonnet 4.5',
    value: ClaudeModel.SONNET_4_5,
  },
  {
    id: 'claude-opus-4-5-20251101',
    label: 'Claude Opus 4.5',
    value: ClaudeModel.OPUS_4_5,
  },
  {
    id: 'claude-haiku-4-5-20251001',
    label: 'Claude Haiku 4.5',
    value: ClaudeModel.HAIKU_4_5,
  },
];

export const LLMModelList = [
  {
    id: 'gpt-4o-mini',
    label: 'GPT-4o Mini',
    value: LLMModel.GPT_4O_MINI,
    description: 'A smaller, faster version of GPT-4, optimized for quick responses.',
  },
  {
    id: 'gpt-4o-mini-search-preview',
    label: 'GPT-4o Mini Search Review',
    value: LLMModel.GPT_4O_MINI_SEARCH_REVIEW,
    description: 'A specialized model for search and review tasks, optimized for efficiency.',
  },
  {
    id: 'gpt-4o',
    label: 'GPT-4o',
    value: LLMModel.GPT_4O,
    description: 'The full version of GPT-4, offering comprehensive capabilities.',
  },
  {
    id: 'gpt-4o-search-preview',
    label: 'GPT-4o Search Preview',
    value: LLMModel.GPT_4O_SEARCH_REVIEW,
    description: 'A powerful model designed for in-depth search and review applications.',
  },
  {
    id: 'gpt-5',
    label: 'GPT-5',
    value: LLMModel.GPT_5,
    description: 'The latest generation model with advanced features and improved performance.',
  },
  {
    id: 'gpt-5-mini',
    label: 'GPT-5 Mini',
    value: LLMModel.GPT_5_MINI,
    description: 'A smaller version of GPT-5, optimized for resource-constrained environments.',
  },
  {
    id: 'gpt-5-nano',
    label: 'GPT-5 Nano',
    value: LLMModel.GPT_5_NANO,
    description: 'A highly compressed version of GPT-5, designed for ultra-low resource usage.',
  },
  {
    id: 'gpt-5.1',
    label: 'GPT-5.1',
    value: LLMModel.GPT_5__1,
    description: 'An improved version of GPT-5 with enhanced capabilities.',
  },
  {
    id: 'gpt-5.2',
    label: 'GPT-5.2',
    value: LLMModel.GPT_5__2,
    description: 'A further refined version of GPT-5, offering even better performance.',
  },
];
