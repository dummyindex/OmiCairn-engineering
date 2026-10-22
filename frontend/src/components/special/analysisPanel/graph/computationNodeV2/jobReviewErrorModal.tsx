import { useEffect, useState } from 'react';
import { Modal, Spin, Typography } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';
import { requestLatestComputation, requestJobReviewerErrorDetails } from '@/request/computation';

const { Paragraph, Title } = Typography;

interface JobReviewErrorModalProps {
  visible: boolean;
  nodeId: string;
  onClose: () => void;
}

const JobReviewErrorModal: React.FC<JobReviewErrorModalProps> = ({ visible, nodeId, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [reviewErrorData, setReviewErrorData] = useState<any>(null);
  const fetchReviewError = async () => {
    if (!nodeId) return;

    setLoading(true);
    try {
      const { data: latestComputation } = await requestLatestComputation(nodeId);

      if (latestComputation) {
        const { data: reviewError } = await requestJobReviewerErrorDetails(latestComputation.id);

        if (reviewError) {
          setReviewErrorData(reviewError || null);
        }
      }
    } catch (error) {
      console.error('Failed to fetch job reviewer error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible && nodeId) {
      fetchReviewError();
    } else {
      setReviewErrorData(null);
    }
  }, [visible, nodeId]);

  const renderErrorContent = () => {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16, color: '#666' }}>Loading review error details...</div>
        </div>
      );
    }

    return (
      <div>
        {reviewErrorData && (
          <div>
            <Title level={5}>Job Reviewer Error Details</Title>
            <div
              style={{
                backgroundColor: '#f5f5f5',
                padding: '16px',
                borderRadius: '4px',
                border: '1px solid #d9d9d9',
                maxHeight: '400px',
                overflowY: 'auto',
              }}
            >
              {typeof reviewErrorData === 'string' ? (
                <Paragraph
                  style={{ marginBottom: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}
                >
                  {reviewErrorData}
                </Paragraph>
              ) : (
                <pre
                  style={{
                    marginBottom: 0,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    fontFamily: 'monospace',
                    fontSize: '13px',
                  }}
                >
                  {JSON.stringify(reviewErrorData, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <Modal
      open={visible}
      title={
        <span>
          <ExclamationCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
          Job Reviewer Error
        </span>
      }
      onCancel={onClose}
      centered
      width={800}
      footer={null}
      bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
    >
      {renderErrorContent()}
    </Modal>
  );
};

export default JobReviewErrorModal;
