<template>
  <div id="app">
    <StarryBackground />
    <Header />
    <div id="main">
      <transition name="scale" mode="out-in">
        <router-view />
      </transition>
    </div>
  </div>
</template>

<script>
import StarryBackground from '@/components/StarryBackground.vue'
import Header from '@/components/Header.vue'

export default {
  components: {
    StarryBackground,
    Header,
  },
}
</script>

<style lang="less">
html,
body,
#app {
  min-height: 100%;
  margin: 0;
  background: #020a2b;
  color: #cfe7ff;
  font-family: 'Microsoft YaHei', sans-serif;
}

body {
  background:
    radial-gradient(circle at 25% 20%, rgba(67, 192, 255, 0.35), transparent 55%),
    radial-gradient(circle at 80% -10%, rgba(255, 255, 255, 0.15), transparent 45%),
    #020a2b;
  background-attachment: fixed;
}
</style>

<style lang="less" scoped>
#main {
  padding: 15px;
  box-sizing: border-box;
}

.scale-enter-active {
  transition: transform 0.5s ease-in-out;
  transform-origin: center;
  transform: scale(0);
}
.scale-enter-to {
  transform: scale(1);
}
.scale-leave-active {
  transition: transform 0.5s ease-in-out;
  transform-origin: center;
  transform: scale(1);
}
.scale-leave-to {
  transform: scale(0);
}
</style>
