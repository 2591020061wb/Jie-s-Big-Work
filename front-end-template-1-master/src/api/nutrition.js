import request from '@/utils/request';

export function getNutritionPlan() {
  return request({
    url: '/api/nutrition/plan',
    method: 'get'
  });
}

export function recordMeal(data) {
  return request({
    url: '/api/nutrition/record_meal',
    method: 'post',
    data
  });
}

export function updateNutritionPlan(data) {
  return request({
    url: '/api/nutrition/update_plan',
    method: 'post',
    data
  });
}

export function getNutritionRecommendations() {
  return request({
    url: '/api/nutrition/recommendations',
    method: 'get'
  });
}
