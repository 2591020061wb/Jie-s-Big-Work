<template>
    <div v-if="visible" class="message" :class="type">
      {{ content }}
    </div>
  </template>
  
  <script>
  export default {
    name: 'Message',
    data() {
      return {
        visible: false,
        content: '',
        type: 'success'
      }
    },
    methods: {
      show(content, type = 'success', duration = 3000) {
        this.content = content
        this.type = type
        this.visible = true
        
        setTimeout(() => {
          this.visible = false
        }, duration)
      }
    }
  }
  </script>
  
  <style scoped>
  .message {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    padding: 10px 20px;
    border-radius: 4px;
    color: white;
    z-index: 9999;
    min-width: 200px;
    text-align: center;
  }
  
  .message.success {
    background-color: #67c23a;
    border: 1px solid #67c23a;
  }
  
  .message.error {
    background-color: #f56c6c;
    border: 1px solid #f56c6c;
  }
  
  .message.warning {
    background-color: #e6a23c;
    border: 1px solid #e6a23c;
  }
  </style>