/**
 * API客户端基础配置
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// API基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000;

// 创建axios实例
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 添加请求ID用于追踪
    if (config.headers) {
      config.headers['X-Request-ID'] = generateRequestId();
    }

    // 记录请求日志（开发环境）
    if (import.meta.env.DEV) {
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
      });
    }

    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // 记录响应日志（开发环境）
    if (import.meta.env.DEV) {
      console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
        status: response.status,
        data: response.data,
      });
    }

    return response;
  },
  (error) => {
    // 处理认证错误
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
      return Promise.reject(error);
    }

    // 处理权限错误
    if (error.response?.status === 403) {
      console.error('❌ Permission Denied:', error.response.data);
      // 可以显示权限不足的提示
    }

    // 处理服务器错误
    if (error.response?.status >= 500) {
      console.error('❌ Server Error:', error.response.data);
      // 可以显示服务器错误提示
    }

    // 记录错误日志
    console.error('❌ API Error:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      config: error.config,
    });

    return Promise.reject(error);
  }
);

/**
 * 生成请求ID
 */
function generateRequestId(): string {
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
}

/**
 * API响应数据类型
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  code?: string;
  timestamp?: string;
}

/**
 * 分页响应数据类型
 */
export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

/**
 * 通用API错误类型
 */
export interface ApiError {
  code: string;
  message: string;
  details?: any;
  timestamp?: string;
}

/**
 * API工具函数
 */
export const apiUtils = {
  /**
   * 处理API错误
   */
  handleError: (error: any): ApiError => {
    if (error.response) {
      return {
        code: error.response.data?.code || 'UNKNOWN_ERROR',
        message: error.response.data?.message || error.message,
        details: error.response.data?.details,
        timestamp: new Date().toISOString(),
      };
    } else if (error.request) {
      return {
        code: 'NETWORK_ERROR',
        message: '网络连接失败，请检查网络设置',
        timestamp: new Date().toISOString(),
      };
    } else {
      return {
        code: 'UNKNOWN_ERROR',
        message: error.message || '未知错误',
        timestamp: new Date().toISOString(),
      };
    }
  },

  /**
   * 构建查询参数
   */
  buildQueryParams: (params: Record<string, any>): string => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, value.toString());
      }
    });
    return searchParams.toString();
  },

  /**
   * 格式化分页参数
   */
  formatPagination: (page: number = 1, limit: number = 20): Record<string, number> => {
    return {
      offset: (page - 1) * limit,
      limit: limit,
    };
  },

  /**
   * 重试请求
   */
  retryRequest: async <T>(
    requestFn: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> => {
    let lastError: any;

    for (let i = 0; i < maxRetries; i++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error;
        if (i < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
        }
      }
    }

    throw lastError;
  },

  /**
   * 取消请求的token
   */
  createCancelToken: () => {
    return axios.CancelToken.source();
  },

  /**
   * 检查是否为取消错误
   */
  isCancel: (error: any): boolean => {
    return axios.isCancel(error);
  },
};

/**
 * WebSocket连接管理
 */
export class WebSocketManager {
  private connections: Map<string, WebSocket> = new Map();
  private reconnectAttempts: Map<string, number> = new Map();
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(url: string, onMessage: (data: any) => void, onError?: (error: any) => void): () => void {
    const wsUrl = url.startsWith('ws://') || url.startsWith('wss://') ? url : `ws://localhost:8000${url}`;
    
    const ws = new WebSocket(wsUrl);
    this.connections.set(url, ws);

    ws.onopen = () => {
      console.log(`✅ WebSocket connected: ${url}`);
      this.reconnectAttempts.set(url, 0);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('WebSocket message parsing error:', error);
        onError?.(error);
      }
    };

    ws.onclose = (event) => {
      console.log(`❌ WebSocket closed: ${url}`, event);
      this.connections.delete(url);

      // 尝试重连
      if (!event.wasClean && this.reconnectAttempts.get(url)! < this.maxReconnectAttempts) {
        const attempts = (this.reconnectAttempts.get(url) || 0) + 1;
        this.reconnectAttempts.set(url, attempts);
        
        setTimeout(() => {
          console.log(`🔄 Reconnecting to WebSocket: ${url} (attempt ${attempts})`);
          this.connect(url, onMessage, onError);
        }, this.reconnectDelay * attempts);
      }
    };

    ws.onerror = (error) => {
      console.error(`❌ WebSocket error: ${url}`, error);
      onError?.(error);
    };

    // 返回断开连接的函数
    return () => {
      this.disconnect(url);
    };
  }

  disconnect(url: string) {
    const ws = this.connections.get(url);
    if (ws) {
      ws.close();
      this.connections.delete(url);
      this.reconnectAttempts.delete(url);
    }
  }

  disconnectAll() {
    this.connections.forEach((ws, url) => {
      ws.close();
    });
    this.connections.clear();
    this.reconnectAttempts.clear();
  }

  send(url: string, data: any) {
    const ws = this.connections.get(url);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    } else {
      console.warn(`WebSocket not connected: ${url}`);
    }
  }

  isConnected(url: string): boolean {
    const ws = this.connections.get(url);
    return ws !== undefined && ws.readyState === WebSocket.OPEN;
  }
}

export const wsManager = new WebSocketManager();

/**
 * 缓存管理
 */
export class CacheManager {
  private cache: Map<string, { data: any; timestamp: number; ttl?: number }> = new Map();

  set(key: string, data: any, ttl?: number) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl ? Date.now() + ttl * 1000 : undefined,
    });
  }

  get(key: string): any | null {
    const item = this.cache.get(key);
    if (!item) {
      return null;
    }

    // 检查是否过期
    if (item.ttl && Date.now() > item.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  delete(key: string) {
    this.cache.delete(key);
  }

  clear() {
    this.cache.clear();
  }

  cleanExpired() {
    const now = Date.now();
    for (const [key, item] of this.cache.entries()) {
      if (item.ttl && now > item.ttl) {
        this.cache.delete(key);
      }
    }
  }
}

export const cacheManager = new CacheManager();

// 定期清理过期缓存
setInterval(() => {
  cacheManager.cleanExpired();
}, 60000); // 每分钟清理一次

export default apiClient;

// 导出常用的API客户端实例
export { apiClient };