// main.js
import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import dataV from '@jiaminghi/data-view'
import VueParticles from 'vue-particles'
import $http from '@/utils/request'  // 使用带认证的 axios 实例
import "swiper/swiper.min.css"
import * as echarts from 'echarts';
import "@/utils/echarts-wordcloud.min.js"

// Element UI
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'

Vue.use(VueParticles)
Vue.use(dataV)
Vue.use(ElementUI)

Vue.config.productionTip = false

// 只使用一个 HTTP 实例，避免混淆
Vue.prototype.$http = $http

// 为了兼容旧代码，也可以同时挂载为 $api
Vue.prototype.$api = $http

Vue.prototype.$echarts = echarts

// 使用 Element UI 的 Message 组件
import { Message, MessageBox } from 'element-ui'
Vue.prototype.$msgbox = MessageBox
Vue.prototype.$alert = MessageBox.alert
Vue.prototype.$confirm = MessageBox.confirm
Vue.prototype.$prompt = MessageBox.prompt
Vue.prototype.$message = Message

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')