import { message } from 'antd';
import { requestLoginByPassword } from '@/request/userAuthorization';
import type { LoginCredentials, AuthTokens, LoginResponse, DecodedToken } from './types';
import { AUTH_CONSTANTS } from './constants';

export class AuthService {
  private static instance: AuthService;
  private loginAttempts: Map<string, number> = new Map();
  private lockoutTimers: Map<string, NodeJS.Timeout> = new Map();
  private tokenCheckInterval: NodeJS.Timer | null = null;

  private constructor() {
    this.startTokenCheck();
  }

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  private startTokenCheck(): void {
    if (this.tokenCheckInterval) {
      clearInterval(this.tokenCheckInterval);
    }

    this.tokenCheckInterval = setInterval(() => {
      this.checkTokenExpiration();
    }, 60 * 1000);
  }

  private async checkTokenExpiration(): Promise<void> {
    const token = localStorage.getItem('token');
    if (!token) {
      this.handleTokenExpiration();
      return;
    }

    const tokenData = this.parseToken(token);
    if (!tokenData) {
      this.handleTokenExpiration();
      return;
    }

    const expirationTime = tokenData.exp * 1000;
    const currentTime = Date.now();
    const timeUntilExpiry = expirationTime - currentTime;

    // Try to refresh token if it expires in less than 5 minutes
    if (timeUntilExpiry < 5 * 60 * 1000) {
      try {
        await this.refreshToken();
      } catch (error) {
        this.handleTokenExpiration();
      }
    }
  }

  private parseToken(token: string): DecodedToken | null {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join(''),
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Failed to parse token:', error);
      return null;
    }
  }

  public handleTokenExpiration(): void {
    localStorage.removeItem('token');
    this.clearTokens();
    message.error('Session expired. Please login again.');
    window.location.href = '/login/byPassword';
  }

  // Login Attempt Management Methods
  private isLockedOut(phoneNumber: string): boolean {
    const attempts = this.loginAttempts.get(phoneNumber) || 0;
    return attempts >= AUTH_CONSTANTS.MAX_LOGIN_ATTEMPTS;
  }

  private incrementLoginAttempts(phoneNumber: string): void {
    const currentAttempts = this.loginAttempts.get(phoneNumber) || 0;
    this.loginAttempts.set(phoneNumber, currentAttempts + 1);

    if (currentAttempts + 1 >= AUTH_CONSTANTS.MAX_LOGIN_ATTEMPTS) {
      this.setLockout(phoneNumber);
    }
  }

  private setLockout(phoneNumber: string): void {
    if (this.lockoutTimers.has(phoneNumber)) {
      clearTimeout(this.lockoutTimers.get(phoneNumber));
    }

    const timer = setTimeout(() => {
      this.loginAttempts.delete(phoneNumber);
      this.lockoutTimers.delete(phoneNumber);
    }, AUTH_CONSTANTS.LOCKOUT_DURATION);

    this.lockoutTimers.set(phoneNumber, timer);
  }

  // Token Storage Methods
  private async setTokens(tokens: AuthTokens): Promise<void> {
    try {
      localStorage.setItem('token', tokens.accessToken);
      localStorage.setItem('hadToken', 'true');

      await fetch('/api/auth/set-cookies', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tokens),
      });
    } catch (error) {
      console.error('Failed to set auth tokens:', error);
      throw new Error('Failed to complete authentication');
    }
  }

  private clearTokens(): void {
    localStorage.removeItem('token');
    fetch('/api/auth/clear-cookies', {
      method: 'POST',
      credentials: 'include',
    }).catch(console.error);
  }

  // Public Authentication Methods
  public async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      if (this.isLockedOut(credentials.phoneNumber)) {
        const error = new Error('Account temporarily locked. Please try again later.');
        error.name = 'LockoutError';
        throw error;
      }

      const { areaCode, phoneNumber, password } = credentials;
      const fullPhoneNumber = `${areaCode}${phoneNumber}`;

      const result = await requestLoginByPassword(fullPhoneNumber, password);

      if (result.code === 200) {
        await this.setTokens(result.data);
        this.loginAttempts.delete(credentials.phoneNumber);
        this.startTokenCheck();
        return result;
      }

      this.incrementLoginAttempts(credentials.phoneNumber);
      throw new Error(result.message || 'Login failed');
    } catch (error) {
      if (error.name === 'LockoutError') {
        message.error(error.message);
      } else {
        this.incrementLoginAttempts(credentials.phoneNumber);
        message.error('Invalid credentials');
      }
      throw error;
    }
  }

  public async logout(): Promise<void> {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
      this.clearTokens();
      if (this.tokenCheckInterval) {
        clearInterval(this.tokenCheckInterval);
        this.tokenCheckInterval = null;
      }
      window.location.href = '/login/byPassword';
    } catch (error) {
      console.error('Logout failed:', error);
      message.error('Logout failed. Please try again.');
    }
  }

  public async refreshToken(): Promise<void> {
    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const newTokens: AuthTokens = await response.json();
      await this.setTokens(newTokens);
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.handleTokenExpiration();
    }
  }

  // Method to check if user is currently authenticated
  public isAuthenticated(): boolean {
    const token = localStorage.getItem('token');
    if (!token) return false;

    const tokenData = this.parseToken(token);
    if (!tokenData) return false;

    const currentTime = Date.now() / 1000;
    return tokenData.exp > currentTime;
  }
}
