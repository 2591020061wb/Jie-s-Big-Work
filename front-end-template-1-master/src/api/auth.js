import request from '@/utils/request';

const prefix = '/api/auth';

const authApi = {
  register(payload) {
    return request.post(`${prefix}/register`, payload);
  },
  login(payload) {
    return request.post(`${prefix}/login`, payload);
  },
  getProfile() {
    return request.get(`${prefix}/profile`);
  },
  updateProfile(payload) {
    return request.put(`${prefix}/profile`, payload);
  },
  changePassword(payload) {
    return request.post(`${prefix}/change_password`, payload);
  }
};

export default authApi;
export const { register, login, getProfile, updateProfile, changePassword } = authApi;
