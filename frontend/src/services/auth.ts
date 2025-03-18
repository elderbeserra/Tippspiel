import api, { setAuthToken, removeAuthToken } from '@/lib/api';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface UserResponse {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  password: string;
}

export const authService = {
  /**
   * Login with email and password
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const response = await api.post<TokenResponse>('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    // Store the token
    if (response.data.access_token) {
      setAuthToken(response.data.access_token);
    }
    
    return response.data;
  },

  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<UserResponse> {
    const response = await api.post<UserResponse>('/auth/register', data);
    return response.data;
  },

  /**
   * Logout the current user
   */
  logout(): void {
    removeAuthToken();
  },

  /**
   * Get the current user profile
   */
  async getCurrentUser(): Promise<UserResponse> {
    const response = await api.get<UserResponse>('/auth/me');
    return response.data;
  },

  /**
   * Request a password reset
   */
  async requestPasswordReset(data: PasswordResetRequest): Promise<void> {
    await api.post('/auth/password-reset', data);
  },

  /**
   * Confirm a password reset
   */
  async confirmPasswordReset(data: PasswordResetConfirm): Promise<void> {
    await api.post('/auth/password-reset/confirm', data);
  },
}; 