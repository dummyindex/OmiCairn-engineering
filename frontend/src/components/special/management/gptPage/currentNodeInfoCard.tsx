const CurrentNodeInfoCard = ({ currentNodeInfo }: { currentNodeInfo?: any }) => {
  if (!currentNodeInfo) {
    return (
      <div
        style={{
          padding: '12px 16px',
          background: '#f8f9fa',
          border: '1px solid #e9ecef',
          borderRadius: '8px',
          minHeight: '57px',
          alignItems: 'center',
          display: 'flex',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#d9d9d9',
            }}
          />
          <span style={{ fontSize: '12px', color: '#666', fontWeight: '500' }}>
            No Node Selected
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: '12px 14px 8px 14px',
        background: 'linear-gradient(135deg, #f0f8ff 0%, #e6f7ff 100%)',
        border: '1px solid #d6e4ff',
        borderRadius: '8px',
      }}
    >
      <div>
        <div style={{ fontSize: '11px', color: '#262626' }}>
          <span style={{ color: '#8c8c8c' }}>Current Node:</span>{' '}
          <span style={{ fontWeight: '600' }}>{currentNodeInfo.name || 'Unnamed Node'}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
          <span
            style={{
              padding: '2px 8px',
              fontSize: '8px',
              borderRadius: '12px',
              background: '#fafafa',
              color: '#595959',
              border: '1px solid #d9d9d9',
            }}
          >
            ID: {currentNodeInfo.id || 'N/A'}
          </span>
          {currentNodeInfo.state && (
            <span
              style={{
                padding: '2px 8px',
                fontSize: '8px',
                borderRadius: '12px',
                background: currentNodeInfo.state === 'active' ? '#f6ffed' : '#fff2f0',
                color: currentNodeInfo.state === 'active' ? '#52c41a' : '#ff4d4f',
                border: `1px solid ${currentNodeInfo.state === 'active' ? '#d9f7be' : '#ffccc7'}`,
              }}
            >
              {currentNodeInfo.state.toUpperCase()}
            </span>
          )}
          {currentNodeInfo.type && (
            <span
              style={{
                padding: '2px 8px',
                fontSize: '8px',
                borderRadius: '12px',
                background: '#f0f8ff',
                color: '#1890ff',
                border: '1px solid #d6e4ff',
              }}
            >
              {currentNodeInfo.type}
            </span>
          )}
        </div>
      </div>
      {/* Future: Can add more node properties here */}
      {currentNodeInfo.description && (
        <div style={{ marginTop: '8px', fontSize: '12px', color: '#595959', lineHeight: '1.4' }}>
          {currentNodeInfo.description}
        </div>
      )}
    </div>
  );
};

export default CurrentNodeInfoCard;
