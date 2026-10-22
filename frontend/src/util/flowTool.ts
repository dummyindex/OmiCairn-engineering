import { NodeState, NodeType } from '@/constants/node';

export class FlowTool {
  instance: any;
  edges: any;
  nodes: any;
  nodeMap: Map<string, any>;
  constructor(instance: any) {
    this.instance = instance;
    const obj = instance.toObject();
    const { edges, nodes } = obj;
    this.edges = edges;
    this.nodes = nodes;
    this.nodeMap = this.nodes.reduce((pre: any, cur: any) => {
      pre.set(cur.id, cur);
      return pre;
    }, new Map());
  }

  getNode(nodeId: string) {
    return this.nodeMap.get(nodeId);
  }

  // Look up the node's source name
  checkNodeSource(nodeId: string) {
    const target2EdgeMap = new Map();
    for (const edge of this.edges) {
      // const sourceNode = this.nodeMap.get(edge.source);
      if (target2EdgeMap.has(edge.target)) {
        const edgeList = target2EdgeMap.get(edge.target);
        edgeList.push(edge);
        target2EdgeMap.set(edge.target, edgeList);
      } else {
        target2EdgeMap.set(edge.target, [edge]);
      }
    }
    let findId = nodeId;
    while (target2EdgeMap.get(findId) != undefined) {
      const [sourceEdge] = target2EdgeMap.get(findId);
      findId = sourceEdge.source;
    }

    const firstName = this.nodeMap.get(findId);
    return firstName.data.label;
  }

  // Look up a node by id
  checkNodeById(nodeId: string) {
    return this.nodes.filter((item: any) => {
      if (item.id === nodeId) {
        return item;
      }
    });
  }

  // Find edges connected to the selected node
  checkNodeConnectEdge(nodeArr: any[]) {
    return this.edges.filter((item) => {
      if (nodeArr.includes(item.source) && nodeArr.includes(item.target)) {
        return item;
      }
    });
  }

  // Check predecessor nodes
  checkPreComputable(nodeId: string) {
    const target2EdgeMap = new Map();
    for (const edge of this.edges) {
      // const sourceNode = this.nodeMap.get(edge.source);
      if (target2EdgeMap.has(edge.target)) {
        const edgeList = target2EdgeMap.get(edge.target);
        edgeList.push(edge);
        target2EdgeMap.set(edge.target, edgeList);
      } else {
        target2EdgeMap.set(edge.target, [edge]);
      }
    }

    // check the current node
    if (!target2EdgeMap.has(nodeId)) {
      throw Error('no previous data');
    }

    const queue = target2EdgeMap.get(nodeId);
    const nodeMap = new Map();
    // nodeMap.set(nodeId, this.nodeMap.get(nodeId));
    let index = 0;
    let isTaskRunning = false;
    while (index < queue.length) {
      const e = queue[index];
      const n = this.nodeMap.get(e.source);
      if (nodeMap.has(n.id)) {
        index += 1;
        continue;
      }
      if (!target2EdgeMap.has(n.id)) {
        if (n.type !== NodeType.DATA_NODE && n.type !== NodeType.DATA_NODE_V2) {
          throw Error('no previous data');
        } else {
          queue[index] = '#';
        }
      } else {
        if (n.data.state === NodeState.FINISHED) {
          queue[index] = '#';
        } else if (
          n.data.state === NodeState.PENDING ||
          n.data.state === NodeState.RUNNING ||
          n.data.state === NodeState.DEBUGGING
        ) {
          queue[index] = '#';
          isTaskRunning = true;
        } else {
          nodeMap.set(n.id, n);
          const previousEdgeList = target2EdgeMap.get(n.id);
          queue.push(...previousEdgeList);
        }
      }
      index += 1;
    }

    return {
      isTaskRunning,
      nodeList: Array.from(nodeMap.values()),
      edgeList: queue.filter((edge: any) => {
        return edge !== '#';
      }),
    };
  }

