import { requestGetBranchReportPresignedUrl } from '@/request/node';
import { processFigurePlaceholders } from '@/util/markdown';
import { DownloadOutlined, FileTextOutlined, LoadingOutlined } from '@ant-design/icons';
import { Alert, Button, Card, message, Spin, Typography } from 'antd';
import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';

const { Text } = Typography;

interface Outputs {
  success?: boolean;
  message?: string;
  report_handler?: {
    jobId?: string;
    message?: string;
    reportId?: number;
    status?: string;
  };
}

const CreateReportToolDetails = ({ subTask }) => {
  const [markdownContent, setMarkdownContent] = useState<string>('');
  const [reportContentSections, setReportContentSections] = useState<
    {
      type: 'markdown' | 'figure';
      content: string;
      nodeId?: string;
      nodeName?: string;
      alt?: string;
    }[]
  >([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [downloadUrl, setDownloadUrl] = useState<string>('');
  const [jobId, setJobId] = useState<string>('');
  const [isDownloading, setIsDownloading] = useState<boolean>(false);

  const loadReportContent = async (jobId: string) => {
    setIsLoading(true);
    setError('');
    try {
      const { data } = await requestGetBranchReportPresignedUrl(jobId);

      if (data && data.url) {
        // Store download URL and jobId for download functionality
        setDownloadUrl(data.url);
        setJobId(jobId);

        const response = await fetch(data.url);

        if (!response.ok) {
          throw new Error(`Failed to fetch report: ${response.status} ${response.statusText}`);
        }

        const contentType = response.headers.get('content-type');
        let content = '';

        // Check if it's a zip file
        if (contentType?.includes('application/zip') || data.url.includes('.zip')) {
          const JSZip = (await import('jszip')).default;
          const arrayBuffer = await response.arrayBuffer();
          const zip = await JSZip.loadAsync(arrayBuffer);

          // Find markdown files
          const markdownFiles = Object.keys(zip.files).filter(
            (filename) => filename.endsWith('.md') && !filename.toLowerCase().includes('readme'),
          );

          if (markdownFiles.length > 0) {
            const mainReportFile = markdownFiles[0];
            content = (await zip.file(mainReportFile)?.async('text')) || '';
          } else {
            const anyMdFile = Object.keys(zip.files).find((filename) => filename.endsWith('.md'));
            if (anyMdFile) {
              content = (await zip.file(anyMdFile)?.async('text')) || '';
            } else {
              throw new Error('No markdown file found in the report archive');
            }
          }

          // Process figure placeholders and create sections
          const contentSections = await processFigurePlaceholders(content, zip);
          setReportContentSections(contentSections);
          setMarkdownContent('');
        } else {
          content = await response.text();
          setReportContentSections([
            {
              type: 'markdown',
              content: content,
            },
          ]);
          setMarkdownContent('');
        }
      } else {
        throw new Error('No report URL available');
      }
    } catch (error) {
      console.error('Error loading report:', error);
      setError(error instanceof Error ? error.message : 'Failed to load report');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!downloadUrl && !jobId) {
      message.error('No report available for download');
      return;
    }

    setIsDownloading(true);
    try {
      let urlToDownload = downloadUrl;

      // If no cached URL, request a fresh one
      if (!urlToDownload && jobId) {
        const { data } = await requestGetBranchReportPresignedUrl(jobId);
        if (data && data.url) {
          urlToDownload = data.url;
          setDownloadUrl(data.url);
        } else {
          throw new Error('Failed to get download URL');
        }
      }

      // Create a temporary link element to trigger download
      const link = document.createElement('a');
      link.href = urlToDownload;
      link.download = `report_${jobId || 'unknown'}.zip`; // Default filename
      link.target = '_blank';

      // Add link to document, click it, then remove it
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      message.success('Report download started');
    } catch (error) {
      console.error('Error downloading report:', error);
      message.error('Failed to download report');
    } finally {
      setIsDownloading(false);
    }
  };

  useEffect(() => {
    if (subTask.status === 'finished') {
      let outputs: Outputs = {};

      try {
        outputs = JSON.parse(subTask.outputs || '{}');
      } catch (error) {
        console.error('Error parsing outputs:', error);
        setError('Failed to parse task outputs');
        return;
      }

      if (outputs.success === false) {
        setError(outputs.message || 'Report generation failed');
      } else if (outputs.report_handler?.jobId) {
        loadReportContent(outputs.report_handler.jobId);
      } else {
        setError('No job ID found in report handler');
      }
    }
  }, [subTask.status, subTask.outputs]);

  // Show "Creating Report" when not finished
  if (subTask.status !== 'finished') {
    return (
      <Card
        size="small"
        style={{
          margin: '16px 0',
          textAlign: 'center',
          minHeight: '120px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ padding: '20px' }}>
          <LoadingOutlined
            style={{
              fontSize: '20px',
              color: '#1890ff',
              marginBottom: '10px',
              display: 'block',
            }}
          />
          <Text style={{ fontSize: '14px', color: '#666' }}>Creating Report...</Text>
        </div>
      </Card>
    );
  }

  // Show error message if success is false
  if (error) {
    return (
      <Card
        title={
          <span>
            <FileTextOutlined style={{ marginRight: '8px' }} />
            Report Generation
          </span>
        }
        size="small"
        style={{ margin: '16px 0' }}
      >
        <Alert message={error} type="error" showIcon />
      </Card>
    );
  }

  // Show loading state while fetching report content
  if (isLoading) {
    return (
      <Card
        title={
          <span>
            <FileTextOutlined style={{ marginRight: '8px' }} />
            Report Content
          </span>
        }
        size="small"
        style={{ margin: '16px 0' }}
      >
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" tip="Loading report content..." />
        </div>
      </Card>
    );
  }

  // Show markdown content
  return (
    <Card
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>
            <FileTextOutlined style={{ marginRight: '8px' }} />
            Report Content
          </span>
          <Button
            type="primary"
            size="small"
            loading={isDownloading}
            onClick={handleDownloadReport}
            icon={<DownloadOutlined />}
          >
            Download
          </Button>
        </div>
      }
      size="small"
      style={{ margin: '16px 0' }}
    >
      <div
        style={{
          maxHeight: '30vh',
          overflow: 'auto',
          padding: '12px',
          backgroundColor: '#fafafa',
          border: '1px solid #f0f0f0',
          borderRadius: '6px',
          fontSize: '11px',
        }}
      >
        {reportContentSections.length > 0 ? (
          (() => {
            let figureCount = 0;
            return reportContentSections.map((section, index) => (
              <div key={index}>
                {section.type === 'markdown' ? (
                  <ReactMarkdown
                    components={{
                      h1: ({ children }) => (
                        <h1
                          style={{
                            color: '#333',
                            borderBottom: '2px solid #e8e8e8',
                            paddingBottom: '6px',
                            marginBottom: '12px',
                            fontSize: '16px',
                          }}
                        >
                          {children}
                        </h1>
                      ),
                      h2: ({ children }) => (
                        <h2
                          style={{
                            color: '#333',
                            marginTop: '20px',
                            marginBottom: '10px',
                            fontSize: '14px',
                          }}
                        >
                          {children}
                        </h2>
                      ),
                      h3: ({ children }) => (
                        <h3
                          style={{
                            color: '#333',
                            marginTop: '16px',
                            marginBottom: '8px',
                            fontSize: '12px',
                          }}
                        >
                          {children}
                        </h3>
                      ),
                      p: ({ children }) => (
                        <p
                          style={{
                            lineHeight: '1.5',
                            marginBottom: '10px',
                            color: '#555',
                            fontSize: '11px',
                          }}
                        >
                          {children}
                        </p>
                      ),
                      code: ({ children, className }) =>
                        className ? (
                          <pre
                            style={{
                              backgroundColor: '#f6f8fa',
                              padding: '10px',
                              borderRadius: '4px',
                              fontSize: '10px',
                              overflow: 'auto',
                              border: '1px solid #e1e4e8',
                            }}
                          >
                            <code>{children}</code>
                          </pre>
                        ) : (
                          <code
                            style={{
                              backgroundColor: '#f6f8fa',
                              padding: '2px 4px',
                              borderRadius: '3px',
                              fontSize: '10px',
                              color: '#d73a49',
                            }}
                          >
                            {children}
                          </code>
                        ),
                      ul: ({ children }) => (
                        <ul
                          style={{
                            paddingLeft: '16px',
                            marginBottom: '10px',
                            fontSize: '11px',
                          }}
                        >
                          {children}
                        </ul>
                      ),
                      ol: ({ children }) => (
                        <ol
                          style={{
                            paddingLeft: '16px',
                            marginBottom: '10px',
                            fontSize: '11px',
                          }}
                        >
                          {children}
                        </ol>
                      ),
                      li: ({ children }) => (
                        <li
                          style={{
                            marginBottom: '3px',
                            lineHeight: '1.4',
                            fontSize: '11px',
                          }}
                        >
                          {children}
                        </li>
                      ),
                      blockquote: ({ children }) => (
                        <blockquote
                          style={{
                            borderLeft: '3px solid #dfe2e5',
                            paddingLeft: '12px',
                            marginLeft: '0',
                            color: '#6a737d',
                            fontStyle: 'italic',
                            fontSize: '11px',
                          }}
                        >
                          {children}
                        </blockquote>
                      ),
                      table: ({ children }) => (
                        <table
                          style={{
                            borderCollapse: 'collapse',
                            width: '100%',
                            marginBottom: '12px',
                            fontSize: '10px',
                          }}
                        >
                          {children}
                        </table>
                      ),
                      th: ({ children }) => (
                        <th
                          style={{
                            border: '1px solid #dfe2e5',
                            padding: '6px 8px',
                            backgroundColor: '#f6f8fa',
                            fontWeight: 'bold',
                            fontSize: '10px',
                          }}
                        >
                          {children}
                        </th>
                      ),
                      td: ({ children }) => (
                        <td
                          style={{
                            border: '1px solid #dfe2e5',
                            padding: '6px 8px',
                            fontSize: '10px',
                          }}
                        >
                          {children}
                        </td>
                      ),
                    }}
                  >
                    {section.content}
                  </ReactMarkdown>
                ) : (
                  // Render figure content
                  <div style={{ textAlign: 'center', margin: '16px 0' }}>
                    <img
                      src={section.content}
                      alt={section.alt || `Figure for Node ${section.nodeId}`}
                      style={{
                        maxWidth: '100%',
                        height: 'auto',
                        borderRadius: '6px',
                        padding: '6px',
                        boxShadow: '0 2px 8px rgba(0, 123, 255, 0.15)',
                        border: '1px solid #e8e8e8',
                      }}
                    />
                    <div
                      style={{
                        marginTop: '6px',
                        fontSize: '10px',
                        color: '#666',
                        fontStyle: 'italic',
                      }}
                    >
                      Figure {++figureCount}:{' '}
                      {section.alt ||
                        (section.nodeName
                          ? `Figure for Node ${section.nodeId} (${section.nodeName})`
                          : `Figure for Node ${section.nodeId}`)}
                    </div>
                  </div>
                )}
              </div>
            ));
          })()
        ) : markdownContent ? (
          <ReactMarkdown
            components={{
              h1: ({ children }) => (
                <h1
                  style={{
                    color: '#333',
                    borderBottom: '2px solid #e8e8e8',
                    paddingBottom: '6px',
                    marginBottom: '12px',
                    fontSize: '16px',
                  }}
                >
                  {children}
                </h1>
              ),
              h2: ({ children }) => (
                <h2
                  style={{
                    color: '#333',
                    marginTop: '20px',
                    marginBottom: '10px',
                    fontSize: '14px',
                  }}
                >
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3
                  style={{
                    color: '#333',
                    marginTop: '16px',
                    marginBottom: '8px',
                    fontSize: '12px',
                  }}
                >
                  {children}
                </h3>
              ),
              p: ({ children }) => (
                <p
                  style={{
                    lineHeight: '1.5',
                    marginBottom: '10px',
                    color: '#555',
                    fontSize: '11px',
                  }}
                >
                  {children}
                </p>
              ),
              code: ({ children, className }) =>
                className ? (
                  <pre
                    style={{
                      backgroundColor: '#f6f8fa',
                      padding: '10px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      overflow: 'auto',
                      border: '1px solid #e1e4e8',
                    }}
                  >
                    <code>{children}</code>
                  </pre>
                ) : (
                  <code
                    style={{
                      backgroundColor: '#f6f8fa',
                      padding: '2px 4px',
                      borderRadius: '3px',
                      fontSize: '10px',
                      color: '#d73a49',
                    }}
                  >
                    {children}
                  </code>
                ),
              ul: ({ children }) => (
                <ul
                  style={{
                    paddingLeft: '16px',
                    marginBottom: '10px',
                    fontSize: '11px',
                  }}
                >
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol
                  style={{
                    paddingLeft: '16px',
                    marginBottom: '10px',
                    fontSize: '11px',
                  }}
                >
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li
                  style={{
                    marginBottom: '3px',
                    lineHeight: '1.4',
                    fontSize: '11px',
                  }}
                >
                  {children}
                </li>
              ),
              blockquote: ({ children }) => (
                <blockquote
                  style={{
                    borderLeft: '3px solid #dfe2e5',
                    paddingLeft: '12px',
                    marginLeft: '0',
                    color: '#6a737d',
                    fontStyle: 'italic',
                    fontSize: '11px',
                  }}
                >
                  {children}
                </blockquote>
              ),
              table: ({ children }) => (
                <table
                  style={{
                    borderCollapse: 'collapse',
                    width: '100%',
                    marginBottom: '12px',
                    fontSize: '10px',
                  }}
                >
                  {children}
                </table>
              ),
              th: ({ children }) => (
                <th
                  style={{
                    border: '1px solid #dfe2e5',
                    padding: '6px 8px',
                    backgroundColor: '#f6f8fa',
                    fontWeight: 'bold',
                    fontSize: '10px',
                  }}
                >
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td
                  style={{
                    border: '1px solid #dfe2e5',
                    padding: '6px 8px',
                    fontSize: '10px',
                  }}
                >
                  {children}
                </td>
              ),
            }}
          >
            {markdownContent}
          </ReactMarkdown>
        ) : null}
      </div>
    </Card>
  );
};

export default CreateReportToolDetails;
