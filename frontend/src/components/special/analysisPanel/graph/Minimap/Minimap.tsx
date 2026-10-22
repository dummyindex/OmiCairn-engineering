import { NodeType } from '@/constants/node';
import { Spin } from 'antd';
import React, { useEffect, useState } from 'react';
import { Background, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import { useModel } from 'umi';
import styles from './Minimap.module.css';

const MinimapComponent: React.FC<{ nodes: any[]; isMinimapVisible }> = ({
  nodes,
  isMinimapVisible,
}) => {
  const [newNodeStateMap, setNodeStatefoMap] = useState<Map<string, any>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const { currentSelectedNodes } = useModel('analysis');

  useEffect(() => {
    if (isMinimapVisible) {
      async function fetchAllNodeInfo() {
        setIsLoading(true);
        const newNodeStateMap = new Map();
        for (const node of nodes) {
          newNodeStateMap.set(node.id, node.data.state);
        }
        setNodeStatefoMap(newNodeStateMap);
        setIsLoading(false);
      }
      fetchAllNodeInfo();
    }
  }, [nodes, isMinimapVisible]);

  const getNodeColor = (node) => {
    if (node.type === NodeType.DATA_NODE) {
      return '#4F56A8';
    }

    if (node.type === NodeType.DATA_NODE_V2) {
      return '#9563f1ff';
    }

    const state = newNodeStateMap.get(node.id);
    switch (state) {
      case 'original':
        return '#E2E4EC';
      case 'pending':
        return 'orange';
      case 'cancelled':
        return '#E2E4EC';
      case 'running':
        return 'blue';
      case 'debugging':
        return 'blue';
      case 'finished':
        return '#019002';
      case 'failed':
        return '#DA0001';
      default:
        return '#eee';
    }
  };

  const getNodeStrokeColor = () => {
    if (currentSelectedNodes.some((node) => node.id === node.id)) {
      return '#6776CC';
    }
    return 'transparent';
  };

  return (
    <div className={styles.minimapOuterContainer}>
      {isMinimapVisible && (
        <div>
          {isLoading && (
            <div className={styles.loadingSpinnerContainer}>
              <Spin tip="Loading node info..." />
            </div>
          )}
          <MiniMap
            pannable
            zoomable
            ariaLabel="Graph overview minimap"
            nodeColor={getNodeColor}
            nodeStrokeColor={getNodeStrokeColor}
            nodeBorderRadius={4}
            nodeStrokeWidth={35}
            maskColor="rgba(0, 7, 20, 0.2)"
            style={{ opacity: 0.7, borderRadius: 4, fontSize: '1.5vh' }}
          />
          <Background />
        </div>
      )}
    </div>
  );
};

export default MinimapComponent;
