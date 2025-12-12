import request from '@/utils/request';

const prefix = '/api/metrics';

/** 获取健康仪表板数据 */
export const getMetricsDashboard = () =>
  request.get(`${prefix}/dashboard`);

/** 获取监测记录列表与统计 */
export const getMetricsList = (params = {}) =>
  request.get(`${prefix}/metrics/list`, { params });

/** 提交健康指标 */
export const submitMetrics = (payload) =>
  request.post(`${prefix}/submit`, payload);
