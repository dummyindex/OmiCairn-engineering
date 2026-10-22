/**
 * Quick Links Utility for OMICAIRN Core Functionalities
 * Provides quick access to all major features with proper state management
 */
import { history } from 'umi';
import { message } from 'antd';

export interface QuickLinkAction {
  id: string;
  name: string;
  description: string;
  category: 'data' | 'analysis' | 'ai' | 'visualization';
  action: (analysisId?: string, currentSelectedNodes?: any[]) => void;
  requiresAuth?: boolean;
  requiresData?: boolean;
}

export class QuickLinksManager {
  private static instance: QuickLinksManager;

  public static getInstance(): QuickLinksManager {
    if (!QuickLinksManager.instance) {
      QuickLinksManager.instance = new QuickLinksManager();
    }
    return QuickLinksManager.instance;
  }

  /**
   * Open Data Capture Modal
   */
  openDataCapture(): void {
    try {
      window.dispatchEvent(new CustomEvent('openDataCaptureModal'));
    } catch (error) {
      message.error('Failed to open Data Capture. Please try again.');
    }
  }

  /**
   * Start Auto Genie Task
   */
  startAutoGenie(): void {
    try {
      window.dispatchEvent(new CustomEvent('openAutoGenieModal'));
    } catch (error) {
      message.error('Failed to open Auto Genie. Please try again.');
    }
  }

  /**
   * Open Visualization Panel
   */
  openVisualizationPanel(analysisId?: string, currentSelectedNodes?: any[]): void {
    try {
      window.dispatchEvent(
        new CustomEvent('openVisualizationPanel', {
          detail: { analysisId, currentSelectedNodes },
        }),
      );
    } catch (error) {
      message.error('Failed to open Visualization Panel. Please try again.');
    }
  }

  /**
   * Open Bug Fixer AI
   */
  openBugFixerAI(): void {
    try {
      window.dispatchEvent(new CustomEvent('openBugFixerAI'));
    } catch (error) {
      message.error('Failed to open Bug Fixer AI. Please try again.');
    }
  }

  /**
   * Get all available quick link actions
   */
  getAllQuickLinks(): QuickLinkAction[] {
    return [
      {
        id: 'data-capture',
        name: 'Data Capture',
        description: 'AI-powered dataset discovery and recommendation',
        category: 'data',
        action: () => this.openDataCapture(),
        requiresAuth: true,
      },
      {
        id: 'auto-genie',
        name: 'Auto Genie',
        description: 'Automatically generate analysis pipelines using AI',
        category: 'ai',
        action: () => this.startAutoGenie(),
        requiresAuth: true,
      },
      {
        id: 'visualization-panel',
        name: 'Visualization Panel',
        description: 'Interactive data visualization with multiple chart types',
        category: 'visualization',
        action: (analysisId, currentSelectedNodes) =>
          this.openVisualizationPanel(analysisId, currentSelectedNodes),
        requiresAuth: true,
        requiresData: true,
      },
      {
        id: 'bug-fixer-ai',
        name: 'Bug Fixer AI',
        description: 'AI-powered bug detection and fixing',
        category: 'ai',
        action: () => this.openBugFixerAI(),
        requiresAuth: true,
      },
    ];
  }

  /**
   * Execute quick link by ID
   */
  executeQuickLink(id: string, analysisId?: string, currentSelectedNodes?: any[]): void {
    const quickLink = this.getAllQuickLinks().find((link) => link.id === id);
    if (quickLink) {
      if (quickLink.requiresAuth && !localStorage.getItem('token')) {
        message.warning('Please log in to access this feature.');
        history.push('/login/byPassword');
        return;
      }

      // Check if data is required and validate
      if (quickLink.requiresData && (!currentSelectedNodes || currentSelectedNodes.length === 0)) {
        message.warning('Please select a node to use this feature.');
        return;
      }

      // Execute the quick link action with context
      quickLink.action(analysisId, currentSelectedNodes);
    } else {
      message.error(`Quick link with ID "${id}" not found.`);
    }
  }
}

export const quickLinks = QuickLinksManager.getInstance();

export const openDataCapture = () => quickLinks.openDataCapture();
export const startAutoGenie = () => quickLinks.startAutoGenie();
export const openVisualizationPanel = () => quickLinks.openVisualizationPanel();
export const openBugFixerAI = () => quickLinks.openBugFixerAI();
