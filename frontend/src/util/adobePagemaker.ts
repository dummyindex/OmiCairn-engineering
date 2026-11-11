import { NodeType } from '@/constants/node';
import { requestUpdateNodePosition, requestUpdateNodePositionList } from '@/request/node';
import { message } from 'antd';

export class AdobePagemaker {
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

  //   Get all position coordinates
  getPosition() {
    const nodePositionMap = new Map();
    for (const node of this.nodes) {
      // const sourceNode = this.nodeMap.get(edge.source);
      nodePositionMap.set(node.id, node.position);
    }
    return nodePositionMap;
  }

  //   Get this node's position
  getNodePosition(nodeId: string) {
    return this.nodeMap.get(nodeId).position;
  }

  // Check whether any fb occupies the given positions
  judgePosition(positionListAfterMoving: any[], currentPositionList: any[] | null) {
    function isCoordinateEqual(coord1, coord2) {
      return coord1.x === coord2.x && coord1.y === coord2.y;
    }

    let allPositionList: any[] = [...this.getPosition().values()];

    if (currentPositionList) {
      // remove the node's current position from allPositionList so it does not affect the node's position update
      allPositionList = allPositionList.filter(
        (item1) => !currentPositionList.some((item2) => isCoordinateEqual(item1, item2)),
      );
    }

    for (const obj1 of allPositionList) {
      // get the property values of objects in the first array
      const x = obj1.x;
      const y = obj1.y;

      // iterate over objects in the second array
      for (const obj2 of positionListAfterMoving) {
        // get the property values of objects in the second array
        const x1 = obj2.x;
        const y1 = obj2.y;

        // equal property values mean the sets intersect
        if (x === x1 && y == y1) {
          return true;
        }
      }
    }

    // no intersection, return false
    return false;
  }

  // Count how many nodes are connected after a given node
  getSufNodeCount(nodeId) {
    const count = this.edges.reduce((accumulator, currentValue) => {
      if (currentValue.source === nodeId) {
        return accumulator + 1;
      } else {
        return accumulator;
      }
    }, 0);
    return count;
  }

  // Get the predecessor nodes that need to move
  getPreNodeToMove(nodeId) {
    // array to store predecessor node IDs related to the current node
    const connectedPredecessorNodeIdList = [];
    const sourceId = nodeId;

    const findPredecessors = (currentSourceId) => {
      let found = false;
      let nextSourceId = currentSourceId; // new variable with an initial value

      // iterate over all edges
      this.edges.forEach((edge) => {
        if (edge.target === currentSourceId) {
          // if the edge's target equals the current node's ID, the edge's source is a predecessor
          const type = this.nodeMap.get(edge.source).type;
          if (
            this.getSufNodeCount(edge.source) === 1 &&
            !(type in [NodeType.DATA_NODE, NodeType.DATA_NODE_V2])
          ) {
            nextSourceId = edge.source; // update the new variable
            connectedPredecessorNodeIdList.push(edge.source);
            found = true;
          }
        }
      });

      if (found) {
        // if more predecessors were found, keep searching recursively
        findPredecessors(nextSourceId); // pass the new variable
      }
    };

    findPredecessors(sourceId);

    return connectedPredecessorNodeIdList;
  }

  updatePositionAndMoveNodesOnConnectSingleNode = async (
    target,
    positionX,
    positionY,
    nodeToMoveList,
    updateNodePosition,
  ) => {
    updateNodePosition([{ node_id: target, x: positionX, y: positionY }]);
    await requestUpdateNodePosition(target, positionX, positionY);
    const nodeList = nodeToMoveList.map((item) => {
      return { node_id: item, x: this.getNodePosition(item).x, y: positionY };
    });
    updateNodePosition(nodeList);
    await requestUpdateNodePositionList(nodeList);
    // if the position is free, update the node position
  };

