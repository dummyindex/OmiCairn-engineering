import {
  DatabaseOutlined,
  DownOutlined,
  ExpandOutlined,
  LoadingOutlined,
  ShrinkOutlined,
} from '@ant-design/icons';
import type { TreeDataNode, TreeProps } from 'antd';
import { Button, Empty, message, Spin, Tooltip, Tree } from 'antd';
import React, { useCallback, useEffect, useState } from 'react';
import { useReactFlow } from 'reactflow';
import { useModel } from 'umi';

enum NodeState {
  ORIGINAL = 'original',
  RUNNING = 'running',
  FINISHED = 'finished',
  FAILED = 'failed',
  PENDING = 'pending',
  DEBUGGING = 'debugging',
  CANCELLED = 'cancelled',
  GENERATING = 'generating',
  BEAUTIFYING = 'beautifying',
}

const titleColorMap: Record<string, string> = {
  [NodeState.ORIGINAL]: 'black',
  [NodeState.RUNNING]: '#939393',
  [NodeState.FINISHED]: '#4D9A17',
  [NodeState.FAILED]: '#C74242',
  [NodeState.PENDING]: '#939393',
  [NodeState.DEBUGGING]: '#939393',
  [NodeState.CANCELLED]: 'black',
  [NodeState.GENERATING]: '#939393',
  [NodeState.BEAUTIFYING]: '#939393',
};

const iconColorMap: Record<string, string> = {
  [NodeState.ORIGINAL]: '#1890ff',
  [NodeState.RUNNING]: '#939393',
  [NodeState.FINISHED]: '#4D9A17',
  [NodeState.FAILED]: '#C74242',
  [NodeState.PENDING]: '#939393',
  [NodeState.DEBUGGING]: '#939393',
  [NodeState.CANCELLED]: '#1890ff',
  [NodeState.GENERATING]: '#939393',
  [NodeState.BEAUTIFYING]: '#939393',
};

const NodeTypeIcons = {
  'computation node': '○',
  'computation node v2': '○',
  'report node': '□',
  'data node v2': <DatabaseOutlined style={{ fontSize: '14px' }} />,
  'data node': <DatabaseOutlined style={{ fontSize: '14px' }} />,
};

interface WorkflowNode {
  id: number;
  name: string;
  state: string;
  type: string;
  x?: number;
  y?: number;
}

interface Edge {
  id: number;
  sourceNodeId: number;
  targetNodeId: number;
}

