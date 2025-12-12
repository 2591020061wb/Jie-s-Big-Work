import axios from "axios";

// 直接连接到 Vue 开发服务器，让它代理
const axiosInstance = axios.create({
    baseURL: 'http://localhost:3000',  // 指向 Vue 开发服务器
    timeout: 10000,
})

axiosInstance.interceptors.request.use(
    (config) => {
        console.log('🌐 发送请求到:', config.url);
        console.log('📦 请求数据:', config.data);
        return config;
    },
    (error) => {
        console.error('❌ 请求错误:', error);
        return Promise.reject(error);
    } 
);

axiosInstance.interceptors.response.use(
    (response) => {
        console.log('✅ 响应成功:', response.status);
        return response.data;
    },
    (error) => {
        console.error('❌ 响应错误:');
        console.error('错误消息:', error.message);
        console.error('状态码:', error.response?.status);
        console.error('错误数据:', error.response?.data);
        
        if (error.code === 'ECONNREFUSED') {
            console.error('💥 代理配置错误！');
            console.error('请检查:');
            console.error('1. vue.config.js 是否存在');
            console.error('2. 代理目标端口是否正确 (应该是3000)');
            console.error('3. Vue 开发服务器是否重启');
        }
        
        return Promise.reject(error);
    }
);

export default axiosInstance;