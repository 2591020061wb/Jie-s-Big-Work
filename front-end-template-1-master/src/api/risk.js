import request from '@/utils/request';

export function getRiskAssessment(params = {}) {
  return request({
    url: '/api/risk/assessment',
    method: 'get',
    params
  });
}