  findPredecessorNodes(nodeId: string): any[] {
    const predecessorNodes: any[] = [];
    const processedNodeIds = new Set<string>();

    const traverseGraph = (currentNodeId: string) => {
      if (processedNodeIds.has(currentNodeId)) {
        return;
      }
      processedNodeIds.add(currentNodeId);

      try {
        const node = this.getNode(currentNodeId);
        if (!node) {
          return;
        }

        const edges = this.instance.toObject().edges;
        const incomingEdges = edges.filter((edge) => edge.target === currentNodeId);

        for (const edge of incomingEdges) {
          const sourceNode = this.getNode(edge.source);
          if (!sourceNode) {
            continue;
          }

          predecessorNodes.push(sourceNode);
          traverseGraph(edge.source);
        }
      } catch (error) {
        console.error(`Error finding predecessor nodes for ${currentNodeId}:`, error);
      }
    };

    traverseGraph(nodeId);
    return predecessorNodes;
  }

  // Discover the whole tree
  findComputableSubtree(nodeId: any) {
    const source2EdgeMap = new Map();
    for (const edge of this.edges) {
      // const sourceNode = this.nodeMap.get(edge.source);
      if (source2EdgeMap.has(edge.source)) {
        const edgeList = source2EdgeMap.get(edge.source);
        edgeList.push(edge);
        source2EdgeMap.set(edge.source, edgeList);
      } else {
        source2EdgeMap.set(edge.source, [edge]);
      }
    }

    const findSubtree = (targetNodeId: any) => {
      const nodes: any = [this.nodeMap.get(targetNodeId)];
      const nextEdgeList = source2EdgeMap.get(targetNodeId);
      const queue = [...(nextEdgeList || [])];
      let index = 0;
      while (index < queue.length) {
        const edgePtr = queue[index];
        nodes.push(this.nodeMap.get(edgePtr.target));
        queue.push(...(source2EdgeMap.get(edgePtr.target) || []));
        index += 1;
      }
      return {
        nodeList: nodes,
        edgeList: queue,
      };
    };
    const triggerNode = this.nodeMap.get(nodeId);
    if (triggerNode.type === NodeType.DATA_NODE || triggerNode.type === NodeType.DATA_NODE_V2) {
      if (!source2EdgeMap.has(triggerNode.id)) {
        return {
          nodeList: [],
          edgeList: [],
        };
      }
      const nextEdges = source2EdgeMap.get(triggerNode.id);
      const subTreeList = nextEdges.map((edge: any) => {
        return findSubtree(edge.target);
      });
      return subTreeList.reduce(
        (pre: any, cur: any) => {
          const { nodeList, edgeList } = pre;
          nodeList.push(...cur.nodeList);
          edgeList.push(...cur.edgeList);
          return {
            nodeList,
            edgeList,
          };
        },
        { nodeList: [], edgeList: [] },
      );
    } else if (
      triggerNode.type === NodeType.COMPUTATION_NODE ||
      triggerNode.type === NodeType.COMPUTATION_NODE_V2
    ) {
      const subTree = findSubtree(triggerNode.id);
      return subTree;
    } else {
      throw Error('except node type');
    }
  }

  // Find all successor nodes of a node
  findNextComputable(nodeId: string) {
    // map of all nodes that have successors
    const source2EdgeMap = new Map();
    for (const edge of this.edges) {
      // const sourceNode = this.nodeMap.get(edge.source);
      if (source2EdgeMap.has(edge.source)) {
        const edgeList = source2EdgeMap.get(edge.source);
        edgeList.push(edge);
        source2EdgeMap.set(edge.source, edgeList);
      } else {
        source2EdgeMap.set(edge.source, [edge]);
      }
    }

    const findSuftree = (targetNodeId: any) => {
      const nodes: any = new Map();
      // nodes.set(targetNodeId, source);
      const nextEdgeList = source2EdgeMap.get(targetNodeId);
      const queue = [...(nextEdgeList || [])];
      let index = 0;
      while (index < queue.length) {
        const edgePtr = queue[index];
        nodes.set(edgePtr.target, edgePtr.source);
        queue.push(...(source2EdgeMap.get(edgePtr.target) || []));
        index += 1;
      }
      return {
        nodesMapList: nodes,
        edgeList: queue,
      };
    };

    const nodeSuffixList = findSuftree(nodeId).nodesMapList;
    const nodeSufList: any = [];
    for (const [key] of nodeSuffixList) {
      nodeSufList.push(key);
    }

    return [nodeId, ...nodeSufList];
  }

