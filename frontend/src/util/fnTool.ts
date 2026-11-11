export const memoize = (fn: Function, hashFn: Function, maxResultsCached: number = -1) => {
  const cache = new Map();
  const wrap = (...args) => {
    const key = hashFn(...args);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn(...args);
    cache.set(key, result);
    if (maxResultsCached > -1 && cache.size > maxResultsCached) {
      cache.delete(cache.keys().next().value);
    }
    return result;
  };

  wrap.clear = function clear() {
    cache.clear();
  };

  return wrap;
};