  // Move function when connecting a single node
  async moveLocationOnConnectSingleNode(
    source,
    target,
    sourcePosition,
    targetPosition,
    updateNodePosition,
  ) {
    let flag = 0;
    const positionX = sourcePosition.x + 400;
    const targetpositionX = targetPosition.x;
    let positionY = sourcePosition.y + 200 * flag;
    const targetpositionY = targetPosition.y;

    while (true) {
      positionY = sourcePosition.y + 200 * flag;
      flag++;
      if (
        (targetpositionX === positionX && positionY === targetpositionY) ||
        !this.judgePosition([{ x: positionX, y: positionY }], null)
      ) {
        if (positionY !== sourcePosition.y && this.getSufNodeCount(source) == 0) {
          // call the externally defined async function to update the node position
          const currentPositionY = positionY;
          const nodeToMoveList = [...this.getPreNodeToMove(source), source];

          let nodeToMovePositionList = nodeToMoveList.map((item) => {
            return { x: this.getNodePosition(item).x, y: currentPositionY };
          });
          const nodeToMoveCurrentPositionList = nodeToMoveList.map((item) => {
            return { x: this.getNodePosition(item).x, y: this.getNodePosition(item).y };
          });
          //predecessors need to move and the connected node does not
          if (!this.judgePosition(nodeToMovePositionList, null)) {
            await this.updatePositionAndMoveNodesOnConnectSingleNode(
              target,
              positionX,
              currentPositionY,
              nodeToMoveList,
              updateNodePosition,
            );
            break;
          }

          let currentPositionYforloop = positionY;
          //predecessors need to move and the connected node also needs to move
          while (true) {
            // check and move nodes down
            const currentY = currentPositionYforloop;
            nodeToMovePositionList = nodeToMoveList.map((item) => {
              return { x: this.getNodePosition(item).x, y: currentY };
            });

            nodeToMovePositionList.push({ x: positionX, y: currentY });
            nodeToMoveCurrentPositionList.push({ x: targetpositionX, y: targetpositionY });
            if (!this.judgePosition(nodeToMovePositionList, nodeToMoveCurrentPositionList)) {
              await this.updatePositionAndMoveNodesOnConnectSingleNode(
                target,
                positionX,
                currentY,
                nodeToMoveList,
                updateNodePosition,
              );
              positionY = currentPositionYforloop;
              break;
            }
            currentPositionYforloop += 200;
          }
        } else {
          await requestUpdateNodePosition(target, positionX, positionY);
          updateNodePosition([{ node_id: target, x: positionX, y: positionY }]);
        }
        // if the return value is false, stop the loop
        break;
      }
    }

    return { positionX, positionY };
  }

