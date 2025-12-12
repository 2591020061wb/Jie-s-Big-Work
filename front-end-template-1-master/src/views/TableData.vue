<template>
    <div class="tableData-container">
      <!-- 页面标题 -->
      <div class="page-header">
        <div class="header-left">
          <div class="header-icon">
            <i class="icon-database"></i>
          </div>
          <h2 class="title">病例数据查询系统</h2>
        </div>
        <div class="header-right">
          <div class="search-box">
            <input 
              v-model="searchText" 
              type="text" 
              placeholder="搜索病例信息..."
              @input="handleSearch"
            />
            <i class="icon-search"></i>
          </div>
          <button class="refresh-btn" @click="refreshData">
            <i class="icon-refresh"></i>
            刷新数据
          </button>
        </div>
      </div>
  
      <!-- 统计面板 -->
      <div class="stats-panel">
        <div class="stat-item">
          <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
            <i class="icon-file"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ totalCount }}</div>
            <div class="stat-label">总病例数</div>
          </div>
        </div>
        
        <div class="stat-item">
          <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
            <i class="icon-male"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ maleCount }}</div>
            <div class="stat-label">男性患者</div>
          </div>
        </div>
  
        <div class="stat-item">
          <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)">
            <i class="icon-female"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ femaleCount }}</div>
            <div class="stat-label">女性患者</div>
          </div>
        </div>
  
        <div class="stat-item">
          <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)">
            <i class="icon-chart"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ avgAge }}</div>
            <div class="stat-label">平均年龄</div>
          </div>
        </div>
      </div>
  
      <!-- ✅ 数据分析模块 -->
      <div class="analysis-panel">
        <div class="analysis-header">
          <h3>📊 数据分析中心</h3>
          <div class="analysis-tabs">
            <button 
              :class="['tab-btn', { active: activeTab === 'duration' }]"
              @click="switchTab('duration')"
            >
              患病时长分布
            </button>
            <button 
              :class="['tab-btn', { active: activeTab === 'bmi' }]"
              @click="switchTab('bmi')"
            >
              BMI 健康度
            </button>
            <button 
              :class="['tab-btn', { active: activeTab === 'heatmap' }]"
              @click="switchTab('heatmap')"
            >
              疾病-年龄热力图
            </button>
          </div>
        </div>
  
        <div class="charts-container">
          <!-- 患病时长分布图 -->
          <div v-show="activeTab === 'duration'" class="chart-wrapper">
            <div ref="durationChart" class="chart-box"></div>
            <div class="chart-stats">
              <div class="stat-badge">
                <span class="badge-label">急性病占比</span>
                <span class="badge-value">{{ acuteDiseaseRate }}</span>
              </div>
              <div class="stat-badge">
                <span class="badge-label">慢性病占比</span>
                <span class="badge-value">{{ chronicDiseaseRate }}</span>
              </div>
            </div>
          </div>
  
          <!-- BMI 健康度分析 -->
          <div v-show="activeTab === 'bmi'" class="chart-wrapper">
            <div class="bmi-grid">
              <div ref="bmiChart" class="chart-box"></div>
              <div class="bmi-insights">
                <div class="insight-card">
                  <div class="insight-icon">⚠️</div>
                  <div class="insight-content">
                    <div class="insight-title">高血压患者肥胖率</div>
                    <div class="insight-value">{{ hypertensionObesityRate }}</div>
                  </div>
                </div>
                <div class="insight-card">
                  <div class="insight-icon">📈</div>
                  <div class="insight-content">
                    <div class="insight-title">超重/肥胖总占比</div>
                    <div class="insight-value">{{ overweightRate }}</div>
                  </div>
                </div>
                <div class="insight-card">
                  <div class="insight-icon">✅</div>
                  <div class="insight-content">
                    <div class="insight-title">健康体重占比</div>
                    <div class="insight-value">{{ normalWeightRate }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
  
          <!-- 疾病-年龄热力图 -->
          <div v-show="activeTab === 'heatmap'" class="chart-wrapper">
            <div ref="heatmapChart" class="chart-box heatmap-box"></div>
          </div>
        </div>
      </div>
  
      <!-- 表格区域（保持原样）-->
      <transition name="fade" mode="out-in">
        <div v-if="loading" class="loading-wrapper">
          <div class="loading-spinner"></div>
          <p class="loading-text">数据加载中...</p>
        </div>
  
        <div v-else class="table-container">
          <div class="table-header-tools">
            <div class="tools-left">
              <span class="result-count">
                共 <span class="highlight">{{ filteredData.length }}</span> 条记录
              </span>
            </div>
            <div class="tools-right">
              <button class="tool-btn" @click="exportToExcel">
                <i class="icon-download"></i>
                导出数据
              </button>
              <button class="tool-btn" @click="showFilterModal = true">
                <i class="icon-filter"></i>
                高级筛选
              </button>
            </div>
          </div>
  
          <div class="custom-table">
            <div class="table-wrapper" ref="tableWrapper">
              <table>
                <thead>
                  <tr>
                    <th style="width: 60px">序号</th>
                    <th style="width: 100px">类型</th>
                    <th style="width: 80px">性别</th>
                    <th style="width: 80px">年龄</th>
                    <th style="width: 180px">时间</th>
                    <th style="min-width: 200px">描述</th>
                    <th style="width: 120px">求诊医生</th>
                    <th style="width: 150px">医院</th>
                    <th style="width: 120px">科室</th>
                    <th style="width: 100px">身高(cm)</th>
                    <th style="width: 100px">体重(kg)</th>
                    <th style="width: 120px">患病时间</th>
                    <th style="width: 120px">过敏史</th>
                    <th style="width: 150px" class="fixed-right">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in displayData" :key="index" class="table-row">
                    <td>{{ (currentPage - 1) * pageSize + index + 1 }}</td>
                    <td>
                      <span class="type-tag" :class="getTypeClass(row.type)">
                        {{ row.type || '-' }}
                      </span>
                    </td>
                    <td>
                      <span class="gender-badge" :class="row.gender === '男' ? 'male' : 'female'">
                        <i :class="row.gender === '男' ? 'icon-male' : 'icon-female'"></i>
                        {{ row.gender || '-' }}
                      </span>
                    </td>
                    <td><span class="age-text">{{ row.age || '-' }}</span></td>
                    <td><span class="time-text">{{ row.time || '-' }}</span></td>
                    <td>
                      <div class="desc-cell" :title="row.desc">
                        {{ row.desc || '-' }}
                      </div>
                    </td>
                    <td>{{ row.doctor || '-' }}</td>
                    <td>{{ row.hospital || '-' }}</td>
                    <td>{{ row.department || '-' }}</td>
                    <td>{{ row.height || '-' }}</td>
                    <td>{{ row.weight || '-' }}</td>
                    <td>{{ row.duration || '-' }}</td>
                    <td>
                      <div class="allergy-cell" :title="row.allergy">
                        {{ row.allergy || '-' }}
                      </div>
                    </td>
                    <td class="fixed-right">
                      <button class="action-btn view-btn" @click="viewDetail(row)">
                        <i class="icon-eye"></i>
                        查看
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
  
          <div class="pagination">
            <div class="pagination-info">
              显示第 {{ (currentPage - 1) * pageSize + 1 }} - 
              {{ Math.min(currentPage * pageSize, filteredData.length) }} 条，
              共 {{ filteredData.length }} 条
            </div>
            <div class="pagination-controls">
              <button 
                class="page-btn" 
                :disabled="currentPage === 1"
                @click="currentPage = 1"
              >
                首页
              </button>
              <button 
                class="page-btn" 
                :disabled="currentPage === 1"
                @click="currentPage--"
              >
                上一页
              </button>
              
              <span class="page-numbers">
                <button 
                  v-for="page in visiblePages" 
                  :key="page"
                  class="page-num"
                  :class="{ active: page === currentPage }"
                  @click="currentPage = page"
                >
                  {{ page }}
                </button>
              </span>
              
              <button 
                class="page-btn" 
                :disabled="currentPage === totalPages"
                @click="currentPage++"
              >
                下一页
              </button>
              <button 
                class="page-btn" 
                :disabled="currentPage === totalPages"
                @click="currentPage = totalPages"
              >
                末页
              </button>
            </div>
          </div>
        </div>
      </transition>
  
      <!-- 高级筛选弹窗（保持原样）-->
      <div v-if="showFilterModal" class="modal-overlay" @click="showFilterModal = false">
        <div class="modal-content filter-modal" @click.stop>
          <div class="modal-header">
            <h3>高级筛选</h3>
            <button class="close-btn" @click="showFilterModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="filter-row">
              <div class="filter-item">
                <label>科室类型</label>
                <select v-model="filters.type">
                  <option value="">全部科室</option>
                  <option value="内科">内科</option>
                  <option value="外科">外科</option>
                  <option value="骨科">骨科</option>
                  <option value="精神科">精神科</option>
                </select>
              </div>
  
              <div class="filter-item">
                <label>性别</label>
                <select v-model="filters.gender">
                  <option value="">全部</option>
                  <option value="男">男</option>
                  <option value="女">女</option>
                </select>
              </div>
  
              <div class="filter-item">
                <label>年龄范围</label>
                <div class="range-inputs">
                  <input type="number" v-model.number="filters.ageMin" placeholder="最小" />
                  <span>-</span>
                  <input type="number" v-model.number="filters.ageMax" placeholder="最大" />
                </div>
              </div>
            </div>
  
            <div class="filter-actions">
              <button class="filter-btn reset" @click="resetFilters">
                <i class="icon-reset"></i>
                重置
              </button>
              <button class="filter-btn apply" @click="applyFilters">
                <i class="icon-check"></i>
                应用筛选
              </button>
            </div>
          </div>
        </div>
      </div>
  
      <!-- 详情弹窗（保持原样）-->
      <div v-if="showDetailModal" class="modal-overlay" @click="showDetailModal = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>病例详情</h3>
            <button class="close-btn" @click="showDetailModal = false">×</button>
          </div>
          <div class="modal-body" v-if="currentDetail">
            <div class="detail-section">
              <h4>基本信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="label">类型：</span>
                  <span class="value">{{ currentDetail.type || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">性别：</span>
                  <span class="value">{{ currentDetail.gender || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">年龄：</span>
                  <span class="value">{{ currentDetail.age || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">身高：</span>
                  <span class="value">{{ currentDetail.height || '-' }} cm</span>
                </div>
                <div class="detail-item">
                  <span class="label">体重：</span>
                  <span class="value">{{ currentDetail.weight || '-' }} kg</span>
                </div>
              </div>
            </div>
  
            <div class="detail-section">
              <h4>就诊信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="label">时间：</span>
                  <span class="value">{{ currentDetail.time || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">医生：</span>
                  <span class="value">{{ currentDetail.doctor || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">医院：</span>
                  <span class="value">{{ currentDetail.hospital || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">科室：</span>
                  <span class="value">{{ currentDetail.department || '-' }}</span>
                </div>
              </div>
            </div>
  
            <div class="detail-section">
              <h4>病情描述</h4>
              <p class="desc-content">{{ currentDetail.desc || '-' }}</p>
            </div>
  
            <div class="detail-section">
              <h4>其他信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="label">患病时间：</span>
                  <span class="value">{{ currentDetail.duration || '-' }}</span>
                </div>
                <div class="detail-item full-width">
                  <span class="label">过敏史：</span>
                  <span class="value">{{ currentDetail.allergy || '-' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import * as XLSX from 'xlsx'
  import { saveAs } from 'file-saver'
  
  export default {
    data() {
      return {
        loading: true,
        searchText: '',
        currentPage: 1,
        pageSize: 20,
        tableList: [],
        showDetailModal: false,
        showFilterModal: false,
        currentDetail: null,
        
        filters: {
          type: '',
          gender: '',
          ageMin: null,
          ageMax: null,
          dateStart: '',
          dateEnd: ''
        },
        
        appliedFilters: {
          type: '',
          gender: '',
          ageMin: null,
          ageMax: null,
          dateStart: '',
          dateEnd: ''
        },
  
        activeTab: 'duration',
        echarts: null,
        charts: {
          duration: null,
          bmi: null,
          heatmap: null
        }
      }
    },
  
    computed: {
      filteredData() {
        let data = this.tableList
  
        if (this.searchText) {
          const keyword = this.searchText.toLowerCase()
          data = data.filter(item => {
            return Object.values(item).some(val => 
              String(val).toLowerCase().includes(keyword)
            )
          })
        }
  
        if (this.appliedFilters.type) {
          data = data.filter(item => item.department === this.appliedFilters.type)
        }
  
        if (this.appliedFilters.gender) {
          data = data.filter(item => item.gender === this.appliedFilters.gender)
        }
  
        if (this.appliedFilters.ageMin !== null) {
          data = data.filter(item => {
            const age = parseInt(item.age)
            return !isNaN(age) && age >= this.appliedFilters.ageMin
          })
        }
  
        if (this.appliedFilters.ageMax !== null) {
          data = data.filter(item => {
            const age = parseInt(item.age)
            return !isNaN(age) && age <= this.appliedFilters.ageMax
          })
        }
  
        return data
      },
  
      displayData() {
        const start = (this.currentPage - 1) * this.pageSize
        const end = start + this.pageSize
        return this.filteredData.slice(start, end)
      },
  
      totalPages() {
        return Math.ceil(this.filteredData.length / this.pageSize)
      },
  
      visiblePages() {
        const pages = []
        const total = this.totalPages
        const current = this.currentPage
        
        if (total <= 7) {
          for (let i = 1; i <= total; i++) pages.push(i)
        } else {
          if (current <= 4) {
            for (let i = 1; i <= 5; i++) pages.push(i)
            pages.push('...')
            pages.push(total)
          } else if (current >= total - 3) {
            pages.push(1)
            pages.push('...')
            for (let i = total - 4; i <= total; i++) pages.push(i)
          } else {
            pages.push(1)
            pages.push('...')
            for (let i = current - 1; i <= current + 1; i++) pages.push(i)
            pages.push('...')
            pages.push(total)
          }
        }
        return pages
      },
  
      totalCount() {
        return this.tableList.length
      },
  
      maleCount() {
        return this.tableList.filter(item => item.gender === '男').length
      },
  
      femaleCount() {
        return this.tableList.filter(item => item.gender === '女').length
      },
  
      avgAge() {
        const ages = this.tableList
          .map(item => parseInt(item.age))
          .filter(age => !isNaN(age))
        
        if (ages.length === 0) return '-'
        const sum = ages.reduce((a, b) => a + b, 0)
        return Math.round(sum / ages.length) + '岁'
      },
  
      durationDistribution() {
        const ranges = {
          '一周内': 0,
          '一月内': 0,
          '半年内': 0,
          '大于半年': 0,
          '10年以上': 0,
          '无记录': 0
        }
  
        this.tableList.forEach(item => {
          const duration = item.duration || '无'
          
          if (duration.includes('周') || duration.includes('天') || duration === '1日') {
            ranges['一周内']++
          } else if (duration.includes('月') && !duration.includes('半年')) {
            ranges['一月内']++
          } else if (duration.includes('半年')) {
            ranges['半年内']++
          } else if (duration.includes('年')) {
            const years = parseInt(duration)
            if (years >= 10) ranges['10年以上']++
            else ranges['大于半年']++
          } else if (duration.includes('大于半年')) {
            ranges['大于半年']++
          } else {
            ranges['无记录']++
          }
        })
  
        return {
          xData: Object.keys(ranges),
          yData: Object.values(ranges)
        }
      },
  
      acuteDiseaseRate() {
        const acute = this.durationDistribution.yData[0] + this.durationDistribution.yData[1]
        return ((acute / this.totalCount) * 100).toFixed(1) + '%'
      },
  
      chronicDiseaseRate() {
        const chronic = this.durationDistribution.yData[2] + 
                        this.durationDistribution.yData[3] + 
                        this.durationDistribution.yData[4]
        return ((chronic / this.totalCount) * 100).toFixed(1) + '%'
      },
  
      bmiDistribution() {
        const categories = {
          '偏瘦 (<18.5)': 0,
          '正常 (18.5-24)': 0,
          '超重 (24-28)': 0,
          '肥胖 (≥28)': 0,
          '数据缺失': 0
        }
  
        this.tableList.forEach(item => {
          const height = parseFloat(item.height)
          const weight = parseFloat(item.weight)
  
          if (!height || !weight || isNaN(height) || isNaN(weight)) {
            categories['数据缺失']++
            return
          }
  
          const bmi = weight / ((height / 100) ** 2)
  
          if (bmi < 18.5) categories['偏瘦 (<18.5)']++
          else if (bmi < 24) categories['正常 (18.5-24)']++
          else if (bmi < 28) categories['超重 (24-28)']++
          else categories['肥胖 (≥28)']++
        })
  
        return Object.entries(categories).map(([name, value]) => ({ name, value }))
      },
  
      hypertensionObesityRate() {
        const hypertensionPatients = this.tableList.filter(item => 
          item.type && item.type.includes('高血压')
        )
  
        if (hypertensionPatients.length === 0) return '0%'
  
        const obeseCount = hypertensionPatients.filter(item => {
          const height = parseFloat(item.height)
          const weight = parseFloat(item.weight)
          if (!height || !weight) return false
          const bmi = weight / ((height / 100) ** 2)
          return bmi >= 28
        }).length
  
        return ((obeseCount / hypertensionPatients.length) * 100).toFixed(1) + '%'
      },
  
      overweightRate() {
        const overweight = this.bmiDistribution
          .filter(x => x.name.includes('超重') || x.name.includes('肥胖'))
          .reduce((sum, x) => sum + x.value, 0)
        return ((overweight / this.totalCount) * 100).toFixed(1) + '%'
      },
  
      normalWeightRate() {
        const normal = this.bmiDistribution.find(x => x.name.includes('正常'))?.value || 0
        return ((normal / this.totalCount) * 100).toFixed(1) + '%'
      },
  
      diseaseAgeHeatmap() {
        const diseases = ['高血压', '感冒', '骨折', '颈椎病', '腰椎间盘突出', '胃炎', '抑郁症']
        const ageRanges = ['0-30岁', '31-45岁', '46-60岁', '61岁以上']
        
        const data = []
        diseases.forEach((disease, i) => {
          ageRanges.forEach((range, j) => {
            const [minStr, maxStr] = range.replace('岁', '').replace('以上', '').split('-')
            const min = parseInt(minStr)
            const max = maxStr ? parseInt(maxStr) : 999
            
            const count = this.tableList.filter(item => {
              const age = parseInt(item.age)
              return item.type === disease && 
                     age >= min && 
                     (max === 999 ? true : age <= max)
            }).length
  
            data.push([i, j, count])
          })
        })
  
        return {
          xData: diseases,
          yData: ageRanges,
          data
        }
      }
    },
  
    async created() {
      await this.delay(800)
      await this.getTableList()
    },
  
    async mounted() {
      // ✅ 等待数据加载完成后初始化图表
      this.$watch('tableList', async (newVal) => {
        if (newVal.length > 0 && !this.charts.duration) {
          await this.$nextTick()
          setTimeout(() => {
            this.initCharts()
          }, 500) // ✅ 延迟500ms确保DOM完全渲染
        }
      }, { immediate: true })
    },
  
    beforeDestroy() {
      window.removeEventListener('resize', this.resizeCharts)
      
      Object.values(this.charts).forEach(chart => {
        if (chart) chart.dispose()
      })
    },
  
    methods: {
      delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms))
      },
  
      async getTableList() {
        try {
          this.loading = true
          const res = await this.$http.get('/tableData')
          
          if (res.data && res.data.resultData) {
            this.tableList = res.data.resultData.map((item, index) => ({
              id: index + 1,
              type: item[0],
              gender: item[1],
              age: item[2],
              time: item[3],
              desc: item[4],
              doctor: item[5],
              hospital: item[6],
              department: item[7],
              detailLink: item[8],
              height: item[9],
              weight: item[10],
              duration: item[11],
              allergy: item[12]
            }))
          }
        } catch (error) {
          console.error('获取数据失败:', error)
          this.$message.error('数据加载失败')
        } finally {
          this.loading = false
        }
      },
  
      async refreshData() {
        this.currentPage = 1
        await this.getTableList()
        this.$message.success('数据刷新成功')
      },
  
      handleSearch() {
        this.currentPage = 1
      },
  
      viewDetail(row) {
        this.currentDetail = row
        this.showDetailModal = true
      },
  
      getTypeClass(type) {
        const classMap = {
          '内科': 'type-neike',
          '外科': 'type-waike',
          '妇科': 'type-fuke',
          '儿科': 'type-erke',
          '肿瘤科': 'type-zhongliu'
        }
        return classMap[type] || ''
      },
  
      exportToExcel() {
        try {
          const exportData = this.filteredData.map((item, index) => ({
            '序号': index + 1,
            '类型': item.type || '-',
            '性别': item.gender || '-',
            '年龄': item.age || '-',
            '时间': item.time || '-',
            '描述': item.desc || '-',
            '求诊医生': item.doctor || '-',
            '医院': item.hospital || '-',
            '科室': item.department || '-',
            '身高(cm)': item.height || '-',
            '体重(kg)': item.weight || '-',
            '患病时间': item.duration || '-',
            '过敏史': item.allergy || '-'
          }))
  
          const ws = XLSX.utils.json_to_sheet(exportData)
          const wb = XLSX.utils.book_new()
          XLSX.utils.book_append_sheet(wb, ws, '病例数据')
  
          ws['!cols'] = [
            { wch: 8 }, { wch: 12 }, { wch: 8 }, { wch: 8 }, { wch: 20 },
            { wch: 40 }, { wch: 15 }, { wch: 20 }, { wch: 15 }, { wch: 12 },
            { wch: 12 }, { wch: 15 }, { wch: 20 }
          ]
  
          const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
          const blob = new Blob([wbout], { type: 'application/octet-stream' })
          const filename = `病例数据_${new Date().getTime()}.xlsx`
          saveAs(blob, filename)
          
          this.$message.success(`成功导出 ${exportData.length} 条数据`)
        } catch (error) {
          console.error('导出失败:', error)
          this.$message.error('导出失败，请重试')
        }
      },
  
      applyFilters() {
        this.appliedFilters = { ...this.filters }
        this.currentPage = 1
        this.showFilterModal = false
        
        let msg = '已应用筛选'
        const conditions = []
        
        if (this.appliedFilters.type) conditions.push(`科室: ${this.appliedFilters.type}`)
        if (this.appliedFilters.gender) conditions.push(`性别: ${this.appliedFilters.gender}`)
        if (this.appliedFilters.ageMin || this.appliedFilters.ageMax) {
          conditions.push(`年龄: ${this.appliedFilters.ageMin || '不限'}-${this.appliedFilters.ageMax || '不限'}`)
        }
        
        if (conditions.length > 0) {
          msg += ': ' + conditions.join(', ')
        }
        
        this.$message.success(msg)
      },
  
      resetFilters() {
        this.filters = {
          type: '',
          gender: '',
          ageMin: null,
          ageMax: null,
          dateStart: '',
          dateEnd: ''
        }
        this.appliedFilters = { ...this.filters }
        this.currentPage = 1
        this.showFilterModal = false
        this.$message.info('已重置筛选条件')
      },
  
      // ✅ 修复：切换标签时重新初始化图表
      switchTab(tab) {
    this.activeTab = tab
    this.$nextTick(() => {
      setTimeout(() => {
        if (tab === 'duration' && !this.charts.duration) {
          this.initDurationChart()
        } else if (tab === 'bmi' && !this.charts.bmi) {
          this.initBmiChart()
        } else if (tab === 'heatmap' && !this.charts.heatmap) {
          this.initHeatmapChart()
        } else {
          // ✅ 如果图表已存在，调用 resize
          if (this.charts[tab]) {
            this.charts[tab].resize()
          }
        }
      }, 100)
    })},
  

  
      // ✅ 修复：延迟初始化 + DOM 检查
      async initCharts() {
    await this.$nextTick()
    
    // ✅ 等待数据加载完成
    if (!this.tableList || this.tableList.length === 0) {
      console.warn('⚠️ 数据未加载，延迟初始化图表')
      return
    }
    
    // ✅ 等待 DOM 完全渲染
    setTimeout(async () => {
      const echarts = await import('echarts')
      this.echarts = echarts

      // ✅ 检查 DOM 是否存在且有尺寸
      if (this.$refs.durationChart && this.$refs.durationChart.clientWidth > 0) {
        console.log('✅ 初始化患病时长图表')
        this.initDurationChart()
      } else {
        console.warn('⚠️ 患病时长图表 DOM 未准备好')
      }

      window.addEventListener('resize', this.resizeCharts)
    }, 500) // ✅ 延迟500ms确保DOM渲染完成
  },
  
      // ✅ 修复：患病时长图表
      initDurationChart() {
    if (!this.$refs.durationChart || this.charts.duration) return

    this.charts.duration = this.echarts.init(this.$refs.durationChart)
    this.charts.duration.setOption({
      title: {
        text: '患病时长分布分析',
        left: 'center',
        top: 10,
        textStyle: { color: '#fff', fontSize: 18 }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: '{b}: {c} 例'
      },
      grid: {
        left: '10%',
        right: '10%',
        top: '20%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: this.durationDistribution.xData,
        axisLabel: { 
          color: '#fff', 
          rotate: 30,
          interval: 0
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#fff' }
      },
      series: [{
        name: '病例数',
        type: 'bar',
        data: this.durationDistribution.yData,
        itemStyle: {
          // ✅ 移除 normal 层级（直接配置）
          color: new this.echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#43e97b' },
            { offset: 1, color: '#38f9d7' }
          ]),
          borderRadius: [5, 5, 0, 0] // ✅ 新版语法
        },
        label: {
          show: true,
          position: 'top',
          color: '#fff',
          formatter: '{c}'
        }
      }]
    })
  },
  
      // ✅ 修复：BMI 图表（解决左侧挤压）
      initBmiChart() {
    if (!this.$refs.bmiChart || this.charts.bmi) return

    this.charts.bmi = this.echarts.init(this.$refs.bmiChart)
    this.charts.bmi.setOption({
      title: {
        text: 'BMI 健康度分布',
        left: 'center',
        top: 10,
        textStyle: { color: '#fff', fontSize: 18 }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} 例 ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: { color: '#fff', fontSize: 12 },
        itemWidth: 14,
        itemHeight: 14
      },
      series: [{
        name: 'BMI 分布',
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['40%', '55%'],
        data: this.bmiDistribution,
        label: {
          color: '#fff',
          fontSize: 12,
          formatter: '{b}\n{d}%'
        },
        itemStyle: {
          // ✅ 直接配置颜色（移除 normal）
          color: (params) => {
            const colors = ['#67c23a', '#409eff', '#e6a23c', '#f56c6c', '#909399']
            return colors[params.dataIndex]
          }
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    })
  },
  
      // ✅ 修复：热力图（解决底部遮挡）
      initHeatmapChart() {
        if (!this.$refs.heatmapChart || this.charts.heatmap) return
  
        this.charts.heatmap = this.echarts.init(this.$refs.heatmapChart)
        
        const maxValue = Math.max(...this.diseaseAgeHeatmap.data.map(x => x[2]), 1)
        
        this.charts.heatmap.setOption({
          title: {
            text: '疾病-年龄段热力分布',
            left: 'center',
            top: 10,
            textStyle: { color: '#fff', fontSize: 18 }
          },
          tooltip: {
            position: 'top',
            formatter: (params) => {
              return `${this.diseaseAgeHeatmap.xData[params.data[0]]}<br/>` +
                     `${this.diseaseAgeHeatmap.yData[params.data[1]]}: ${params.data[2]} 例`
            }
          },
          grid: {
            left: '15%', // ✅ 增加左边距
            right: '10%',
            top: '15%',
            bottom: '20%', // ✅ 增加底部边距
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: this.diseaseAgeHeatmap.xData,
            axisLabel: { 
              color: '#fff', 
              rotate: 30,
              interval: 0,
              fontSize: 12
            },
            splitArea: {
              show: true
            }
          },
          yAxis: {
            type: 'category',
            data: this.diseaseAgeHeatmap.yData,
            axisLabel: { 
              color: '#fff',
              fontSize: 12
            },
            splitArea: {
              show: true
            }
          },
          visualMap: {
            min: 0,
            max: maxValue,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '2%', // ✅ 调整到距离底部2%
            textStyle: { 
              color: '#fff',
              fontSize: 12
            },
            inRange: {
              color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', 
                      '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
            }
          },
          series: [{
            name: '病例数',
            type: 'heatmap',
            data: this.diseaseAgeHeatmap.data,
            label: {
              show: true,
              color: '#fff',
              fontSize: 11,
              formatter: (params) => params.data[2] || ''
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }]
        })
      },
  
      resizeCharts() {
        Object.values(this.charts).forEach(chart => {
          if (chart) {
            chart.resize()
          }
        })
      }
    }
  }

  </script>
  
  <style scoped>
  /* 保持原有样式 + 以下修复 */
  
  /* ✅ 修复图表容器尺寸 */
  .charts-container {
    padding: 30px;
    min-height: 500px; /* 增加最小高度 */
  }
  
  .chart-wrapper {
    animation: fadeIn 0.5s;
    width: 100%;
    min-height: 450px;
  }
  
  .chart-box {
    width: 100%;
    height: 420px; /* 明确高度 */
    min-height: 420px;
  }
  
  .heatmap-box {
    height: 550px; /* 增加高度容纳底部图例 */
    min-height: 550px;
  }
  
  /* ✅ 修复 BMI 网格布局 */
  .bmi-grid {
    display: grid;
    grid-template-columns: 1.2fr 0.8fr; /* 调整比例 */
    gap: 30px;
    align-items: start; /* 顶部对齐 */
    min-height: 450px;
  }
  
  .bmi-grid .chart-box {
    height: 400px; /* BMI 饼图高度 */
  }
  
  .bmi-insights {
    display: flex;
    flex-direction: column;
    gap: 15px;
    padding-top: 20px; /* 顶部留白 */
  }
  
  /* 保持原有样式（省略...与你提供的一致） */
  .tableData-container {
    min-height: 100vh;
    background: linear-gradient(180deg, #0a0e27 0%, #1a1f3a 100%);
    padding: 20px;
  }
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 20px 30px;
    background: linear-gradient(135deg, rgba(42, 64, 148, 0.3) 0%, rgba(30, 46, 98, 0.3) 100%);
    border: 1px solid rgba(47, 128, 237, 0.2);
    border-radius: 10px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 15px;
  }
  
  .header-icon {
    width: 50px;
    height: 50px;
    background: linear-gradient(135deg, #2f80ed 0%, #1e5799 100%);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 20px rgba(47, 128, 237, 0.5);
  }
  
  .header-icon i::before {
    content: '📊';
    font-size: 24px;
  }
  
  .title {
    margin: 0;
    font-size: 26px;
    font-weight: 600;
    color: #fff;
    text-shadow: 0 2px 10px rgba(47, 128, 237, 0.5);
  }
  
  .header-right {
    display: flex;
    gap: 15px;
  }
  
  .search-box {
    position: relative;
    width: 300px;
  }
  
  .search-box input {
    width: 100%;
    height: 40px;
    padding: 0 40px 0 15px;
    background: rgba(30, 46, 98, 0.5);
    border: 1px solid rgba(47, 128, 237, 0.3);
    border-radius: 20px;
    color: #fff;
    font-size: 14px;
    transition: all 0.3s;
  }
  
  .search-box input:focus {
    outline: none;
    border-color: #2f80ed;
    box-shadow: 0 0 15px rgba(47, 128, 237, 0.3);
  }
  
  .search-box input::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }
  
  .search-box i::before {
    content: '🔍';
    position: absolute;
    right: 15px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 16px;
  }
  
  .refresh-btn {
    padding: 0 25px;
    height: 40px;
    background: linear-gradient(135deg, #2f80ed 0%, #1e5799 100%);
    border: none;
    border-radius: 20px;
    color: #fff;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .refresh-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 20px rgba(47, 128, 237, 0.4);
  }
  
  .refresh-btn i::before {
    content: '🔄';
  }
  
  .stats-panel {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
  }
  
  .stat-item {
    background: linear-gradient(135deg, rgba(42, 64, 148, 0.3) 0%, rgba(30, 46, 98, 0.3) 100%);
    border: 1px solid rgba(47, 128, 237, 0.2);
    border-radius: 10px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 15px;
    transition: all 0.3s;
    cursor: pointer;
  }
  
  .stat-item:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 30px rgba(47, 128, 237, 0.3);
    border-color: rgba(47, 128, 237, 0.5);
  }
  
  .stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  }
  
  .stat-icon i::before {
    color: #fff;
  }
  
  .icon-file::before { content: '📁'; }
  .icon-male::before { content: '👨'; }
  .icon-female::before { content: '👩'; }
  .icon-chart::before { content: '📈'; }
  
  .stat-content {
    flex: 1;
  }
  
  .stat-value {
    font-size: 32px;
    font-weight: bold;
    color: #fff;
    text-shadow: 0 2px 10px rgba(47, 128, 237, 0.5);
  }
  
  .stat-label {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    margin-top: 5px;
  }
  
  .analysis-panel {
    margin-bottom: 20px;
    background: linear-gradient(135deg, rgba(42, 64, 148, 0.3) 0%, rgba(30, 46, 98, 0.3) 100%);
    border: 1px solid rgba(47, 128, 237, 0.2);
    border-radius: 10px;
    overflow: hidden;
  }
  
  .analysis-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 30px;
    border-bottom: 1px solid rgba(47, 128, 237, 0.2);
  }
  
  .analysis-header h3 {
    margin: 0;
    color: #fff;
    font-size: 20px;
    font-weight: 600;
  }
  
  .analysis-tabs {
    display: flex;
    gap: 10px;
  }
  
  .tab-btn {
    padding: 8px 20px;
    background: rgba(30, 46, 98, 0.5);
    border: 1px solid rgba(47, 128, 237, 0.3);
    border-radius: 5px;
    color: rgba(255, 255, 255, 0.7);
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .tab-btn:hover {
    background: rgba(47, 128, 237, 0.3);
    color: #fff;
  }
  
  .tab-btn.active {
    background: linear-gradient(135deg, #2f80ed 0%, #1e5799 100%);
    border-color: #2f80ed;
    color: #fff;
    font-weight: 600;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  .chart-stats {
    display: flex;
    justify-content: center;
    gap: 30px;
    margin-top: 20px;
  }
  
  .stat-badge {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 15px 30px;
    background: rgba(30, 46, 98, 0.5);
    border: 1px solid rgba(47, 128, 237, 0.3);
    border-radius: 8px;
  }
  
  .badge-label {
    color: rgba(255, 255, 255, 0.7);
    font-size: 14px;
  }
  
  .badge-value {
    color: #2f80ed;
    font-size: 24px;
    font-weight: bold;
  }
  
  .insight-card {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 20px;
    background: rgba(30, 46, 98, 0.5);
    border: 1px solid rgba(47, 128, 237, 0.3);
    border-radius: 8px;
    transition: all 0.3s;
  }
  
  .insight-card:hover {
    transform: translateX(5px);
    border-color: #2f80ed;
    box-shadow: 0 4px 15px rgba(47, 128, 237, 0.3);
  }
  
  .insight-icon {
    font-size: 32px;
  }
  
  .insight-content {
    flex: 1;
  }
  
  .insight-title {
    color: rgba(255, 255, 255, 0.7);
    font-size: 14px;
    margin-bottom: 5px;
  }
  
  .insight-value {
    color: #fff;
    font-size: 24px;
    font-weight: bold;
  }
  
  .loading-wrapper {
    text-align: center;
    padding: 100px 20px;
  }
  
  .loading-spinner {
    width: 60px;
    height: 60px;
    border: 4px solid rgba(47, 128, 237, 0.2);
    border-top: 4px solid #2f80ed;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .loading-text {
    color: rgba(255, 255, 255, 0.6);
    font-size: 16px;
  }
  
  .table-container {
    background: linear-gradient(135deg, rgba(42, 64, 148, 0.3) 0%, rgba(30, 46, 98, 0.3) 100%);
    border: 1px solid rgba(47, 128, 237, 0.2);
    border-radius: 10px;
    overflow: hidden;
  }
  
  .table-header-tools {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 30px;
    border-bottom: 1px solid rgba(47, 128, 237, 0.2);
  }
  
  .result-count {
    color: rgba(255, 255, 255, 0.8);
    font-size: 14px;
  }
  
  .highlight {
    color: #2f80ed;
    font-weight: bold;
    font-size: 18px;
  }
  
  .tools-right {
    display: flex;
    gap: 10px;
  }
  
  .tool-btn {
    padding: 8px 20px;
    background: rgba(47, 128, 237, 0.2);
    border: 1px solid rgba(47, 128, 237, 0.3);
    border-radius: 5px;
    color: #fff;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    gap: 5px;
  }
  
  .tool-btn:hover {
    background: rgba(47, 128, 237, 0.4);
    border-color: #2f80ed;
  }
  
  .icon-download::before { content: '⬇️'; }
  .icon-filter::before { content: '🔧'; }
  
  .custom-table {
    padding: 0 30px 20px;
  }
  
  .table-wrapper {
    overflow-x: auto;
    overflow-y: auto;
    max-height: 600px;
  }
  
  .table-wrapper::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  
  .table-wrapper::-webkit-scrollbar-track {
    background: rgba(30, 46, 98, 0.3);
  }
  
  .table-wrapper::-webkit-scrollbar-thumb {
    background: rgba(47, 128, 237, 0.5);
    border-radius: 4px;
  }
  
  .table-wrapper::-webkit-scrollbar-thumb:hover {
    background: rgba(47, 128, 237, 0.8);
  }
  
  table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
  }
  
  thead {
    position: sticky;
    top: 0;
    z-index: 10;
  }
  
  thead th {
    background: linear-gradient(180deg, #2a4094 0%, #1e2e62 100%);
    color: #fff;
    padding: 15px 10px;
    text-align: center;
    font-weight: 600;
    font-size: 14px;
    border-bottom: 2px solid rgba(47, 128, 237, 0.5);
    white-space: nowrap;
  }
  
  thead th.fixed-right {
    position: sticky;
    right: 0;
    z-index: 11;
  }
  
  tbody tr {
    transition: all 0.3s;
  }
  
  tbody tr:nth-child(even) {
    background: rgba(30, 46, 98, 0.2);
  }
  
  tbody tr:hover {
    background: rgba(47, 128, 237, 0.15);
    transform: scale(1.01);
  }
  
  tbody td {
    padding: 12px 10px;
    text-align: center;
    color: rgba(255, 255, 255, 0.85);
    font-size: 13px;
    border-bottom: 1px solid rgba(47, 128, 237, 0.1);
  }
  
  tbody td.fixed-right {
    position: sticky;
    right: 0;
    background: inherit;
    z-index: 9;
  }
  
  .type-tag {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
  }
  
  .type-neike {
    background: rgba(64, 158, 255, 0.2);
    color: #409eff;
    border: 1px solid rgba(64, 158, 255, 0.4);
  }
  
  .type-waike {
    background: rgba(103, 194, 58, 0.2);
    color: #67c23a;
    border: 1px solid rgba(103, 194, 58, 0.4);
  }
  
  .type-fuke {
    background: rgba(230, 162, 60, 0.2);
    color: #e6a23c;
    border: 1px solid rgba(230, 162, 60, 0.4);
  }
  
  .type-erke {
    background: rgba(245, 108, 108, 0.2);
    color: #f56c6c;
    border: 1px solid rgba(245, 108, 108, 0.4);
  }
  
  .type-zhongliu {
    background: rgba(144, 147, 153, 0.2);
    color: #909399;
    border: 1px solid rgba(144, 147, 153, 0.4);
  }
  
  .gender-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
  }
  
  .gender-badge.male {
    background: rgba(64, 158, 255, 0.2);
    color: #409eff;
  }
  
  .gender-badge.female {
    background: rgba(245, 108, 108, 0.2);
    color: #f56c6c;
  }
  
  .gender-badge i::before {
    font-style: normal;
  }
  
  .age-text {
    font-weight: 600;
    color: #fff;
  }
  
  .time-text {
    color: rgba(255, 255, 255, 0.7);
    font-size: 12px;
  }
  
  .desc-cell,
  .allergy-cell {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: left;
  }
  
  .action-btn {
    padding: 6px 15px;
    background: linear-gradient(135deg, #2f80ed 0%, #1e5799 100%);
    border: none;
    border-radius: 5px;
    color: #fff;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s;
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }
  
  .action-btn:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 15px rgba(47, 128, 237, 0.4);
  }
  
  .icon-eye::before { content: '👁️'; }
  
  .pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 30px;
    border-top: 1px solid rgba(47, 128, 237, 0.2);
  }
  
  .pagination-info {
    color: rgba(255, 255, 255, 0.7);
    font-size: 14px;
  }
  
  .pagination-controls {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .page-btn,
  .page-num {
    padding: 8px 15px;
    background: rgba(47, 128, 237, 0.2);
    border: 1px solid rgba(47, 128, 237, 0.3);
    border-radius: 5px;
    color: #fff;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .page-btn:hover:not(:disabled),
  .page-num:hover {
    background: rgba(47, 128, 237, 0.4);
    border-color: #2f80ed;
  }
  
  .page-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  
  .page-num.active {
    background: linear-gradient(135deg, #2f80ed 0%, #1e5799 100%);
    border-color: #2f80ed;
    font-weight: bold;
  }
  
  .page-numbers {
    display: flex;
    gap: 5px;
  }
  
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    animation: fadeIn 0.3s;
  }
  
  .modal-content {
    width: 90%;
    max-width: 800px;
    max-height: 80vh;
    overflow-y: auto;
    background: linear-gradient(135deg, rgba(42, 64, 148, 0.95) 0%, rgba(30, 46, 98, 0.95) 100%);
    border: 1px solid rgba(47, 128, 237, 0.5);
    border-radius: 15px;
    box-shadow: 0 10px 50px rgba(0, 0, 0, 0.5);
    animation: slideUp 0.3s;
  }
  
  .filter-modal {
    max-width: 600px;
  }
  
  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(50px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 25px 30px;
    border-bottom: 1px solid rgba(47, 128, 237, 0.3);
  }
  
  .modal-header h3 {
    margin: 0;
    color: #fff;
    font-size: 24px;
    font-weight: 600;
  }
  
  .close-btn {
    width: 35px;
    height: 35px;
    background: rgba(245, 108, 108, 0.2);
    border: 1px solid rgba(245, 108, 108, 0.4);
    border-radius: 50%;
    color: #f56c6c;
    font-size: 24px;
    line-height: 1;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .close-btn:hover {
    background: rgba(245, 108, 108, 0.4);
    transform: rotate(90deg);
  }
  
  .modal-body {
    padding: 30px;
  }
  
  .filter-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
  }
  
  .filter-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .filter-item label {
    color: rgba(255, 255, 255, 0.8);
    font-size: 14px;
    font-weight: 500;
  }
  
  .filter-item select,
  .filter-item input[type="number"],
  .filter-item input[type="date"] {
    padding: 10px 15px;
    background: rgba(30, 46, 98, 0.5);
    border: 1px solid rgba(47, 128, 237, 0.3);
    border-radius: 5px;
    color: #fff;
    font-size: 14px;
    transition: all 0.3s;
  }
  
  .filter-item select:focus,
  .filter-item input:focus {
    outline: none;
    border-color: #2f80ed;
    box-shadow: 0 0 10px rgba(47, 128, 237, 0.3);
  }
  
  .range-inputs {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .range-inputs input {
    flex: 1;
  }
  
  .range-inputs span {
    color: rgba(255, 255, 255, 0.6);
  }
  
  .filter-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid rgba(47, 128, 237, 0.3);
  }
  
  .filter-btn {
    padding: 10px 25px;
    border: none;
    border-radius: 5px;
    color: #fff;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .filter-btn.reset {
    background: rgba(144, 147, 153, 0.3);
    border: 1px solid rgba(144, 147, 153, 0.5);
  }
  
  .filter-btn.reset:hover {
    background: rgba(144, 147, 153, 0.5);
  }
  
  .filter-btn.apply {
    background: linear-gradient(135deg, #2f80ed 0%, #1e5799 100%);
    box-shadow: 0 2px 10px rgba(47, 128, 237, 0.3);
  }
  
  .filter-btn.apply:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(47, 128, 237, 0.5);
  }
  
  .icon-reset::before { content: '↻'; }
  .icon-check::before { content: '✓'; }
  
  .detail-section {
    margin-bottom: 25px;
  }
  
  .detail-section h4 {
    color: #2f80ed;
    font-size: 18px;
    margin: 0 0 15px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(47, 128, 237, 0.3);
  }
  
  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
  }
  
  .detail-item {
    padding: 10px 0;
  }
  
  .detail-item.full-width {
    grid-column: 1 / -1;
  }
  
  .detail-item .label {
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
  }
  
  .detail-item .value {
    color: #fff;
    font-size: 14px;
    font-weight: 500;
  }
  
  .desc-content {
    color: rgba(255, 255, 255, 0.85);
    line-height: 1.8;
    padding: 15px;
    background: rgba(30, 46, 98, 0.3);
    border-radius: 8px;
    border-left: 3px solid #2f80ed;
  }
  
  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.5s ease;
  }
  
  .fade-enter-from,
  .fade-leave-to {
    opacity: 0;
  }
  
  /* ✅ 响应式调整 */
  @media (max-width: 1200px) {
    .bmi-grid {
      grid-template-columns: 1fr;
    }
    
    .chart-box,
    .heatmap-box {
      height: auto;
      aspect-ratio: 16 / 9;
    }
  }
  
  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
      gap: 15px;
    }
  
    .header-right {
      width: 100%;
      flex-direction: column;
    }
  
    .search-box {
      width: 100%;
    }
  
    .stats-panel {
      grid-template-columns: repeat(2, 1fr);
    }
  
    .analysis-header {
      flex-direction: column;
      gap: 15px;
    }
  
    .analysis-tabs {
      width: 100%;
      flex-direction: column;
    }
  
    .tab-btn {
      width: 100%;
    }
  
    .charts-container {
      padding: 20px;
    }
  
    .chart-box {
      height: 300px;
    }
  
    .heatmap-box {
      height: 400px;
    }
  
    .chart-stats {
      flex-direction: column;
      gap: 15px;
    }
  
    .stat-badge {
      width: 100%;
    }
  
    .table-header-tools {
      flex-direction: column;
      gap: 15px;
    }
  
    .tools-right {
      width: 100%;
      justify-content: space-between;
    }
  
    .pagination {
      flex-direction: column;
      gap: 15px;
    }
  
    .pagination-controls {
      flex-wrap: wrap;
      justify-content: center;
    }
  
    .filter-row {
      grid-template-columns: 1fr;
    }
    
    .filter-actions {
      flex-direction: column;
    }
    
    .filter-btn {
      width: 100%;
      justify-content: center;
    }
  }
  </style>
  