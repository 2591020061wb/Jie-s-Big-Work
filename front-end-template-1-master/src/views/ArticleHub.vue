<template>
    <div class="article-page">
      <transition name="fade">
        <div v-if="loading" class="loading">
          <dv-loading>加载个性化文章...</dv-loading>
        </div>
        <div v-else class="article-grid">
          <dv-border-box-12 class="panel list-panel">
            <div class="panel-header">
              <div>
                <div class="title">智能文章推荐</div>
                <small>基于风险评估与最新健康指标</small>
              </div>
              <div class="actions">
                <el-button
                  type="primary"
                  icon="el-icon-refresh"
                  size="mini"
                  :loading="loading"
                  @click="loadArticles"
                >
                  刷新
                </el-button>
              </div>
            </div>
  
            <div class="article-list">
              <div
                v-for="item in articles"
                :key="item.id"
                class="article-item"
                :class="{ active: item.id === selectedId }"
                @click="selectArticle(item)"
              >
                <div class="article-title">{{ item.title }}</div>
                <div class="article-meta">
                  <span>{{ item.source || 'MedGPT Lab' }}</span>
                  <span>{{ item.time }}</span>
                </div>
              </div>
              <div v-if="!articles.length" class="article-empty">暂无推荐，请稍后再试</div>
            </div>
          </dv-border-box-12>
  
          <dv-border-box-13 class="panel detail-panel">
            <div class="panel-header">
              <div>
                <div class="title">文章详情</div>
                <small>{{ detailSubtitle }}</small>
              </div>
              <el-button-group>
                <el-button size="mini" :disabled="!selectedId" @click="reloadCurrent">
                  重新加载
                </el-button>
                <el-button
                  size="mini"
                  type="success"
                  :loading="recording"
                  :disabled="!selectedId"
                  @click="submitEngagement"
                >
                  提交阅读反馈
                </el-button>
              </el-button-group>
            </div>
  
            <div v-if="detailLoading" class="detail-loading">
              <dv-loading>正在加载文章...</dv-loading>
            </div>
  
            <div v-else-if="articleDetail" class="detail-body">
              <div class="detail-headline">
                <h2>{{ articleDetail.title }}</h2>
                <div class="detail-meta">
                  <span>来源：{{ articleDetail.source || 'MedGPT Lab' }}</span>
                  <span>发布时间：{{ articleDetail.published_at || '未知' }}</span>
                </div>
                <div class="tag-list">
                  <el-tag v-for="tag in articleDetail.tags" :key="tag" size="mini">
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
  
              <div class="detail-content" v-html="articleDetail.content" />
  
              <div class="engagement-box">
                <div class="label">阅读投入度（0.5-1.5）</div>
                <el-slider
                  v-model="engagementScore"
                  :min="0.5"
                  :max="1.5"
                  :step="0.1"
                  :show-input="true"
                  input-size="small"
                />
                <small>拖动或输入分值，衡量本次阅读的专注与互动。</small>
              </div>
            </div>
  
            <div v-else class="detail-empty">请选择左侧任意文章查看详情</div>
          </dv-border-box-13>
        </div>
      </transition>
    </div>
  </template>
  
  <script>
  import {
    fetchRecommendedArticles,
    fetchArticleDetail,
    recordArticleView
  } from '@/api/articles';
  
  export default {
    name: 'ArticleHub',
    data() {
      return {
        loading: true,
        detailLoading: false,
        recording: false,
        articles: [],
        selectedId: null,
        articleDetail: null,
        engagementScore: 1,
        viewedSet: new Set()
      };
    },
    computed: {
      detailSubtitle() {
        if (!this.articleDetail) return '选择文章即可查看详细内容';
        const source = this.articleDetail.source || 'MedGPT Lab';
        const published = this.articleDetail.published_at || '未知时间';
        return `${source} · ${published}`;
      }
    },
    created() {
      this.loadArticles();
    },
    methods: {
      async loadArticles() {
  this.loading = true;
  try {
    console.log('📢 开始请求推荐文章');
    // 关键修复：去掉解构，直接接收数据（拦截器已返回response.data）
    const data = await fetchRecommendedArticles();
    console.log('📥 前端接收的文章数据：', data); // 此时data就是后端返回的数组
    this.articles = data || [];
    console.log('📝 前端articles变量赋值：', this.articles);
    
    if (this.articles.length) {
      this.selectArticle(this.articles[0]);
    } else {
      this.selectedId = null;
      this.articleDetail = null;
    }
  } catch (error) {
    console.error('[ArticleHub] 获取文章失败', error);
    console.error('错误详情：', error.response?.data || error.message);
    this.$message?.error('无法获取文章推荐，请稍后再试');
  } finally {
    this.loading = false;
  }
},
      async selectArticle(article) {
        if (!article || article.id === this.selectedId) return;
        this.selectedId = article.id;
        await this.loadArticleDetail(article.id);
      },
      async reloadCurrent() {
        if (this.selectedId) {
          await this.loadArticleDetail(this.selectedId, { silentRecord: true });
        }
      },
      async loadArticleDetail(articleId, { silentRecord = false } = {}) {
  this.detailLoading = true;
  this.articleDetail = null;
  try {
    // 关键修复：直接接收数据，无需解构
    const data = await fetchArticleDetail(articleId);
    this.articleDetail = data;
    this.articleDetail.tags = data.tags || [];
    this.engagementScore = 1;

    if (!this.viewedSet.has(articleId)) {
      await this.persistArticleView(articleId, this.engagementScore, { silent: true });
      this.viewedSet.add(articleId);
    } else if (!silentRecord) {
      this.$message?.info('可调整阅读反馈后再次提交');
    }
  } catch (error) {
    console.error('[ArticleHub] 加载详情失败', error);
    this.$message?.error('加载文章详情失败');
  } finally {
    this.detailLoading = false;
  }
},
      async persistArticleView(articleId, score, { silent = false } = {}) {
        try {
          await recordArticleView({
            article_id: articleId,
            engagement_score: score
          });
          if (!silent) {
            this.$message?.success('阅读反馈已提交');
          }
        } catch (error) {
          console.error('[ArticleHub] 记录文章阅读失败', error);
          if (!silent) {
            this.$message?.error('提交阅读反馈失败，请稍后重试');
          }
        }
      },
      async submitEngagement() {
        if (!this.selectedId) return;
        this.recording = true;
        try {
          await this.persistArticleView(this.selectedId, this.engagementScore);
          this.viewedSet.add(this.selectedId);
        } finally {
          this.recording = false;
        }
      }
    }
  };
  </script>
  
  <style lang="less" scoped>
  .article-page {
    min-height: calc(100vh - 120px);
    padding: 18px;
    color: #d6ecff;
  }
  .loading {
    min-height: 480px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .article-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
    gap: 18px;
  }
  .panel {
    padding: 18px;
    box-sizing: border-box;
  }
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
  }
  .title {
    font-size: 18px;
    font-weight: 600;
    color: #0efcff;
  }
  .article-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .article-item {
    padding: 12px 14px;
    border-radius: 12px;
    cursor: pointer;
    background: rgba(12, 32, 58, 0.55);
    transition: all 0.25s ease;
  }
  .article-item:hover {
    transform: translateX(4px);
    background: rgba(14, 50, 92, 0.72);
  }
  .article-item.active {
    border: 1px solid #0efcff;
    background: rgba(14, 60, 112, 0.85);
  }
  .article-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 6px;
  }
  .article-meta {
    font-size: 12px;
    display: flex;
    justify-content: space-between;
    color: #8eb8ff;
  }
  .article-empty {
    padding: 40px 0;
    text-align: center;
    color: #7ea0d8;
  }
  .detail-panel {
    min-height: 420px;
  }
  .detail-loading,
  .detail-empty {
    min-height: 360px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #8eb8ff;
  }
  .detail-body {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }
  .detail-headline h2 {
    margin: 0 0 10px;
    color: #fff;
  }
  .detail-meta {
    font-size: 12px;
    display: flex;
    gap: 12px;
    color: #9bcfff;
  }
  .tag-list {
    margin-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .detail-content {
    line-height: 1.7;
    color: #f5f8ff;
    padding-right: 10px;
    max-height: 340px;
    overflow-y: auto;
  }
  .detail-content h3,
  .detail-content h4 {
    color: #72f5ff;
  }
  .detail-content ul {
    padding-left: 18px;
  }
  .engagement-box {
    padding: 14px;
    border-radius: 12px;
    background: rgba(8, 25, 48, 0.8);
  }
  .engagement-box .label {
    font-size: 14px;
    margin-bottom: 8px;
    color: #8eb8ff;
  }
  @media (max-width: 768px) {
    .article-grid {
      grid-template-columns: 1fr;
    }
  }
  </style>