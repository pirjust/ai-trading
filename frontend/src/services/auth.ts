// 认证服务
import { User } from '../types/auth';
import { apiUtils } from './api';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  username: string;
  email: string;
  is_superuser: boolean;
  expires_in: number;
}

class AuthService {
  private baseUrl = '/api/v1/auth';
  private tokenKey = 'ai_trading_token';
  private userKey = 'ai_trading_user';

  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const loginRequest = async () => {
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await fetch(`${this.baseUrl}/login`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '登录失败');
      }

      const data = await response.json();
      this.setToken(data.access_token);
      this.setUser({
        id: data.user_id,
        username: data.username,
        email: data.email,
        is_superuser: data.is_superuser,
      });
      
      return data;
    };

    try {
      return await apiUtils.retryRequest(loginRequest, 3, 1000);
    } catch (error) {
      throw new Error(`登录失败: ${apiUtils.handleError(error).message}`);
    }
  }

  async register(userData: RegisterRequest): Promise<{ message: string; user?: Partial<User> }> {
    const registerRequest = async () => {
      const response = await fetch(`${this.baseUrl}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          'username': userData.username,
          'password': userData.password,
          'email': userData.email,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '注册失败');
      }

      return await response.json();
    };

    try {
      return await apiUtils.retryRequest(registerRequest, 2, 500);
    } catch (error) {
      throw new Error(`注册失败: ${apiUtils.handleError(error).message}`);
    }
  }

  async getCurrentUser(): Promise<User> {
    const getCurrentUserRequest = async () => {
      const token = this.getToken();
      if (!token) {
        throw new Error('未登录');
      }

      const response = await fetch(`${this.baseUrl}/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        this.clearAuth();
        throw new Error('获取用户信息失败');
      }

      const user = await response.json();
      this.setUser(user);
      return user;
    };

    try {
      return await apiUtils.retryRequest(getCurrentUserRequest, 2, 500);
    } catch (error) {
      throw new Error(`获取用户信息失败: ${apiUtils.handleError(error).message}`);
    }
  }

  async refreshToken(): Promise<AuthResponse> {
    const refreshRequest = async () => {
      const token = this.getToken();
      if (!token) {
        throw new Error('未登录');
      }

      const response = await fetch(`${this.baseUrl}/refresh`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        this.clearAuth();
        throw new Error('令牌刷新失败');
      }

      const data = await response.json();
      this.setToken(data.access_token);
      return data;
    };

    try {
      return await apiUtils.retryRequest(refreshRequest, 2, 500);
    } catch (error) {
      this.clearAuth();
      throw new Error(`令牌刷新失败: ${apiUtils.handleError(error).message}`);
    }
  }

  async logout(): Promise<void> {
    const token = this.getToken();
    if (token) {
      try {
        await fetch(`${this.baseUrl}/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } catch (error) {
        console.warn('登出请求失败:', error);
      }
    }
    
    this.clearAuth();
  }

  setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  setUser(user: User): void {
    localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  getUser(): User | null {
    const userStr = localStorage.getItem(this.userKey);
    return userStr ? JSON.parse(userStr) : null;
  }

  clearAuth(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  getAuthHeader(): { Authorization: string } | null {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : null;
  }
}

export const authService = new AuthService();