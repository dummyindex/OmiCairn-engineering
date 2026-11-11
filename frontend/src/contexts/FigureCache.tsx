import React, { createContext, useContext, useState } from 'react';

type FigureData = {
  figureList: any[];
  currentFigure: any | null;
  currentFigureUrl: string;
  analysisId: string;
};

interface FigureCacheContextType {
  cache: Record<string, FigureData>;
  setFigureCache: (nodeId: string, data: FigureData) => void;
  getFigureCache: (nodeId: string) => FigureData | undefined;
  isCached: (nodeId: string) => boolean;
  clearCache: () => void;
  clearAnalysisCache: (analysisId: string) => void;
}

const FigureCacheContext = createContext<FigureCacheContextType>({
  cache: {},
  setFigureCache: () => {},
  getFigureCache: () => undefined,
  isCached: () => false,
  clearCache: () => {},
  clearAnalysisCache: () => {},
});

export const FigureCacheProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cache, setCache] = useState<Record<string, FigureData>>({});

  const setFigureCache = (nodeId: string, data: FigureData) => {
    setCache((prevCache) => ({
      ...prevCache,
      [nodeId]: data,
    }));
  };

  const getFigureCache = (nodeId: string) => {
    return cache[nodeId];
  };

  const isCached = (nodeId: string) => {
    return !!cache[nodeId];
  };

  const clearCache = () => {
    setCache({});
  };

  const clearAnalysisCache = (analysisId: string) => {
    setCache((prevCache) => {
      const newCache = { ...prevCache };

      Object.keys(newCache).forEach((nodeId) => {
        if (newCache[nodeId].analysisId === analysisId) {
          delete newCache[nodeId];
        }
      });

      return newCache;
    });
  };

  return (
    <FigureCacheContext.Provider
      value={{
        cache,
        setFigureCache,
        getFigureCache,
        isCached,
        clearCache,
        clearAnalysisCache,
      }}
    >
      {children}
    </FigureCacheContext.Provider>
  );
};

export const useFigureCache = () => useContext(FigureCacheContext);
