import { Card } from 'antd';
import { useState } from 'react';
interface FunctionBlock {
  createdTime: string;
  currentVersionId: number;
  groupId: number;
  id: number;
  name: string;
  state: string;
  type: string;
  altName: string | null;
}

interface Group {
  createdTime: number;
  functionBlockList: FunctionBlock[];
  id: number;
  name: string;
  serialNumber: number;
  altName: string;
}

interface ApiResponse {
  success: boolean;
  message: string;
  groups: Group[];
}

const GetAvailableFunctionBlocksToolDetails = ({ subTask }) => {
  const [expandedGroups, setExpandedGroups] = useState<Set<number>>(new Set());

  const toggleGroup = (groupId: number) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupId)) {
      newExpanded.delete(groupId);
    } else {
      newExpanded.add(groupId);
    }
    setExpandedGroups(newExpanded);
  };

  const renderFunctionBlock = (fb: FunctionBlock) => (
    <div
      key={fb.id}
      style={{
        backgroundColor: '#fafafa',
        border: '1px solid #e0e0e0',
        borderRadius: '3px',
        padding: '6px',
        marginBottom: '4px',
      }}
    >
      <div
        style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '11px' }}
      >
        <div>
          <strong>ID:</strong> {fb.id}
        </div>
        <div>
          <strong>Name:</strong> {fb.name}
        </div>
        <div>
          <strong>Alternate name:</strong> {fb.altName || 'N/A'}
        </div>
        <div>
          <strong>Type:</strong> {fb.type}
        </div>
        <div>
          <strong>State:</strong>{' '}
          <span
            style={{
              color: fb.state === 'active' ? '#52c41a' : '#666',
              fontWeight: 'bold',
            }}
          >
            {fb.state}
          </span>
        </div>
        <div>
          <strong>Version ID:</strong> {fb.currentVersionId}
        </div>
        <div style={{ gridColumn: '1 / -1' }}>
          <strong>Created:</strong> {fb.createdTime}
        </div>
      </div>
    </div>
  );

  const renderGroup = (group: Group) => {
    const isExpanded = expandedGroups.has(group.id);

    return (
      <div
        key={group.id}
        style={{
          border: '1px solid #e0e0e0',
          borderRadius: '4px',
          marginBottom: '4px',
          overflow: 'hidden',
        }}
      >
        <div
          onClick={() => toggleGroup(group.id)}
          style={{
            backgroundColor: '#1890ff',
            color: 'white',
            padding: '6px',
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            userSelect: 'none',
          }}
        >
          <div>
            <div style={{ fontSize: '11px' }}>
              {group.name} ({group.altName})
            </div>
          </div>
          <div style={{ fontSize: '8px' }}>{isExpanded ? '▼' : '▶'}</div>
        </div>

        {isExpanded && (
          <div style={{ padding: '8px', backgroundColor: '#fff' }}>
            {group.functionBlockList.length > 0 ? (
              group.functionBlockList.map(renderFunctionBlock)
            ) : (
              <div
                style={{
                  textAlign: 'center',
                  color: '#666',
                  fontStyle: 'italic',
                  padding: '10px',
                  fontSize: '11px',
                }}
              >
                No function blocks in this group
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderContent = () => {
    if (subTask.status !== 'finished') {
      return (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px 10px',
            color: '#666',
            fontSize: '12px',
            fontStyle: 'italic',
          }}
        >
          Fetching fbs...
        </div>
      );
    }

    try {
      const data: ApiResponse = JSON.parse(subTask.outputs);

      return (
        <div>
          {/* Status Header */}
          <div
            style={{
              backgroundColor: data.success ? '#f6ffed' : '#fff2f0',
              border: `1px solid ${data.success ? '#b7eb8f' : '#ffccc7'}`,
              color: data.success ? '#389e0d' : '#ff4d4f',
              borderRadius: '3px',
              padding: '6px',
              marginBottom: '10px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ fontSize: '12px' }}>{data.success ? '✅' : '❌'}</span>
              <div>
                <div style={{ fontWeight: 'bold', fontSize: '11px' }}>
                  Status: {data.success ? 'Success' : 'Failed'}
                </div>
                {data.message && (
                  <div style={{ fontSize: '10px', marginTop: '2px' }}>{data.message}</div>
                )}
              </div>
            </div>
          </div>

          {/* Groups */}
          <div>
            <h3
              style={{
                color: '#333',
                marginBottom: '8px',
                borderBottom: `1px solid #1890ff`,
                paddingBottom: '4px',
                fontSize: '12px',
              }}
            >
              Function Block Groups ({data.groups.length})
            </h3>

            <div style={{ maxHeight: '25vh', overflowY: 'auto', paddingRight: '4px' }}>
              {data.groups.length > 0 ? (
                data.groups.map(renderGroup)
              ) : (
                <div
                  style={{
                    textAlign: 'center',
                    color: '#666',
                    fontStyle: 'italic',
                    padding: '20px',
                    fontSize: '11px',
                  }}
                >
                  No groups available
                </div>
              )}
            </div>
          </div>
        </div>
      );
    } catch (error) {
      return (
        <div
          style={{
            backgroundColor: '#fff2f0',
            border: '1px solid #ffccc7',
            borderRadius: '4px',
            padding: '8px',
            color: '#ff4d4f',
            fontSize: '11px',
          }}
        >
          Error parsing JSON: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      );
    }
  };

  return (
    <Card style={{ fontFamily: 'Arial, sans-serif' }} size="small">
      {renderContent()}
    </Card>
  );
};

export default GetAvailableFunctionBlocksToolDetails;
