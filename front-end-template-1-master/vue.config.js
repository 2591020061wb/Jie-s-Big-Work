module.exports = {
  devServer: {
    port: 8081, // 强制改回8081（核心！）
    proxy: {
      // 匹配所有以 /api 开头的请求（后端接口统一前缀）
      '/api': {
        target: 'http://localhost:3000', // 后端Flask地址
        changeOrigin: true, // 开启跨域代理
        secure: false,
        logLevel: 'debug'
      },
      // 匹配 /getHomeData 这类非/api开头的接口（日志里看到的请求）
      '/getHomeData': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      }
    }
  }
}