  // Get ids of nodes whose predecessors have data
  checkPreDataNode(nodeId: string) {
    const target2EdgeMap = new Map();
    // map of all nodes that have predecessors
    for (const edge of this.edges) {
      // const sourceNode = this.nodeMap.get(edge.source);
      if (target2EdgeMap.has(edge.target)) {
        const edgeList = target2EdgeMap.get(edge.target);
        edgeList.push(edge);
        target2EdgeMap.set(edge.target, edgeList);
      } else {
        target2EdgeMap.set(edge.target, [edge]);
      }
    }

    // check the current node
    if (!target2EdgeMap.has(nodeId)) {
      throw Error('no previous data');
    }

    const queue = target2EdgeMap.get(nodeId);
    const nodeMap = new Map();
    // nodeMap.set(nodeId, this.nodeMap.get(nodeId));
    let index = 0;
    while (index < queue.length) {
      const e = queue[index];
      const n = this.nodeMap.get(e.source);
      if (nodeMap.has(n.id)) {
        index += 1;
        continue;
      }
      if (!target2EdgeMap.has(n.id)) {
        if (n.type !== NodeType.DATA_NODE && n.type !== NodeType.DATA_NODE_V2) {
          throw Error('no previous data');
        } else {
          return n.id;
        }
      } else {
        if (n.data.state === NodeState.FINISHED) {
          return n.id;
        } else {
          nodeMap.set(n.id, n);
          const previousEdgeList = target2EdgeMap.get(n.id);
          queue.push(...previousEdgeList);
        }
      }
      index += 1;
    }
  }

  checkNextDataNodes(nodeId: string) {
    const source2EdgeMap = new Map<string, any[]>();

    this.edges.forEach((edge) => {
      const edgeList = source2EdgeMap.get(edge.source) || [];
      edgeList.push(edge);
      source2EdgeMap.set(edge.source, edgeList);
    });

    if (!source2EdgeMap.has(nodeId)) {
      return [];
    }

    const queue = source2EdgeMap.get(nodeId);
    const nextNodes = queue?.map((edge) => edge.target);

    return nextNodes;
  }

  // Get the id list
  getIdList = (result: any) => {
    const { nodeList, edgeList } = result;

    const nodeIdList = nodeList.map((node: any) => {
      return node.id;
    });
    let edgeIdList;
    if (edgeList !== undefined) {
      edgeIdList = edgeList.map((edge: any) => {
        return edge.id;
      });
    }
    return { nodeIdList, edgeIdList };
  };
}

const constructTarget2SourceMap = (edges: any) => {
  const target2SourceMap = new Map();
  for (const edge of edges) {
    if (target2SourceMap.has(edge.targetNodeId)) {
      const sourceList = target2SourceMap.get(edge.targetNodeId);
      sourceList.push(edge.sourceNodeId);
      target2SourceMap.set(edge.targetNodeId, sourceList);
    } else {
      target2SourceMap.set(edge.targetNodeId, [edge.sourceNodeId]);
    }
  }
  return target2SourceMap;
};

export const findHeadNodes = (edges: any, nodes: any) => {
  const target2EdgeMap = constructTarget2SourceMap(edges);

  const headNodeList = nodes.filter((node: any) => {
    return !target2EdgeMap.has(node.id);
  });

  return headNodeList;
};

export const organizeAnalysisTree = (edges: any, nodes: any) => {
  // const source2TargetMap = constructSource2TargetMap(edges);
  const target2SourceMap = constructTarget2SourceMap(edges);
  const headerNodeList = nodes.filter((node: any) => {
    return !target2SourceMap.has(node.id);
  });

  const nodeMap = new Map();
  nodes.forEach((node: any) => {
    nodeMap.set(node.id, { ...node, key: node.id + '', children: [] });
  });

  edges.forEach((edge: any) => {
    const sourceNode = nodeMap.get(edge.sourceNodeId);
    const targetNode = nodeMap.get(edge.targetNodeId);
    if (sourceNode && targetNode) {
      sourceNode.children.push(targetNode);
    }
  });

  const treeData = headerNodeList.map((node: any) => nodeMap.get(node.id));
  return treeData;
};
