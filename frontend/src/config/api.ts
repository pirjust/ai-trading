// API配置
export const API_CONFIG = {
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  apiPrefix: '/api/v1',
  timeout: 30000,
  
  getFullUrl(path: string): string {
    return `${this.baseUrl}${this.apiPrefix}${path}`;
  }
};

// 开发环境配置
if (import.meta.env.DEV) {
  console.log('开发环境API配置:', API_CONFIG);
}