<template>
  <div class="profile-page">
    <dv-loading v-if="loading">Loading…</dv-loading>

    <div v-else class="profile-layout">
      <dv-border-box-10 class="profile-card overview-card">
        <div class="card-header">
          <div>
            <p class="caption">PERSONAL HEALTH</p>
            <h2>{{ form.username || '用户' }} 的个人中心</h2>
          </div>
          <div class="timestamp">最近更新：{{ summary.lastUpdate || '未填写' }}</div>
        </div>

        <div class="stat-line">
          <div class="stat" v-for="item in stats" :key="item.label">
            <span class="label">{{ item.label }}</span>
            <span class="value">{{ item.value }}</span>
          </div>
        </div>

        <div class="tag-list">
          <span v-for="tag in tagList" :key="tag" class="tag-pill">{{ tag }}</span>
          <span v-if="!tagList.length" class="tag-pill muted">暂无 lifestyle 标签</span>
        </div>
      </dv-border-box-10>

      <div class="form-columns">
        <dv-border-box-12 class="profile-card form-card">
          <h3>基础信息</h3>
          <div class="form-grid">
            <label>
              <span>用户名</span>
              <input v-model="form.username" disabled />
            </label>
            <label>
              <span>邮箱</span>
              <input v-model="form.email" type="email" />
            </label>
            <label>
              <span>手机号</span>
              <input v-model="form.phone" placeholder="可选" />
            </label>
            <label>
              <span>性别</span>
              <select v-model="form.gender">
                <option value="">未设置</option>
                <option value="male">男</option>
                <option value="female">女</option>
                <option value="other">其他</option>
              </select>
            </label>
            <label>
              <span>出生日期</span>
              <input v-model="form.birth_date" type="date" />
            </label>
            <label>
              <span>身高 (cm)</span>
              <input v-model.number="form.height_cm" type="number" min="0" />
            </label>
            <label>
              <span>体重 (kg)</span>
              <input v-model.number="form.weight_kg" type="number" min="0" />
            </label>
            <label>
              <span>血型</span>
              <input v-model="form.blood_type" placeholder="A/B/AB/O 或 unknown" />
            </label>
          </div>

          <div class="textarea-row">
            <label>
              <span>慢性疾病（用逗号或换行分隔）</span>
              <textarea v-model="form.chronic_conditions_text" rows="2" />
            </label>
            <label>
              <span>过敏史</span>
              <textarea v-model="form.allergies_text" rows="2" />
            </label>
            <label>
              <span>长期用药</span>
              <textarea v-model="form.medications_text" rows="2" />
            </label>
            <label>
              <span>生活方式标签</span>
              <textarea v-model="form.lifestyle_tags_text" rows="2" />
            </label>
          </div>

          <div class="actions">
            <p class="feedback" v-if="feedback">{{ feedback }}</p>
            <button class="primary-btn" :disabled="saving" @click="saveProfile">
              {{ saving ? '保存中…' : '保存资料' }}
            </button>
          </div>
        </dv-border-box-12>

        <dv-border-box-12 class="profile-card form-card password-card">
          <h3>安全设置</h3>
          <label>
            <span>当前密码</span>
            <input v-model="passwordForm.current_password" type="password" />
          </label>
          <label>
            <span>新密码</span>
            <input v-model="passwordForm.new_password" type="password" />
          </label>
          <div class="actions">
            <p class="feedback" v-if="passwordFeedback">{{ passwordFeedback }}</p>
            <button class="ghost-btn" :disabled="changing" @click="changePwd">
              {{ changing ? '提交中…' : '修改密码' }}
            </button>
          </div>
        </dv-border-box-12>
      </div>
    </div>
  </div>
</template>

<script>
import { getProfile, updateProfile, changePassword } from '@/api/auth'

