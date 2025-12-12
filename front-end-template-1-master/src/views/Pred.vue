<template>
  <div class="pred-container">
    <!-- 左侧输入区 -->
    <div class="left">
      <div class="title">
        <img src="../assets/logo.png" style="width:80px;height:80px;" alt="">
        病情初步预测
      </div>
      <div class="form">
        <div class="form-group">
          <div class="form-label">病情描述</div>
          <div class="form-control">
            <input 
              type="text" 
              v-model="formSubmit.content" 
              placeholder="请输入症状（如：头痛 发热 咳嗽）"
              @keyup.enter="submit"
            >
          </div>
        </div>
        <div class="form-group button">
          <button type="button" @click="submit" :disabled="loading">
            {{ loading ? '预测中...' : '提交' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 右侧结果区 -->
    <div class="right">
      <!-- 提示卡片 -->
      <div class="top">
        <div class="content">
          <div class="title">
            <dv-decoration-11 style="width:400px;height:60px;font-size:13px">
              小贴士：仅为机器预测，身体如有任何不适请到正规医院检查
            </dv-decoration-11>
          </div>
        </div>
      </div>

      <!-- 预测结果卡片 -->
      <div class="top bottom">
        <div class="content">
          <div class="title">
            <dv-decoration-11 style="width:400px;height:60px;font-size:13px">
              预测结果 {{ results.length > 0 ? `(${results.length}个)` : '' }}
            </dv-decoration-11>
          </div>
          
          <dv-border-box-9>
            <!-- 无结果提示 -->
            <div 
              v-if="results.length === 0" 
              class="word no-result"
            >
              {{ resultText }}
            </div>

            <!-- 结果列表 -->
            <div v-else class="result-list">
              <div 
                v-for="(item, index) in results" 
                :key="index" 
                class="result-item"
              >
                <!-- 疾病名称和得分 -->
                <div class="disease-info">
                  <span class="rank">{{ index + 1 }}</span>
                  <span class="name">{{ item.name }}</span>
                  <span class="category">[{{ item.category }}]</span>
                  <span class="score">{{ item.score_percent }}</span>
                </div>
                
                <!-- 症状列表 -->
                <div class="symptoms">
                  <span class="label">关键症状：</span>
                  <span class="symptom-tags">
                    <span 
                      v-for="(symptom, idx) in item.symptoms" 
                      :key="idx" 
                      class="symptom-tag"
                    >
                      {{ symptom }}
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </dv-border-box-9>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Pred',
  data() {
    return {
      formSubmit: {
        content: ''
      },
      results: [],
      resultText: '暂无信息',
      loading: false
    }
  },
  methods: {
    async submit() {
  if (!this.formSubmit.content.trim()) {
    this.$message.warning('请输入症状描述')
    return
  }

  this.loading = true
  this.results = []
  this.resultText = '预测中...'

  try {
    console.log('🚀 发送请求:', this.formSubmit)
    
    const res = await this.$http.post('/submitModel', this.formSubmit)
    
    console.log('✅ 完整响应:', res.data)

    // ⭐ 关键修改：直接从 res.data 解构
    const responseData = res.data.data || res.data  // ⬅️ 兼容两种格式
    
    if (responseData && responseData.results) {
      const { results, count } = responseData
      
      console.log('📊 结果数组:', results)
      console.log('🔢 结果数量:', count)
      
      if (results && Array.isArray(results) && results.length > 0) {
        this.results = results
        this.resultText = ''
        console.log('✅ 显示成功:', this.results)
      } else {
        this.results = []
        this.resultText = '未找到匹配疾病\n💡 提示：请输入更多症状'
      }
    } else {
      console.error('❌ 响应格式错误:', res.data)
      this.results = []
      this.resultText = '数据格式错误'
      this.$message.error('数据格式错误')
    }
  } catch (error) {
    console.error('❌ 请求失败:', error)
    this.results = []
    this.resultText = '网络错误，请稍后重试'
    this.$message.error('预测失败：' + (error.message || '未知错误'))
  } finally {
    this.loading = false
  }
}
}
      
    }
  

</script>

<style lang="less" scoped>
.button {
  width: 100%;
  height: 30px;
  display: flex;
  justify-content: center;
}

button {
  width: 80%;
  height: 100%;
  background: #26fffd;
  color: rgb(0, 0, 0);
  border-radius: 15px;
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover:not(:disabled) {
    background: #1de8e6;
    transform: scale(1.02);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.pred-container {
  display: flex;
  width: 100%;
  height: 100vh;
  
  .left {
    width: 800px;
    display: flex;
    flex-direction: column;
    align-items: center;
    
    .title {
      color: #26fffd;
      margin-top: 80px;
      font-size: 38px;
      font-weight: bold;
    }
    
    .form {
      margin-top: 35px;
      
      .form-group {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        
        .form-label {
          margin-right: 25px;
          font-size: 18px;
          color: #fff;
        }
        
        .form-control input {
          border-radius: 15px;
          background: #d3dcf7;
          border: none;
          outline: none;
          padding: 0 10px;
          height: 25px;
          width: 300px;
        }
      }
    }
  }
  
  .right {
    flex: 1;
    
    .top {
      margin-top: 30px;
      width: 80%;
      
      .content {
        padding: 15px 25px;
        
        .title {
          display: flex;
          justify-content: center;
          color: #fff;
          font-weight: bold;
          font-size: 18px;
        }
      }
    }
    
    .bottom {
      margin-top: 30px;
      width: 80%;
      min-height: 400px;
    }
  }
}

/* 无结果提示 */
.no-result {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 150px;
  font-size: 20px;
  color: #999;
  white-space: pre-line;
  text-align: center;
}

/* 结果列表 */
.result-list {
  padding: 20px;
  max-height: 500px;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: #26fffd;
    border-radius: 3px;
  }
}

/* 单个结果项 */
.result-item {
  background: rgba(38, 255, 253, 0.05);
  border-left: 3px solid #26fffd;
  padding: 15px;
  margin-bottom: 15px;
  border-radius: 8px;
  transition: all 0.3s;
  
  &:hover {
    background: rgba(38, 255, 253, 0.1);
    transform: translateX(5px);
  }
  
  .disease-info {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
    
    .rank {
      display: inline-block;
      width: 30px;
      height: 30px;
      line-height: 30px;
      text-align: center;
      background: linear-gradient(135deg, #26fffd, #1de8e6);
      color: #000;
      border-radius: 50%;
      font-weight: bold;
      margin-right: 12px;
    }
    
    .name {
      font-size: 20px;
      font-weight: bold;
      color: #26fffd;
      margin-right: 10px;
    }
    
    .category {
      font-size: 14px;
      color: #999;
      margin-right: 15px;
    }
    
    .score {
      margin-left: auto;
      font-size: 18px;
      font-weight: bold;
      background: linear-gradient(to right, orange, #26fffd);
      -webkit-background-clip: text;
      color: transparent;
    }
  }
  
  .symptoms {
    display: flex;
    align-items: center;
    
    .label {
      font-size: 14px;
      color: #999;
      margin-right: 10px;
    }
    
    .symptom-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      
      .symptom-tag {
        background: rgba(38, 255, 253, 0.2);
        color: #26fffd;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 13px;
        border: 1px solid rgba(38, 255, 253, 0.3);
      }
    }
  }
}
</style>
