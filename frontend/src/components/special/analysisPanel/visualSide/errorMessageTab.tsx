import React from 'react';
import { Collapse, Dropdown } from 'antd';
import { LoadingOutlined, MoreOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { useModel } from 'umi';

const { Panel } = Collapse;

interface ErrorMessageTabProps {
  errorNodeList?: any[];
  activePanelKey?: string | string[] | number | number[];
  errorMessage?: any;
  errorSolution?: any;
  errorMessageAndSolution?: any;
  errorMessageAndSolutionLoading?: any;
  errorLogShow?: any;
  errorMessageLog?: any;
  errorMessageLogLoading?: any;
  onCollapseChange?: (key: string | string[] | number | number[]) => void;
  getErrorMessageMenu?: (nodeId: string) => React.ReactNode;
  collapseRefs?: React.MutableRefObject<Record<string, HTMLDivElement | null>>;
}

const ErrorMessageTab: React.FC<ErrorMessageTabProps> = ({
  errorNodeList = [],
  activePanelKey,
  errorMessage = {},
  errorSolution = {},
  errorMessageAndSolution = {},
  errorMessageAndSolutionLoading = {},
  errorLogShow = {},
  errorMessageLog = {},
  errorMessageLogLoading = {},
  onCollapseChange,
  getErrorMessageMenu,
  collapseRefs,
}) => {
  const { dictionary } = useModel('localization');

  return (
    <div className="error-message-content">
      {errorNodeList.map((item) => (
        <div
          key={item.id}
          ref={collapseRefs ? (el) => (collapseRefs.current[item.id] = el) : undefined}
          data-node-id={item.id}
        >
          <Collapse ghost collapsible="icon" activeKey={activePanelKey} onChange={onCollapseChange}>
            <Panel
              key={item.id}
              header={
                <div className="error-message-header">
                  <span>{item.name}</span>
                </div>
              }
              extra={
                getErrorMessageMenu && (
                  <Dropdown overlay={getErrorMessageMenu(item.id)} trigger={['hover']}>
                    <MoreOutlined style={{ cursor: 'pointer' }} />
                  </Dropdown>
                )
              }
            >
              {errorMessageAndSolutionLoading[item.id] ? (
                <div>
                  <LoadingOutlined /> {dictionary.LOADING || 'Loading'}...
                </div>
              ) : errorSolution[item.id] !== '' && errorMessage[item.id] !== '' ? (
                <div>
                  <div className="errorDetails">
                    <ReactMarkdown className="markdown-content">
                      {errorMessage[item.id]}
                    </ReactMarkdown>
                  </div>
                  <div className="errorSolutionTitle">SOLUTION</div>
                  <div className="errorSolution">
                    <ReactMarkdown className="markdown-content">
                      {errorSolution[item.id]}
                    </ReactMarkdown>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="errorSolutionTitle">ERROR MESSAGE AND SOLUTION</div>
                  <div className="errorSolution">
                    <ReactMarkdown className="markdown-content">
                      {errorMessageAndSolution[item.id]}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
              <div>
                {errorMessageLogLoading[item.id] ? (
                  <div className="loading" style={{ marginTop: '20px' }}>
                    <LoadingOutlined /> {dictionary.LOADING || 'Loading'}...
                  </div>
                ) : errorMessageLog[item.id] ? (
                  <div
                    className="errorLogContent"
                    style={{
                      marginTop: '7px',
                      display: errorLogShow[item.id] ? 'block' : 'none',
                    }}
                  >
                    {errorMessageLog[item.id]}
                  </div>
                ) : null}
              </div>
            </Panel>
          </Collapse>
        </div>
      ))}
    </div>
  );
};

export default ErrorMessageTab;
