import { requestEdgeListOfAnalysis } from '@/request/edge';
import { requestNodeListOfAnalysis } from '@/request/node';
import { organizeAnalysisTree } from '@/util/flowTool';
import { DownOutlined, FileOutlined, FolderOutlined, LoadingOutlined } from '@ant-design/icons';
import { Button, Drawer, message, Spin, Tree } from 'antd';
import React, { useEffect, useState } from 'react';

const AnalysisTree = ({ visible, onClose, selectedKeys, onSelectKeys, analysisId, isEditable }) => {
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [loadingKeySet, setLoadingKeySet] = useState<Set<React.Key>>(new Set());
  const [treeData, setTreeData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const loadTreeData = async () => {
    if (analysisId == null) {
      setTreeData([]);
      return;
    }
    setLoading(true);
    try {
      const { data: nodes } = await requestNodeListOfAnalysis(analysisId);
      const { data: edges } = await requestEdgeListOfAnalysis(analysisId);

      if (nodes && edges) {
        const treeData = organizeAnalysisTree(
          edges,
          nodes.filter((node) => node.type !== 'report node'),
        );
        setTreeData(treeData);
      } else {
        message.error('Failed to load analysis tree data');
      }
    } catch (error) {
      console.error('Error loading analysis tree:', error);
      message.error('Failed to load analysis tree');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible) {
      loadTreeData();
    }
  }, [visible]);

  useEffect(() => {
    if (!analysisId) {
      const intervalId = setInterval(() => {
        loadTreeData();
      }, 3000);
      return () => clearInterval(intervalId);
    }
  }, [analysisId]);

  // const getAllChildKeys = (node: any): string[] => {
  //   let allKeys = [node.key];
  //   if (node.children && node.children.length > 0) {
  //     node.children.forEach((child: any) => {
  //       allKeys = allKeys.concat(getAllChildKeys(child));
  //     });
  //   }
  //   return allKeys;
  // };

  // const handleSelectWithChildren = (node: any) => {
  //   const allKeys = getAllChildKeys(node);
  //   const newCheckedKeys = [...new Set([...checkedKeys, ...allKeys])];
  //   setCheckedKeys(newCheckedKeys);
  //   onSelectKeys(newCheckedKeys);
  // };

  const onSelect = (selectedKeysValue: React.Key[]) => {
    setLoadingKeySet(new Set(selectedKeysValue));
    onSelectKeys(selectedKeysValue);
    setTimeout(() => {
      setLoadingKeySet(new Set());
    }, 2200);
  };

  const onExpand = (expandedKeysValue: React.Key[]) => {
    setExpandedKeys(expandedKeysValue);
  };

  const clearAll = () => {
    onSelectKeys([]);
  };

  return (
    <Drawer
      title="Analysis Tree"
      placement="right"
      onClose={onClose}
      open={visible}
      width={600}
      mask={false}
    >
      <div style={{ height: '90vh' }}>
        <div
          style={{
            padding: '12px',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <span>Analysis Tree</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              size="small"
              onClick={clearAll}
              style={{ fontSize: '12px' }}
              disabled={!isEditable}
            >
              Clear All
            </Button>
          </div>
        </div>

        <div style={{ padding: '12px', height: 'calc(100% - 120px)', overflow: 'auto' }}>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: '12px' }}>
            Selected {selectedKeys.length} nodes
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <LoadingOutlined /> Loading analysis tree...
            </div>
          ) : treeData.length > 0 ? (
            treeData.map((rootNode) => (
              <div key={rootNode.key} style={{ marginBottom: '12px' }}>
                <Tree
                  checkable
                  checkStrictly
                  showLine={rootNode.children && rootNode.children.length > 0}
                  showIcon
                  switcherIcon={<DownOutlined />}
                  disabled={!isEditable}
                  onCheck={(checkedKeys) => {
                    const checked = Array.isArray(checkedKeys) ? checkedKeys : checkedKeys.checked;
                    if (checked.length === 0) {
                      onSelect([]);
                    } else {
                      const lastKey = checked[checked.length - 1];
                      if (lastKey !== undefined) {
                        onSelect([lastKey]);
                      }
                    }
                  }}
                  onSelect={onSelect}
                  onExpand={onExpand}
                  checkedKeys={selectedKeys}
                  expandedKeys={expandedKeys}
                  selectedKeys={selectedKeys}
                  treeData={[rootNode]}
                  titleRender={(nodeData) => (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        width: '100%',
                      }}
                    >
                      {loadingKeySet.has(nodeData.key) ? (
                        <Spin size="small" style={{ marginRight: '8px' }} />
                      ) : nodeData.children.length > 0 ? (
                        <FolderOutlined
                          style={{
                            color: nodeData.icon?.props.style.color || '#000',
                            marginRight: '8px',
                          }}
                        />
                      ) : (
                        <FileOutlined style={{ marginRight: '8px' }} />
                      )}
                      <span>{nodeData.name}</span>
                      {/* {nodeData.children && nodeData.children.length > 0 && (
                      <Button
                        size="small"
                        type="text"
                        style={{
                          fontSize: '10px',
                          height: '20px',
                          padding: '0 6px',
                          marginLeft: '8px',
                          color: '#5974CE',
                          border: '1px solid #5974CE',
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectWithChildren(nodeData);
                        }}
                      >
                        Select All
                      </Button>
                    )} */}
                    </div>
                  )}
                />
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', color: '#999', padding: '40px 20px' }}>
              <FileOutlined style={{ fontSize: '32px', marginBottom: '16px' }} />
              <div>No tree data found</div>
            </div>
          )}
        </div>
      </div>
    </Drawer>
  );
};

export default AnalysisTree;