  // Move function when connecting multiple nodes
  async moveLocationOnConnectMultipleNode(source, target, updateNodePosition) {
    const targetPosition = this.getNodePosition(target);
    const sourcePosition = this.getNodePosition(source);
    const { positionX, positionY } = await this.moveLocationOnConnectSingleNode(
      source,
      target,
      sourcePosition,
      targetPosition,
      updateNodePosition,
    );

    const differenceX = targetPosition.x - positionX;
    const differenceY = targetPosition.y - positionY;
    const findNextComputableList = this.findNextComputable(target);
    const flag = 0;
    const updatePositionY = 200 * flag;
    // positions of successor nodes
    const findNextComputablePositionList = findNextComputableList.map((item) => {
      const { x, y } = this.getNodePosition(item);

      const positionX = x - differenceX;
      const positionY = y - differenceY + updatePositionY;

      return { x: positionX, y: positionY };
    });
    const findNextCurrentComputablePositionList = findNextComputableList.map((item) => {
      const { x, y } = this.getNodePosition(item);
      return { x: x, y: y };
    });

    if (differenceX === 0 && differenceY === 0) {
      // no position update needed
      return;
    } else {
      if (this.judgePosition(findNextComputablePositionList, null)) {
        // new position is occupied; keep shifting by +200
        if (this.getSufNodeCount(source) == 0) {
          // call the externally defined async function to update the node position
          // predecessor list also needs to move down
          let currentPositionYforloop = updatePositionY;
          const nodeToMoveList = [...this.getPreNodeToMove(source), source];
          const nodeToMoveCurrentPositionList = nodeToMoveList.map((item) => {
            return {
              x: this.getNodePosition(item).x,
              y: this.getNodePosition(item).y,
            };
          });

          while (true) {
            // check and move nodes down
            const currentY = currentPositionYforloop;

            const nodeToMovePositionList = nodeToMoveList.map((item) => {
              return {
                x: this.getNodePosition(item).x,
                y: targetPosition.y - differenceY + currentY,
              };
            });

            const findNextComputablePositionList = findNextComputableList.map((item) => {
              const { x, y } = this.getNodePosition(item);

              const positionX = x - differenceX;
              const positionY = y - differenceY + currentY;
              return { x: positionX, y: positionY };
            });
            if (
              !this.judgePosition(
                findNextComputablePositionList,
                findNextCurrentComputablePositionList,
              ) &&
              !this.judgePosition(nodeToMovePositionList, nodeToMoveCurrentPositionList)
            ) {
              findNextComputableList.push(target);
              // nodeToMoveList.forEach((item) => {
              //   findNextComputableList.push(item);
              // });
              // const promiseArray: any = [];
              const findNextComputableToMoveList = findNextComputableList.map((item) => {
                const { x, y } = this.getNodePosition(item);
                const currentPositionX = x - differenceX;
                const currentPositionY = y - differenceY + currentY;
                // updateNodePosition(item, currentPositionX, currentPositionY);
                return { node_id: item, x: currentPositionX, y: currentPositionY };
              });

              // if the position is free, update the node position

              const nodeToMovePositionList = nodeToMoveList.map((item) => {
                const { x } = this.getNodePosition(item);
                const currentPositionX = x;
                const currentPositionY = targetPosition.y - differenceY + currentY;
                return { node_id: item, x: currentPositionX, y: currentPositionY };
                // promiseArray.push(updateNodePosition(item, currentPositionX, currentPositionY));
              });
              const nodeList = findNextComputableToMoveList.concat(nodeToMovePositionList);
              updateNodePosition(nodeList);
              await requestUpdateNodePositionList(nodeList);
              break;
            }
            currentPositionYforloop += 200;
          }
        } else {
          //  predecessor list does not need to move down
          let currentPositionYforloop = updatePositionY;
          while (true) {
            // check and move nodes down
            const currentY = currentPositionYforloop;
            const findNextComputablePositionList = findNextComputableList.map((item) => {
              const { x, y } = this.getNodePosition(item);

              const positionX = x - differenceX;
              const positionY = y - differenceY + currentY;

              return { x: positionX, y: positionY };
            });
            if (
              !this.judgePosition(
                findNextComputablePositionList,
                findNextCurrentComputablePositionList,
              )
            ) {
              findNextComputableList.push(target);
              const nodeList = findNextComputableList.map((item) => {
                const { x, y } = this.getNodePosition(item);
                const currentPositionX = x - differenceX;
                const currentPositionY = y - differenceY + currentY;
                return { node_id: item, x: currentPositionX, y: currentPositionY };
                // promiseArray.push(updateNodePosition(item, currentPositionX, currentPositionY));
              });
              updateNodePosition(nodeList);
              await requestUpdateNodePositionList(nodeList);
              break;
            }
            currentPositionYforloop += 200;
          }
        }
      } else {
        //  new position is free
        const nodeList = findNextComputableList.map((item) => {
          const { x, y } = this.getNodePosition(item);
          const currentPositionX = x - differenceX;
          const currentPositionY = y - differenceY;
          return { node_id: item, x: currentPositionX, y: currentPositionY };
        });
        updateNodePosition(nodeList);
        await requestUpdateNodePositionList(nodeList);
      }
    }
  }

