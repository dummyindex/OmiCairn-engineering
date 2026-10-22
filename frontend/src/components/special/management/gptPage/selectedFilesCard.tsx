interface FileItem {
  id: string;
  name: string;
  size?: string;
  lastModified?: string;
}

const SelectedFilesCard: React.FC<{ selectedFiles: FileItem[] }> = ({ selectedFiles }) => {
  if (!selectedFiles || selectedFiles.length === 0) {
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
            No Files Selected
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: '12px 16px',
        background: 'linear-gradient(135deg, #f0f8ff 0%, #e6f7ff 100%)',
        border: '1px solid #d6e4ff',
        borderRadius: '8px',
        minHeight: '57px',
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#262626', marginBottom: '2px' }}>
              <span style={{ color: '#8c8c8c' }}>Selected Files:</span>{' '}
              <span style={{ fontWeight: '600' }}>
                {selectedFiles.length} item{selectedFiles.length !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              padding: '2px 8px',
              fontSize: '11px',
              borderRadius: '12px',
              background: '#f0f8ff',
              color: '#1890ff',
              border: '1px solid #d6e4ff',
            }}
          >
            {selectedFiles.length} FILES
          </span>
        </div>
      </div>
    </div>
  );
};

export default SelectedFilesCard;
