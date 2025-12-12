const TOKEN_KEY = 'med-portal-token';
const USER_KEY = 'med-portal-user';

// Token 操作
export function getToken() {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token);
  }
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

// 用户信息操作
export function getUser() {
  const userStr = window.localStorage.getItem(USER_KEY);
  return userStr ? JSON.parse(userStr) : null;
}

export function setUser(user) {
  if (user) {
    window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function clearUser() {
  window.localStorage.removeItem(USER_KEY);
}

// 认证状态检查
export function isAuthenticated() {
  return Boolean(getToken());
}

// 清除所有认证信息
export function clearAuth() {
  clearToken();
  clearUser();
}
export function logout() {
  // 强制清除Token和用户信息，不保留缓存
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  // 可选：如果有其他存储的登录相关信息，也一起清除
  // localStorage.clear(); // 谨慎使用，会清除所有本地存储
}