  // visualpanel triggers adding multiple nodes
  async moveLocationOnVisualpanel(
    source,
    target,
    sourcePosition,
    targetPosition,
    findNextComputableList,
    findNextComputableNodePositionList,
    updateNodePosition,
  ) {
    const { positionX, positionY } = await this.moveLocationOnConnectSingleNode(
      source,
      target,
      sourcePosition,
      targetPosition,
      updateNodePosition,
    );

    console.log(positionX, positionY);

    const differenceX = targetPosition.x - positionX;
    const differenceY = targetPosition.y - positionY;
    const flag = 0;
    const updatePositionY = 200 * flag;
    // positions of successor nodes
    console.log('findNextComputableNodePositionList', findNextComputableNodePositionList);

    const findNextComputablePositionList = findNextComputableList.map((item, index) => {
      const positionX = findNextComputableNodePositionList[index].x - differenceX;
      const positionY = findNextComputableNodePositionList[index].y - differenceY + updatePositionY;

      return { x: positionX, y: positionY };
    });
    const findNextCurrentComputablePositionList = findNextComputableList.map((item, index) => {
      return {
        x: findNextComputableNodePositionList[index].x,
        y: findNextComputableNodePositionList[index].y,
      };
    });

    if (differenceX === 0 && differenceY === 0) {
      // no position update needed
      return;
    } else {
      if (this.judgePosition(findNextComputablePositionList, null)) {
        // new position is occupied; keep shifting by +200
        if (this.getSufNodeCount(source) == 0) {
          // call the externally defined async function to update the node position
          // predecessor list also needs to move down
          let currentPositionYforloop = updatePositionY;
          const nodeToMoveList = [...this.getPreNodeToMove(source), source];
          const nodeToMoveCurrentPositionList = nodeToMoveList.map((item) => {
            return {
              x: this.getNodePosition(item).x,
              y: this.getNodePosition(item).y,
            };
          });

          while (true) {
            // check and move nodes down
            const currentY = currentPositionYforloop;

            const nodeToMovePositionList = nodeToMoveList.map((item) => {
              return {
                x: this.getNodePosition(item).x,
                y: targetPosition.y - differenceY + currentY,
              };
            });

            const findNextComputablePositionList = findNextComputableList.map((item, index) => {
              const positionX = findNextComputableNodePositionList[index].x - differenceX;
              const positionY =
                findNextComputableNodePositionList[index].y - differenceY + currentY;

              return { x: positionX, y: positionY };
            });
            if (
              !this.judgePosition(
                findNextComputablePositionList,
                findNextCurrentComputablePositionList,
              ) &&
              !this.judgePosition(nodeToMovePositionList, nodeToMoveCurrentPositionList)
            ) {
              findNextComputableList.push(target);
              findNextComputableNodePositionList.push({
                x: targetPosition.x,
                y: targetPosition.y,
              });
              const findNextComputableToMoveList = findNextComputableList.map((item, index) => {
                const currentPositionX = findNextComputableNodePositionList[index].x - differenceX;
                const currentPositionY =
                  findNextComputableNodePositionList[index].y - differenceY + currentY;
                return { node_id: item, x: currentPositionX, y: currentPositionY };
              });

              // if the position is free, update the node position

              const nodeToMovePositionList = nodeToMoveList.map((item) => {
                const { x } = this.getNodePosition(item);
                const currentPositionX = x;
                const currentPositionY = targetPosition.y - differenceY + currentY;
                return { node_id: item, x: currentPositionX, y: currentPositionY };
              });
              const nodeList = findNextComputableToMoveList.concat(nodeToMovePositionList);
              updateNodePosition(nodeList);
              await requestUpdateNodePositionList(nodeList);
              break;
            }
            currentPositionYforloop += 200;
          }
        } else {
          //  predecessor list does not need to move down
          let currentPositionYforloop = updatePositionY;
          while (true) {
            // check and move nodes down
            const currentY = currentPositionYforloop;
            const findNextComputablePositionList = findNextComputableList.map((item, index) => {
              const positionX = findNextComputableNodePositionList[index].x - differenceX;
              const positionY =
                findNextComputableNodePositionList[index].y - differenceY + currentY;

              return { x: positionX, y: positionY };
            });
            if (
              !this.judgePosition(
                findNextComputablePositionList,
                findNextCurrentComputablePositionList,
              )
            ) {
              findNextComputableList.push(target);
              findNextComputableNodePositionList.push({
                x: targetPosition.x,
                y: targetPosition.y,
              });
              const nodeList = findNextComputableList.map((item, index) => {
                const currentPositionX = findNextComputableNodePositionList[index].x - differenceX;
                const currentPositionY =
                  findNextComputableNodePositionList[index].y - differenceY + currentY;
                return { node_id: item, x: currentPositionX, y: currentPositionY };
                // promiseArray.push(updateNodePosition(item, currentPositionX, currentPositionY));
              });
              console.log('nodeList', nodeList);

              updateNodePosition(nodeList);
              await requestUpdateNodePositionList(nodeList);
              break;
            }
            currentPositionYforloop += 200;
          }
        }
      } else {
        //  new position is free
        const nodeList = findNextComputableList.map((item, index) => {
          const currentPositionX = findNextComputableNodePositionList[index].x - differenceX;
          const currentPositionY = findNextComputableNodePositionList[index].y - differenceY;
          return { node_id: item, x: currentPositionX, y: currentPositionY };
        });
        updateNodePosition(nodeList);
        await requestUpdateNodePositionList(nodeList);
      }
    }
  }

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

