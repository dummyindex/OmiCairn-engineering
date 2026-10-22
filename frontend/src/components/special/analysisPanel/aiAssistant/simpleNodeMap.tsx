const SimpleNodeMap = ({ nodes, onNodeClick, chatContext }) => {
  if (!nodes || !Array.isArray(nodes) || nodes.length === 0) {
    return (
      <div>
        <div
          style={{
            fontSize: '12px',
            color: '#666',
            marginBottom: '8px',
            paddingLeft: '10px',
            cursor: 'default',
          }}
        >
          Node Tags:
        </div>
        <div
          style={{
            border: '1px solid #e8e8e8',
            borderRadius: '8px',
            padding: '10px',
            background: '#f8f9fc',
            margin: '8px 0 12px 4px',
            height: '50px',
            width: '98%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div style={{ fontSize: '12px', color: '#666', cursor: 'default' }}>
            No nodes available
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        paddingLeft: '10px',
        width: '100%',
      }}
    >
      <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px', cursor: 'default' }}>
        Node Tags:
      </div>

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px',
          padding: '10px',
          border: '1px solid #e8e8e8',
          borderRadius: '8px',
          background: '#f8f9fc',
          margin: '0 8px 12px 0',
        }}
      >
        {nodes.map((node) => {
          const nodeLabel = chatContext === 'pipeline' ? node.data.label : node.data.label;
          const nodeState =
            chatContext === 'pipeline' ? node.data.state || 'normal' : node.data?.state || 'normal';

          return (
            <div
              key={node.id}
              onClick={() => onNodeClick(node)}
              style={{
                backgroundColor: nodeState === 'failed' ? '#fff0f0' : '#e6effb',
                border: `1px solid ${nodeState === 'failed' ? '#ffccc7' : '#d6e4ff'}`,
                borderRadius: '4px',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                fontSize: '10px',
                fontWeight: 500,
                color: nodeState === 'failed' ? '#f5222d' : '#1a1a1a',
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                transition: 'transform 0.2s, box-shadow 0.2s',
                padding: '4px 8px',
                height: '22px',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'scale(1.05)';
                e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'scale(1)';
                e.currentTarget.style.boxShadow = '0 1px 2px rgba(0,0,0,0.05)';
              }}
            >
              #{nodeLabel}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SimpleNodeMap;
