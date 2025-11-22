/**
 * API调用相关的React Hooks
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiClient, ApiResponse, apiUtils, ApiError, PaginatedResponse } from '../services/api';

/**
 * 通用API调用Hook
 */
export function useApi<T = any>() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  
  const mountedRef = useRef(true);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const execute = useCallback(async (
    requestFn: () => Promise<ApiResponse<T>>,
    onSuccess?: (data: T) => void,
    onError?: (error: ApiError) => void
  ) => {
    if (!mountedRef.current) return;

    setLoading(true);
    setError(null);

    try {
      const response = await requestFn();
      
      if (mountedRef.current) {
        if (response.success && response.data) {
          setData(response.data);
          onSuccess?.(response.data);
        } else {
          const apiError = apiUtils.handleError(new Error(response.error || '请求失败'));
          setError(apiError);
          onError?.(apiError);
        }
      }
    } catch (err: any) {
      if (mountedRef.current) {
        const apiError = apiUtils.handleError(err);
        setError(apiError);
        onError?.(apiError);
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  const reset = useCallback(() => {
    if (mountedRef.current) {
      setData(null);
      setError(null);
      setLoading(false);
    }
  }, []);

  return {
    loading,
    data,
    error,
    execute,
    reset,
  };
}

/**
 * 轮询API Hook
 */
export function usePollingApi<T = any>(
  requestFn: () => Promise<ApiResponse<T>>,
  interval: number = 5000,
  autoStart: boolean = true
) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isPolling, setIsPolling] = useState(autoStart);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  const executeRequest = useCallback(async () => {
    if (!mountedRef.current) return;

    try {
      const response = await requestFn();
      
      if (mountedRef.current) {
        if (response.success && response.data) {
          setData(response.data);
          setError(null);
        } else {
          const apiError = apiUtils.handleError(new Error(response.error || '请求失败'));
          setError(apiError);
        }
      }
    } catch (err: any) {
      if (mountedRef.current) {
        const apiError = apiUtils.handleError(err);
        setError(apiError);
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [requestFn]);

  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    setIsPolling(true);
    setLoading(true);
    
    // 立即执行一次
    executeRequest();

    // 设置定时器
    intervalRef.current = setInterval(executeRequest, interval);
  }, [interval, executeRequest]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
    setLoading(false);
  }, []);

  useEffect(() => {
    if (autoStart) {
      startPolling();
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      mountedRef.current = false;
    };
  }, [autoStart, startPolling, interval]);

  return {
    loading,
    data,
    error,
    isPolling,
    startPolling,
    stopPolling,
    execute: executeRequest,
  };
}

/**
 * 分页API Hook
 */
export function usePaginatedApi<T = any>(
  requestFn: (page: number, limit: number) => Promise<ApiResponse<PaginatedResponse<T>>>,
  initialPage: number = 1,
  initialLimit: number = 20
) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<T[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [currentLimit, setCurrentLimit] = useState(initialLimit);
  const [error, setError] = useState<ApiError | null>(null);
  
  const mountedRef = useRef(true);

  const loadPage = useCallback(async (page: number = currentPage, limit: number = currentLimit) => {
    if (!mountedRef.current) return;

    setLoading(true);
    setError(null);

    try {
      const response = await requestFn(page, limit);
      
      if (mountedRef.current) {
        if (response.success && response.data) {
          setData(response.data.items);
          setTotalCount(response.data.total);
          setCurrentPage(page);
          setCurrentLimit(limit);
        } else {
          const apiError = apiUtils.handleError(new Error(response.error || '加载失败'));
          setError(apiError);
        }
      }
    } catch (err: any) {
      if (mountedRef.current) {
        const apiError = apiUtils.handleError(err);
        setError(apiError);
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [requestFn, currentPage, currentLimit]);

  const nextPage = useCallback(() => {
    const hasNextPage = (currentPage - 1) * currentLimit + data.length < totalCount;
    if (hasNextPage) {
      loadPage(currentPage + 1, currentLimit);
    }
  }, [currentPage, currentLimit, data.length, totalCount, loadPage]);

  const prevPage = useCallback(() => {
    if (currentPage > 1) {
      loadPage(currentPage - 1, currentLimit);
    }
  }, [currentPage, currentLimit, loadPage]);

  const refresh = useCallback(() => {
    loadPage(currentPage, currentLimit);
  }, [loadPage, currentPage, currentLimit]);

  const changeLimit = useCallback((newLimit: number) => {
    loadPage(1, newLimit);
  }, [loadPage]);

  useEffect(() => {
    loadPage();
  }, [loadPage]);

  return {
    loading,
    data,
    totalCount,
    currentPage,
    currentLimit,
    error,
    hasNextPage: (currentPage - 1) * currentLimit + data.length < totalCount,
    hasPrevPage: currentPage > 1,
    totalPages: Math.ceil(totalCount / currentLimit),
    loadPage,
    nextPage,
    prevPage,
    refresh,
    changeLimit,
    setCurrentPage,
    setCurrentLimit,
  };
}

/**
 * 缓存API Hook
 */
export function useCachedApi<T = any>(
  key: string,
  requestFn: () => Promise<ApiResponse<T>>,
  ttl?: number
) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  
  const mountedRef = useRef(true);

  const execute = useCallback(async (forceRefresh: boolean = false) => {
    if (!mountedRef.current) return;

    // 检查缓存
    if (!forceRefresh) {
      const cachedData = apiClient.get ? 
        localStorage.getItem(`cache_${key}`) : null;
      
      if (cachedData) {
        try {
          const parsed = JSON.parse(cachedData);
          if (parsed.timestamp && (!ttl || Date.now() - parsed.timestamp < ttl * 1000)) {
            if (mountedRef.current) {
              setData(parsed.data);
              setLastUpdated(parsed.timestamp);
              setLoading(false);
            }
            return;
          }
        } catch (e) {
          console.warn('Cache parsing error:', e);
        }
      }
    }

    setLoading(true);
    setError(null);

    try {
      const response = await requestFn();
      
      if (mountedRef.current) {
        if (response.success && response.data) {
          setData(response.data);
          setLastUpdated(Date.now());
          
          // 缓存数据
          try {
            localStorage.setItem(`cache_${key}`, JSON.stringify({
              data: response.data,
              timestamp: Date.now(),
            }));
          } catch (e) {
            console.warn('Cache saving error:', e);
          }
        } else {
          const apiError = apiUtils.handleError(new Error(response.error || '请求失败'));
          setError(apiError);
        }
      }
    } catch (err: any) {
      if (mountedRef.current) {
        const apiError = apiUtils.handleError(err);
        setError(apiError);
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [key, requestFn, ttl]);

  const invalidateCache = useCallback(() => {
    localStorage.removeItem(`cache_${key}`);
    setData(null);
    setLastUpdated(null);
    setError(null);
  }, [key]);

  useEffect(() => {
    execute();
    return () => {
      mountedRef.current = false;
    };
  }, [execute]);

  return {
    loading,
    data,
    error,
    lastUpdated,
    execute,
    invalidateCache,
  };
}

/**
 * 防抖API Hook
 */
export function useDebouncedApi<T = any>(
  requestFn: () => Promise<ApiResponse<T>>,
  delay: number = 300
) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  const execute = useCallback((debounce: boolean = true) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    if (debounce) {
      timeoutRef.current = setTimeout(async () => {
        if (!mountedRef.current) return;

        setLoading(true);
        setError(null);

        try {
          const response = await requestFn();
          
          if (mountedRef.current) {
            if (response.success && response.data) {
              setData(response.data);
            } else {
              const apiError = apiUtils.handleError(new Error(response.error || '请求失败'));
              setError(apiError);
            }
          }
        } catch (err: any) {
          if (mountedRef.current) {
            const apiError = apiUtils.handleError(err);
            setError(apiError);
          }
        } finally {
          if (mountedRef.current) {
            setLoading(false);
          }
        }
      }, delay);
    } else {
      // 不防抖立即执行
      (async () => {
        if (!mountedRef.current) return;

        setLoading(true);
        setError(null);

        try {
          const response = await requestFn();
          
          if (mountedRef.current) {
            if (response.success && response.data) {
              setData(response.data);
            } else {
              const apiError = apiUtils.handleError(new Error(response.error || '请求失败'));
              setError(apiError);
            }
          }
        } catch (err: any) {
          if (mountedRef.current) {
            const apiError = apiUtils.handleError(err);
            setError(apiError);
          }
        } finally {
          if (mountedRef.current) {
            setLoading(false);
          }
        }
      })();
    }
  }, [requestFn, delay]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      mountedRef.current = false;
    };
  }, []);

  const reset = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    if (mountedRef.current) {
      setData(null);
      setError(null);
      setLoading(false);
    }
  }, []);

  return {
    loading,
    data,
    error,
    execute,
    reset,
  };
}