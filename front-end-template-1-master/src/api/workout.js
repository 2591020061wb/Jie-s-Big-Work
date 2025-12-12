import request from '@/utils/request';

const prefix = '/api/workout';

const workoutApi = {
  getPlan() {
    return request.get(`${prefix}/plan`);
  },
  getSessions(params = {}) {
    return request.get(`${prefix}/sessions`, { params });
  },
  completeSession(payload) {
    return request.post(`${prefix}/complete`, payload);
  },
  skipSession(payload) {
    return request.post(`${prefix}/skip`, payload);
  }
};

export default workoutApi;
export const {
  getPlan,
  getSessions,
  completeSession,
  skipSession
} = workoutApi;