const AnalysisTree: React.FC = () => {
  const [treeData, setTreeData] = useState<TreeDataNode[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const { nodeList, edgeList, setTemporaryCenteredNodeId } = useModel('analysis');
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [allKeys, setAllKeys] = useState<string[]>([]);
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([]);
  const { setCenter } = useReactFlow();

  const renderTitle = (node: WorkflowNode) => {
    const color = titleColorMap[node.state] || 'black';
    return <span style={{ color }}>{node.name}</span>;
  };

  const getNodeIcon = (state: string, type: string) => {
    const color = iconColorMap[state] || '#1890ff';
    const icon = NodeTypeIcons[type] || '○';
    return <span style={{ color, fontSize: '16px' }}>{icon}</span>;
  };

  const processDataToTree = (nodes: WorkflowNode[], edges: Edge[]): TreeDataNode[] => {
    if (!nodes || nodes.length === 0) {
      return [];
    }

    const nodeMap: Record<number, WorkflowNode & { children: WorkflowNode[] }> = {};
    nodes.forEach((node) => {
      nodeMap[node.id] = {
        ...node,
        children: [],
      };
    });

    const childNodes = new Set<number>();
    const sourceNodes = new Set<number>();

    if (edges && edges.length > 0) {
      edges.forEach((edge) => {
        const sourceNode = nodeMap[edge.sourceNodeId];
        const targetNode = nodeMap[edge.targetNodeId];

        if (sourceNode && targetNode) {
          childNodes.add(edge.targetNodeId);
          sourceNodes.add(edge.sourceNodeId);
          sourceNode.children.push(targetNode);
        }
      });
    }

    const rootNodes = nodes.filter((node) => sourceNodes.has(node.id) && !childNodes.has(node.id));

    rootNodes.sort((a, b) => {
      const aY = typeof a.y === 'number' ? a.y : 0;
      const bY = typeof b.y === 'number' ? b.y : 0;
      return aY - bY;
    });

    const allNodeKeys: string[] = [];

    const convertNodeToTreeNode = (node: WorkflowNode): TreeDataNode => {
      const nodeData = nodeMap[node.id];
      const nodeKey = String(nodeData.id);
      allNodeKeys.push(nodeKey);

      return {
        title: renderTitle(nodeData),
        key: nodeKey,
        children:
          nodeData.children.length > 0
            ? nodeData.children
                .sort((a, b) => (a.y || 0) - (b.y || 0))
                .map((child) => convertNodeToTreeNode(child))
            : undefined,
        icon: getNodeIcon(nodeData.state, nodeData.type),
        position:
          nodeData.x !== undefined && nodeData.y !== undefined
            ? { x: nodeData.x, y: nodeData.y }
            : undefined,
      };
    };

    const treeNodes = rootNodes.map((rootNode) => convertNodeToTreeNode(rootNode));
    setAllKeys(allNodeKeys);
    return treeNodes;
  };

  useEffect(() => {
    if (nodeList && Array.isArray(nodeList)) {
      setLoading(true);
      try {
        const processedTreeData = processDataToTree(nodeList, edgeList || []);
        setTreeData(processedTreeData);
      } catch (error) {
        console.error('Error processing tree data:', error);
        message.error('Error processing workflow data');
        setTreeData([]);
      } finally {
        setLoading(false);
      }
    } else {
      setTreeData([]);
    }
  }, [nodeList, edgeList]);

  const onSelect: TreeProps['onSelect'] = (selectedKeysValue, info) => {
    if (selectedKeysValue.length > 0) {
      const selectedNodePosition = (info.node as TreeDataNode).position;
      const selectedNodeId = String(info.node.key);
      setSelectedKeys(selectedKeysValue);

      if (selectedNodePosition) {
        setTemporaryCenteredNodeId(selectedNodeId.toString());

        setTimeout(() => {
          setTemporaryCenteredNodeId(null);
        }, 800);

        setCenter(selectedNodePosition.x + 130, selectedNodePosition.y + 75, {
          duration: 0,
          zoom: 1,
        });
      } else {
        console.error('Selected node position not found');
      }
    } else {
      setSelectedKeys([]);
    }
  };

  const onExpand = (expandedKeysValue: React.Key[]) => {
    setExpandedKeys(expandedKeysValue);
  };

  const expandAll = useCallback(() => {
    setExpandedKeys(allKeys);
  }, [allKeys]);

  const collapseAll = useCallback(() => {
    setExpandedKeys([]);
  }, []);

  return (
    <div style={{ height: 'calc(100% - 50px)' }}>
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
          <Tooltip title="Expand All">
            <Button
              size="small"
              onClick={expandAll}
              icon={<ExpandOutlined />}
              disabled={loading || treeData.length === 0}
            />
          </Tooltip>
          <Tooltip title="Collapse All">
            <Button
              size="small"
              onClick={collapseAll}
              icon={<ShrinkOutlined />}
              disabled={loading || treeData.length === 0}
            />
          </Tooltip>
        </div>
      </div>

      <div style={{ padding: '12px', height: 'calc(100% - 60px)', overflow: 'auto' }}>
        {loading ? (
          <div style={{ textAlign: 'center', marginTop: '100px' }}>
            <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
            <div style={{ marginTop: '8px' }}>Loading workflow data...</div>
          </div>
        ) : treeData.length > 0 ? (
          <div>
            {treeData.map((rootNode) => (
              <div key={rootNode.key} style={{ marginBottom: '12px' }}>
                <Tree
                  showLine={rootNode.children && rootNode.children.length > 0}
                  showIcon
                  switcherIcon={<DownOutlined />}
                  onSelect={onSelect}
                  onExpand={onExpand}
                  expandedKeys={expandedKeys}
                  selectedKeys={selectedKeys}
                  treeData={[rootNode]}
                />
              </div>
            ))}
          </div>
        ) : (
          <Empty description="No workflow data available" style={{ marginTop: '100px' }} />
        )}
      </div>
    </div>
  );
};

export default AnalysisTree;
