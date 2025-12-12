// src/api/articles.js
import request from '@/utils/request';

// 获取推荐文章（直接返回request结果，已被拦截器处理为response.data）
export function fetchRecommendedArticles() {
  return request({
    url: '/api/article/recommended',
    method: 'get'
  });
}

// 获取文章详情
export function fetchArticleDetail(articleId) {
  return request({
    url: `/api/article/detail/${articleId}`,
    method: 'get'
  });
}

// 记录文章查看
export function recordArticleView(payload) {
  return request({
    url: '/api/article/view',
    method: 'post',
    data: payload
  });
}

export default {
  fetchRecommendedArticles,
  fetchArticleDetail,
  recordArticleView
};