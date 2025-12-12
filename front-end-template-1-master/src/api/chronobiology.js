import request from '@/utils/request';

const prefix = '/api/chronobiology';

const chronobiologyApi = {
  getPlan() {
    return request.get(`${prefix}/plan`);
  },
  updateAction(payload) {
    return request.post(`${prefix}/update`, payload);
  },
  recordSleep(payload) {
    return request.post(`${prefix}/record_sleep`, payload);
  }
};

export default chronobiologyApi;
export const { getPlan, updateAction, recordSleep } = chronobiologyApi;
