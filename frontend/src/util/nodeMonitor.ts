import { NodeState } from '@/constants/node';
import type { Node } from '@/interfaces/node';
import { requestNodeListByIdx } from '@/request/node';

interface NodeObserverConstructorProps {
  currentState?: string;
  currentLockState?: boolean;
  onLocked?: (n: Node) => void;
  onUnlocked?: (n: Node) => void;
  onStateChange?: (o: string, n: string, node: Node) => void;
}

const INTERVAL = 3000;

export class NodeObserver {
  onStateChange: (o: string, n: string, nn: Node) => void;
  currentState: any;
  currentLockState: boolean;
  onLocked: (n: Node) => void;
  onUnlocked: (n: Node) => void;

  constructor(props: NodeObserverConstructorProps) {
    const { currentState, onStateChange, currentLockState, onLocked, onUnlocked } = props;
    this.currentState = currentState || NodeState.ORIGINAL;
    this.currentLockState = currentLockState || false;
    this.onStateChange = onStateChange || (() => {});
    this.onLocked = onLocked || (() => {});
    this.onUnlocked = onUnlocked || (() => {});
  }

  updateNode(node: Node) {
    // state
    const oldState = this.currentState;
    if (this.currentState !== node.state) {
      this.onStateChange(oldState, node.state, node);
    }
    this.currentState = node.state;

    // locked
    const oldLockedState = this.currentLockState;
    if (oldLockedState && !node.locked) {
      this.onUnlocked(node);
    } else if (!oldState && node.locked) {
      this.onLocked(node);
    }
    this.currentLockState = node.locked;
  }
}

interface GlobalObserverConstructorProps {
  onUpdate?: (nodeList: Node[]) => void;
}

export class GlobalObserver {
  onUpdate: (nodeList: Node[]) => void;
  constructor(props: GlobalObserverConstructorProps) {
    const { onUpdate } = props;
    this.onUpdate = onUpdate || (() => {});
  }

  update(nodeList: Node[]) {
    this.onUpdate(nodeList);
  }
}

class NodeMonitor {
  globalObserverMap: Map<string, GlobalObserver>;
  nodeObserverMap: Map<number, NodeObserver>;
  timer: NodeJS.Timer;
  constructor() {
    this.globalObserverMap = new Map();
    this.nodeObserverMap = new Map();
    this.timer = setInterval(() => {
      this.work();
    }, INTERVAL);
  }

  registerGlobalObserver(observerId: string, observer: GlobalObserver) {
    this.globalObserverMap.set(observerId, observer);
  }

  unregisterGlobalObserver(observerId: string) {
    this.globalObserverMap.delete(observerId);
  }

  registerNodeObserver(nodeId: any, observer: NodeObserver) {
    // if (typeof nodeId === 'string') {
    //   nodeId = parseInt(nodeId);
    // }
    this.nodeObserverMap.set(parseInt(nodeId), observer);
  }

  unregisterNodeObserver(nodeId: any) {
    // if (typeof nodeId === 'string') {
    //   nodeId = parseInt(nodeId);
    // }
    this.nodeObserverMap.delete(parseInt(nodeId));
  }

  async work() {
    const nodeIdx = Array.from(this.nodeObserverMap.keys());
    if (nodeIdx.length === 0) {
      return;
    }
    const { data: nodeList } = await requestNodeListByIdx(nodeIdx);
    nodeList.forEach((node: Node) => {
      const observer = this.nodeObserverMap.get(node.id);
      if (observer) {
        observer.updateNode(node);
      }
    });
    const globalObserverKeys = Array.from(this.globalObserverMap.keys());
    globalObserverKeys.forEach((key: string) => {
      const observer = this.globalObserverMap.get(key);
      if (observer) {
        observer.update(nodeList);
      }
    });
  }
}

const nodeMonitor = new NodeMonitor();

export default nodeMonitor;
