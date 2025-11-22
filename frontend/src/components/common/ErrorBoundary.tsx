/**
 * 错误边界组件
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // 调用错误处理回调
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // 记录错误日志
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // 发送错误到监控系统（如果配置了的话）
    this.reportError(error, errorInfo);
  }

  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    try {
      // 这里可以集成错误监控服务，如Sentry
      const errorReport = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      };

      // 发送到错误监控服务
      if (process.env.NODE_ENV === 'production') {
        // fetch('/api/v1/errors/report', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify(errorReport),
        // }).catch(console.error);
      } else {
        console.warn('Error Report (Development):', errorReport);
      }
    } catch (e) {
      console.error('Failed to report error:', e);
    }
  };

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // 如果提供了自定义fallback，使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认错误UI
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
            <div className="mb-4">
              <AlertTriangle className="h-16 w-16 text-red-500 mx-auto" />
            </div>
            
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              出现了错误
            </h1>
            
            <p className="text-gray-600 mb-6">
              抱歉，应用程序遇到了意外错误。请尝试刷新页面或联系技术支持。
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mb-6 text-left">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 mb-2">
                  错误详情
                </summary>
                <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded text-xs">
                  <div className="mb-2">
                    <strong>错误信息:</strong>
                    <pre className="mt-1 text-red-800 whitespace-pre-wrap">
                      {this.state.error.message}
                    </pre>
                  </div>
                  
                  {this.state.error.stack && (
                    <div className="mb-2">
                      <strong>堆栈跟踪:</strong>
                      <pre className="mt-1 text-red-800 whitespace-pre-wrap text-xs overflow-auto">
                        {this.state.error.stack}
                      </pre>
                    </div>
                  )}
                  
                  {this.state.errorInfo && (
                    <div>
                      <strong>组件堆栈:</strong>
                      <pre className="mt-1 text-red-800 whitespace-pre-wrap text-xs overflow-auto">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={this.handleRetry}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                重试
              </button>
              
              <button
                onClick={this.handleReload}
                className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
              >
                刷新页面
              </button>
            </div>

            <div className="mt-6 text-sm text-gray-500">
              错误ID: {Date.now().toString(36)}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * 轻量级错误边界Hook
 */
export function useErrorBoundary() {
  const [error, setError] = React.useState<Error | null>(null);
  const [errorInfo, setErrorInfo] = React.useState<ErrorInfo | null>(null);

  const reset = React.useCallback(() => {
    setError(null);
    setErrorInfo(null);
  }, []);

  const captureError = React.useCallback((error: Error, errorInfo?: ErrorInfo) => {
    setError(error);
    setErrorInfo(errorInfo || null);
  }, []);

  return {
    error,
    errorInfo,
    hasError: !!error,
    reset,
    captureError,
  };
}

/**
 * API错误边界组件
 */
interface ApiErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onApiError?: (error: any) => void;
}

export function ApiErrorBoundary({ children, fallback, onApiError }: ApiErrorBoundaryProps) {
  const [apiError, setApiError] = React.useState<any>(null);

  const handleApiError = React.useCallback((error: any) => {
    setApiError(error);
    onApiError?.(error);
  }, [onApiError]);

  const handleRetry = React.useCallback(() => {
    setApiError(null);
  }, []);

  if (apiError) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-3 mb-3">
          <AlertTriangle className="h-6 w-6 text-red-500" />
          <h3 className="text-lg font-semibold text-red-900">
            API请求失败
          </h3>
        </div>
        
        <p className="text-red-700 mb-4">
          {apiError.message || '网络请求失败，请检查网络连接后重试。'}
        </p>

        <div className="flex gap-3">
          <button
            onClick={handleRetry}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
          >
            重试
          </button>
          
          <button
            onClick={() => window.location.reload()}
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors"
          >
            刷新页面
          </button>
        </div>

        {process.env.NODE_ENV === 'development' && apiError.details && (
          <details className="mt-4">
            <summary className="cursor-pointer text-sm text-red-800 font-medium">
              详细信息
            </summary>
            <pre className="mt-2 p-3 bg-red-100 rounded text-xs overflow-auto">
              {JSON.stringify(apiError.details, null, 2)}
            </pre>
          </details>
        )}
      </div>
    );
  }

  return <>{children}</>;
}

export default ErrorBoundary;