export default {
  name: 'ProfilePage',
  data() {
    return {
      loading: true,
      saving: false,
      changing: false,
      feedback: '',
      passwordFeedback: '',
      form: {
        username: '',
        email: '',
        phone: '',
        gender: '',
        birth_date: '',
        height_cm: '',
        weight_kg: '',
        blood_type: '',
        chronic_conditions_text: '',
        allergies_text: '',
        medications_text: '',
        lifestyle_tags_text: ''
      },
      summary: {
        lastUpdate: '',
        bmi: '--'
      },
      passwordForm: {
        current_password: '',
        new_password: ''
      }
    }
  },
  computed: {
    stats() {
      return [
        { label: '血型', value: this.form.blood_type || '--' },
        { label: '身高', value: this.form.height_cm ? `${this.form.height_cm} cm` : '--' },
        { label: '体重', value: this.form.weight_kg ? `${this.form.weight_kg} kg` : '--' },
        { label: 'BMI', value: this.summary.bmi || '--' }
      ]
    },
    tagList() {
      return this.splitList(this.form.lifestyle_tags_text)
    }
  },
  created() {
    this.fetchProfile()
  },
  methods: {
    async fetchProfile() {
      this.loading = true
      try {
        const data = await getProfile()
        this.form.username = data.username
        this.form.email = data.email || ''
        this.form.phone = data.phone || ''
        this.form.gender = data.gender || ''
        this.form.birth_date = data.birth_date || ''
        this.form.height_cm = data.height_cm || ''
        this.form.weight_kg = data.weight_kg || ''
        this.form.blood_type = data.blood_type || 'unknown'
        this.form.chronic_conditions_text = this.joinList(data.chronic_conditions)
        this.form.allergies_text = this.joinList(data.allergies)
        this.form.medications_text = this.joinList(data.medications)
        this.form.lifestyle_tags_text = this.joinList(data.lifestyle_tags)
        this.summary.bmi = data.bmi || '--'
        this.summary.lastUpdate = this.formatDateTime(data.last_profile_update)
      } catch (e) {
        console.error(e)
      } finally {
        this.loading = false
      }
    },
    async saveProfile() {
      if (this.saving) return
      this.saving = true
      this.feedback = ''
      try {
        await updateProfile({
          email: this.form.email,
          phone: this.form.phone,
          gender: this.form.gender,
          birth_date: this.form.birth_date,
          height_cm: this.form.height_cm,
          weight_kg: this.form.weight_kg,
          blood_type: this.form.blood_type,
          chronic_conditions: this.splitList(this.form.chronic_conditions_text),
          allergies: this.splitList(this.form.allergies_text),
          medications: this.splitList(this.form.medications_text),
          lifestyle_tags: this.splitList(this.form.lifestyle_tags_text)
        })
        this.feedback = '资料已更新'
        this.fetchProfile()
      } catch (e) {
        this.feedback = e?.response?.data?.message || '保存失败'
      } finally {
        this.saving = false
      }
    },
    async changePwd() {
      if (!this.passwordForm.current_password || !this.passwordForm.new_password) {
        this.passwordFeedback = '请先填写完整密码信息'
        return
      }
      this.changing = true
      this.passwordFeedback = ''
      try {
        await changePassword(this.passwordForm)
        this.passwordFeedback = '密码修改成功'
        this.passwordForm = { current_password: '', new_password: '' }
      } catch (e) {
        this.passwordFeedback = e?.response?.data?.message || '修改失败'
      } finally {
        this.changing = false
      }
    },
    splitList(text) {
      if (!text) return []
      return text
        .split(/[，,;；\n\r]+/)
        .map((item) => item.trim())
        .filter(Boolean)
    },
    joinList(value) {
      if (!value) return ''
      if (Array.isArray(value)) return value.join('，')
      if (typeof value === 'string') {
        try {
          const parsed = JSON.parse(value)
          if (Array.isArray(parsed)) return parsed.join('，')
        } catch (_) {
          return value
        }
      }
      return ''
    },
    formatDateTime(input) {
      if (!input) return ''
      const date = new Date(input)
      if (Number.isNaN(date.getTime())) return input
      const pad = (n) => String(n).padStart(2, '0')
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
    }
  }
}
</script>

<style lang="less" scoped>
.profile-page {
  min-height: calc(100vh - 80px);
  padding: 15px;
  color: #e4f2ff;
}

.profile-layout {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.profile-card {
  background: rgba(6, 18, 58, 0.7);
  border-radius: 16px;
  padding: 20px;
}

.overview-card {
  position: relative;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;

  h2 {
    margin: 4px 0 0;
    font-size: 24px;
    color: #ffffff;
  }

  .caption {
    letter-spacing: 2px;
    font-size: 12px;
    color: #81b5ff;
  }

  .timestamp {
    font-size: 14px;
    color: #7ab7ff;
  }
}

.stat-line {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  margin-top: 20px;
}

.stat {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(8, 34, 82, 0.8);
  border: 1px solid rgba(129, 181, 255, 0.2);
}

.stat .label {
  font-size: 12px;
  color: #80a7d6;
}

.stat .value {
  font-size: 20px;
  font-weight: 600;
  color: #f9fcff;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.tag-pill {
  padding: 6px 12px;
  border-radius: 999px;
  background: linear-gradient(120deg, rgba(76, 147, 255, 0.2), rgba(82, 218, 203, 0.2));
  border: 1px solid rgba(129, 181, 255, 0.3);
  font-size: 12px;
}

.tag-pill.muted {
  opacity: 0.6;
}

.form-columns {
  display: grid;
  gap: 15px;
}

@media (min-width: 1200px) {
  .form-columns {
    grid-template-columns: 2fr 1fr;
  }
}

.form-card h3 {
  margin: 0 0 15px;
  font-size: 18px;
  color: #82c5ff;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px 15px;
}

label {
  display: flex;
  flex-direction: column;
  font-size: 13px;
  color: #9dc4ff;
  gap: 6px;
}

input,
select,
textarea {
  background: rgba(9, 25, 62, 0.8);
  border: 1px solid rgba(104, 164, 255, 0.4);
  border-radius: 8px;
  padding: 8px 10px;
  color: #e4f2ff;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

input:focus,
select:focus,
textarea:focus {
  border-color: #52dacb;
}

textarea {
  resize: vertical;
}

.textarea-row {
  margin-top: 15px;
  display: grid;
  gap: 12px;
}

.actions {
  margin-top: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: center;
}

.primary-btn,
.ghost-btn {
  min-width: 140px;
  padding: 10px 16px;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.primary-btn {
  background: linear-gradient(120deg, #52dacb, #568aea);
  color: #04122f;
}

.primary-btn:disabled,
.ghost-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ghost-btn {
  background: transparent;
  border: 1px solid rgba(129, 181, 255, 0.6);
  color: #e4f2ff;
}

.feedback {
  font-size: 13px;
  color: #7efadd;
}

.password-card label {
  margin-bottom: 12px;
}
</style>
