import React, { useState } from 'react';
import { Card, Button, Tooltip, Input, Row, Col, Badge } from 'antd';
import {
  DatabaseOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
  BugOutlined,
} from '@ant-design/icons';
import type { QuickLinkAction } from '@/utils/quickLinks';
import { quickLinks } from '@/utils/quickLinks';
import styles from './QuickLinksPanel.less';
const { Search } = Input;

// Icon mapping for different functionalities
const iconMap: Record<string, React.ReactNode> = {
  'data-capture': <DatabaseOutlined />,
  'auto-genie': <ThunderboltOutlined />,
  'visualization-panel': <BarChartOutlined />,
  'bug-fixer-ai': <BugOutlined />,
};

// Category colors
const categoryColors: Record<string, string> = {
  data: '#1890ff',
  analysis: '#52c41a',
  ai: '#722ed1',
  visualization: '#fa8c16',
};

interface QuickLinksPanelProps {
  className?: string;
  style?: React.CSSProperties;
  showSearch?: boolean;
  compactMode?: boolean;
}

const QuickLinksPanel: React.FC<QuickLinksPanelProps> = ({
  className,
  style,
  showSearch = true,
  compactMode = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const allQuickLinks = quickLinks.getAllQuickLinks();

  // Filter links based on search term
  const filteredLinks = allQuickLinks.filter((link) => {
    const matchesSearch =
      link.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      link.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  const handleQuickLinkClick = (link: QuickLinkAction) => {
    quickLinks.executeQuickLink(link.id);
  };

  const renderQuickLinkCard = (link: QuickLinkAction) => (
    <Col
      key={link.id}
      xs={24}
      sm={compactMode ? 24 : 12}
      md={compactMode ? 12 : 8}
      lg={compactMode ? 8 : 6}
      style={{ marginBottom: 16 }}
    >
      <Card
        hoverable
        className={styles.quickLinkCard}
        bodyStyle={{ padding: compactMode ? '12px' : '16px' }}
        onClick={() => handleQuickLinkClick(link)}
      >
        <div className={styles.cardContent}>
          <div className={styles.cardIcon}>
            <Badge dot color={categoryColors[link.category]} offset={[4, 4]}>
              {iconMap[link.id] || <ExperimentOutlined />}
            </Badge>
          </div>
          <div className={styles.cardInfo}>
            <h4 className={styles.cardTitle}>{link.name}</h4>
            {!compactMode && <p className={styles.cardDescription}>{link.description}</p>}
            <div className={styles.cardMeta}>
              <span
                className={styles.categoryTag}
                style={{ backgroundColor: categoryColors[link.category] }}
              >
                {link.category.toUpperCase()}
              </span>
              {link.requiresAuth && (
                <Tooltip title="Requires authentication">
                  <span className={styles.requirementTag}>Auth</span>
                </Tooltip>
              )}
              {link.requiresData && (
                <Tooltip title="Requires data selection">
                  <span className={styles.requirementTag}>Data</span>
                </Tooltip>
              )}
            </div>
          </div>
        </div>
      </Card>
    </Col>
  );

  return (
    <div className={`${styles.quickLinksPanel} ${className}`} style={style}>
      <div className={styles.panelHeader}>
        <h3>OmiCairn Core Functionalities</h3>
        {showSearch && (
          <Search
            placeholder="Search functionalities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ width: 300, marginBottom: 16 }}
            allowClear
          />
        )}
      </div>

      <Row gutter={[16, 16]}>{filteredLinks.map(renderQuickLinkCard)}</Row>

      {filteredLinks.length === 0 && searchTerm && (
        <div className={styles.emptyState}>
          <p>No functionalities found matching {searchTerm}.</p>
          <Button type="link" onClick={() => setSearchTerm('')}>
            Clear search
          </Button>
        </div>
      )}
    </div>
  );
};

export default QuickLinksPanel;
