import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import type { QuickLinkAction } from '@/utils/quickLinks';
import { quickLinks } from '@/utils/quickLinks';

interface UseQuickLinksOptions {
  enableKeyboardShortcuts?: boolean;
  autoHideMessages?: boolean;
}

interface UseQuickLinksResult {
  allLinks: QuickLinkAction[];
  filteredLinks: QuickLinkAction[];
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  activeCategory: string;
  setActiveCategory: (category: string) => void;
  executeLink: (linkId: string) => void;
  getLinksByCategory: (category: string) => QuickLinkAction[];
  isAuthenticated: boolean;
  hasSelectedData: boolean;
}

export const useQuickLinks = (options: UseQuickLinksOptions = {}): UseQuickLinksResult => {
  const { enableKeyboardShortcuts = false, autoHideMessages = true } = options;

  const [searchTerm, setSearchTerm] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [hasSelectedData, setHasSelectedData] = useState(false);

  // Get all available quick links
  const allLinks = quickLinks.getAllQuickLinks();

  // Filter links based on search term and category
  const filteredLinks = allLinks.filter((link) => {
    const matchesSearch =
      link.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      link.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = activeCategory === 'all' || link.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  // Check authentication status
  useEffect(() => {
    const checkAuthStatus = () => {
      const token = localStorage.getItem('token');
      const isGuest = localStorage.getItem('isGuest') === 'true';
      setIsAuthenticated(!!token && !isGuest);
    };

    checkAuthStatus();

    // Listen for auth changes
    const handleStorageChange = () => {
      checkAuthStatus();
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  // Check data selection status (placeholder - implement based on your app's state management)
  useEffect(() => {
    // This would typically check your app's global state for selected data
    // For now, we'll assume data is available if user is authenticated
    setHasSelectedData(isAuthenticated);
  }, [isAuthenticated]);

  // Execute quick link with validation
  const executeLink = useCallback(
    (linkId: string) => {
      const link = allLinks.find((l) => l.id === linkId);

      if (!link) {
        message.error(`Quick link "${linkId}" not found`);
        return;
      }

      // Validate authentication requirement
      if (link.requiresAuth && !isAuthenticated) {
        message.warning('Please log in to access this feature');
        return;
      }

      // Validate data requirement
      if (link.requiresData && !hasSelectedData) {
        message.warning('Please select data to use this feature');
        return;
      }

      // Execute the link
      try {
        quickLinks.executeQuickLink(linkId);
      } catch (error) {
        message.error(`Failed to execute "${link.name}". Please try again.`);
        console.error('Quick link execution error:', error);
      }
    },
    [allLinks, isAuthenticated, hasSelectedData],
  );

  // Get links by category
  const getLinksByCategory = useCallback(
    (category: string) => {
      if (category === 'all') return filteredLinks;
      return filteredLinks.filter((link) => link.category === category);
    },
    [filteredLinks],
  );

  // Keyboard shortcuts
  useEffect(() => {
    if (!enableKeyboardShortcuts) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle shortcuts when Ctrl/Cmd + Shift are pressed
      if (!(event.ctrlKey || event.metaKey) || !event.shiftKey) return;

      // Prevent default browser behavior
      event.preventDefault();

      switch (event.key.toLowerCase()) {
        case 'd':
          executeLink('data-capture');
          break;
        case 'g':
          executeLink('auto-genie');
          break;
        case 'v':
          executeLink('visualization-panel');
          break;
        case 'b':
          executeLink('bug-fixer-ai');
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [enableKeyboardShortcuts, executeLink]);

  // Auto-hide messages
  useEffect(() => {
    if (autoHideMessages) {
      message.config({
        duration: 3,
        maxCount: 3,
      });
    }
  }, [autoHideMessages]);

  return {
    allLinks,
    filteredLinks,
    searchTerm,
    setSearchTerm,
    activeCategory,
    setActiveCategory,
    executeLink,
    getLinksByCategory,
    isAuthenticated,
    hasSelectedData,
  };
};

// Hook for global quick link state management
export const useGlobalQuickLinks = () => {
  const [isQuickLinksVisible, setIsQuickLinksVisible] = useState(false);

  // Toggle quick links panel
  const toggleQuickLinks = useCallback(() => {
    setIsQuickLinksVisible((prev) => !prev);
  }, []);

  // Show quick links panel
  const showQuickLinks = useCallback(() => {
    setIsQuickLinksVisible(true);
  }, []);

  // Hide quick links panel
  const hideQuickLinks = useCallback(() => {
    setIsQuickLinksVisible(false);
  }, []);

  // Listen for global quick links toggle events
  useEffect(() => {
    const handleToggleQuickLinks = () => {
      toggleQuickLinks();
    };

    window.addEventListener('toggleQuickLinks', handleToggleQuickLinks);
    return () => window.removeEventListener('toggleQuickLinks', handleToggleQuickLinks);
  }, [toggleQuickLinks]);

  return {
    isQuickLinksVisible,
    toggleQuickLinks,
    showQuickLinks,
    hideQuickLinks,
  };
};

export default useQuickLinks;