    const nodeSufList = [...findSuftree(nodeId).nodesMapList.keys()];
    return nodeSufList;
  }

  // Get the branch list and orphan list
  getBranchListAndSingleList() {
    const nodeMap = this.nodeMap;
    const branchRootList: string[] = [];
    const edgeTargetMap = new Map();
    const edgeSourceMap = new Map();
    const singleNodeList: string[] = [];
    // get the nodeMap of nodes without predecessors
    for (const edge of this.edges) {
      edgeTargetMap.set(edge.target, edge);
      edgeSourceMap.set(edge.source, edge);
    }
    nodeMap.forEach((item) => {
      if (!edgeTargetMap.has(item.id)) {
        if (!edgeSourceMap.has(item.id)) {
          singleNodeList.push(item.id);
        } else {
          branchRootList.push(item.id);
        }
      }
    });
    const branchMapList = branchRootList.map((item) => {
      const currentBranchMap = new Map();
      const findNextNodeist = this.findNextComputable(item);
      findNextNodeist.push(item);
      return currentBranchMap.set(item, findNextNodeist);
    });
    return { branchMapList, singleNodeList };
  }

  // Breadth-first traversal of an n-ary tree
  // Find child nodes
  findchildren(treeNote: string) {
    const childrenString = [];
    for (const edge of this.edges) {
      if (edge.source === treeNote) {
        childrenString.push(edge.target);
      }
    }

    return { id: treeNote, children: childrenString };
  }

  //Build an n-ary tree
  buildTree(treeNote: string) {
    const value = this.findchildren(treeNote);
    if (value.children.length == 0) {
      return { id: value.id, children: [] };
    }

    // TODO code to attach the node under the root node
    const childrenTree = value.children.map((element) => {
      return this.buildTree(element);
    });

    // return the current node and its subtree
    return { ...value, children: childrenTree };
  }

  // Depth-first traversal to lay out the compact tree
  depthFirstTraversal(root, nodesMap, levelNodeMap, path = []) {
    if (!root) {
      return;
    }
    path.push(root.id);

    for (const child of root.children) {
      const childrenPosition = child.children.map((element) => {
        return nodesMap.get(element.id).y;
      });

      if (child.children.length > 0) {
        if (nodesMap.get(child.id).y > Math.min(...childrenPosition)) {
          let updatePositionY = 200;
          const nodeToMove = [];
          const childPositinList = this.edges
            .filter((element) => element.source === child.id)
            .map((element) => {
              const targetNode = nodesMap.get(element.target);
              nodeToMove.push(element.target);
              return { id: element.target, x: targetNode.x, y: targetNode.y };
            });

          if (childPositinList.length > 0) {
            const maxYValueObject = childPositinList.reduce((maxYObject, currentObject) => {
              if (!maxYObject || currentObject.y > maxYObject.y) {
                return currentObject;
              }
              return maxYObject;
            });
            const maxYValueObjectId = maxYValueObject.id;

            let newArray;
            levelNodeMap.forEach((value) => {
              const targetIndex = value.indexOf(maxYValueObjectId);

              if (targetIndex != -1) {
                newArray = value.slice(targetIndex + 1);

                newArray.forEach((element) => {
                  nodeToMove.push(element);
                });
              } else {
                newArray = [];
              }
            });
          }

          while (true) {
            const currentY = updatePositionY;
            const nodeToMovePositionList = nodeToMove.map((item) => {
              if (nodesMap.has(item)) {
                const y = nodesMap.get(item).y;

                const currentPositionY = y + currentY;
                return currentPositionY;
              }
            });

            if (nodesMap.get(child.id).y == Math.min(...nodeToMovePositionList)) {
              nodeToMove.forEach((item) => {
                if (nodesMap.has(item)) {
                  const { x, y } = nodesMap.get(item);
                  const currentPositionX = x;
                  const currentPositionY = y + currentY;

                  nodesMap.set(item, { x: currentPositionX, y: currentPositionY });
                }
              });
              break;
            }
            updatePositionY += 200;
          }
        } else if (nodesMap.get(child.id).y < Math.min(...childrenPosition)) {
          const getPreNodeToMove = [...path, child.id].reverse();
          getPreNodeToMove.forEach((item) => {
            const nodeToMove = [item];
            const childPositinList = this.edges
              .filter((element) => element.source === item)
              .map((element) => nodesMap.get(element.target).y);
            let newArray;
            levelNodeMap.forEach((value) => {
              const targetIndex = value.indexOf(item);
              if (value.indexOf(item) != -1) {
                newArray = value.slice(targetIndex + 1);
                newArray.forEach((element) => {
                  nodeToMove.push(element);
                });
              } else {
                newArray = [];
              }
            });

            if (nodesMap.get(item).y < Math.min(...childPositinList)) {
              let updatePositionY = 200;
              while (true) {
                const currentY = updatePositionY;
                const nodeToMovePositionList = nodeToMove.map((node) => {
                  if (nodesMap.has(node)) {
                    const y = nodesMap.get(node).y;
                    const currentPositionY = y + currentY;
                    return currentPositionY;
                  }
                });

                if (Math.min(...childPositinList) == Math.min(...nodeToMovePositionList)) {
                  nodeToMove.forEach((item) => {
                    if (nodesMap.has(item)) {
                      const { x, y } = nodesMap.get(item);
                      const currentPositionX = x;
                      const currentPositionY = y + currentY;

                      nodesMap.set(item, { x: currentPositionX, y: currentPositionY });
                    }
                  });
                  break;
                }
                updatePositionY += 200;
              }
            }
          });
        }
      }
      this.depthFirstTraversal(child, nodesMap, levelNodeMap, path); // recursively traverse child nodes
    }
    path.pop();
    return nodesMap;
  }

  async branchSearchTraversal(root, treeHeight, nodeWidth, nodeHeight) {
    const result: number[] = [];
    const levelNodeMap: Map<any, any> = new Map();
    const queue: any[] = [];
    let currentLevelWidth = 0;
    let nextLevelWidth = 0;

    if (!root) {
      throw new Error('The tree is empty');
    }
    try {
      const nodesMap = new Map();
      nodesMap.set(root.id, { x: 0, y: treeHeight });
      queue.push(root);
      currentLevelWidth = 1;

      // breadth-first pass to compact the tree
      while (queue.length > 0) {
        const currentNode = queue.shift();
        let currentLevelNode = [];
        currentLevelWidth--;
        for (const child of currentNode?.children) {
          queue.push(child);
          nextLevelWidth++;
        }
        if (currentLevelWidth === 0) {
          currentLevelNode = JSON.parse(JSON.stringify(queue)).map((item) => item.id);
          result.push(nextLevelWidth);
          levelNodeMap.set(result.length, currentLevelNode);
          currentLevelWidth = nextLevelWidth;
          nextLevelWidth = 0;
        }
      }
      levelNodeMap.forEach((value, key) => {
        // if (value.length == 0) return;
        value.forEach((element, index) => {
          nodesMap.set(element, { x: key * nodeWidth, y: nodeHeight * index + treeHeight });
        });
      });
      const newNodesMap = this.depthFirstTraversal(root, nodesMap, levelNodeMap);

      let maxY = -Infinity;
      const nodePositionList: any[] = [];
      for (const [key, value] of newNodesMap) {
        maxY = Math.max(maxY, parseInt(value.y));
        nodePositionList.push({ node_id: key, x: value.x, y: value.y });
      }
      return [nodePositionList, maxY];
    } catch {
      message.error('Global layout failure');
    }
  }
}
