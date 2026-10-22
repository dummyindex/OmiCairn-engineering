export class PromiseLock {
  private lockKey: string;
  private lock: boolean;
  private timeout: number;
  constructor(lockKey: string) {
    this.lockKey = lockKey;
    this.lock = false;
    this.timeout = 20000;
  }
  getLockKey() {
    return this.lockKey;
  }

  getLock() {
    return this.lock;
  }

  getTimeout() {
    return this.timeout;
  }

  async acquire() {
    let timeCost = 0;
    while (this.lock) {
      await new Promise((resolve) => setTimeout(resolve, 100));
      timeCost += 100;
      if (timeCost > this.timeout) {
        throw new Error(`lock timeout: ${this.lockKey}`);
      }
    }
    this.lock = true;
  }
  async release() {
    this.lock = false;
  }
}

export class PromiseLockFactory {
  private locks: Map<string, { lock: PromiseLock; createdTime: number }>;
  constructor() {
    this.locks = new Map();
  }
  getLock(key) {
    // If more than 500 locks, purge those older than 5 minutes
    if (this.locks.size > 500) {
      const now = new Date().getTime();
      const keys = this.locks.keys();
      for (const key of keys) {
        const lock = this.locks.get(key);
        if (!lock || lock.lock) {
          continue;
        }
        if (now - lock.createdTime > 5 * 60 * 1000) {
          this.locks.delete(key);
        }
      }
    }

    if (!this.locks.has(key)) {
      this.locks.set(key, {
        lock: new PromiseLock(key),
        createdTime: new Date().getTime(),
      });
    }
    const lock = this.locks.get(key)?.lock;
    if (!lock) {
      throw new Error(`lock not found: ${key}`);
    }
    return lock;
  }
}

export const promiseLockFactory = new PromiseLockFactory();
