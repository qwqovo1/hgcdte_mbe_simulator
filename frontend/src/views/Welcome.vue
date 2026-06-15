<template>
  <div class="welcome-container">
    <div class="welcome-content">
      <h1 class="welcome-title">欢迎来到分子束外延数字孪生项目</h1>
      <p class="welcome-subtitle">Molecular Beam Epitaxy Digital Twin System</p>
      <button class="btn btn-primary enter-btn" @click="enterSystem">
        进入系统
      </button>
    </div>
    <div class="welcome-background">
      <div class="particle" v-for="n in 20" :key="n"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Welcome',
  methods: {
    enterSystem() {
      this.$router.push('/home')
    }
  }
}
</script>

<style scoped>
.welcome-container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  position: relative;
  overflow: hidden;
}

.welcome-content {
  text-align: center;
  z-index: 10;
  padding: 20px;
}

.welcome-title {
  font-size: 42px;
  color: white;
  margin-bottom: 15px;
  font-weight: 600;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.welcome-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 50px;
  letter-spacing: 2px;
}

.enter-btn {
  padding: 15px 50px;
  font-size: 18px;
}

/* 背景粒子动画 */
.welcome-background {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
}

.particle {
  position: absolute;
  width: 6px;
  height: 6px;
  background: rgba(64, 158, 255, 0.6);
  border-radius: 50%;
  animation: float 15s infinite;
}

.particle:nth-child(odd) {
  background: rgba(255, 255, 255, 0.4);
}

@keyframes float {
  0%, 100% {
    transform: translateY(100vh) rotate(0deg);
    opacity: 0;
  }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% {
    transform: translateY(-100vh) rotate(720deg);
    opacity: 0;
  }
}

.particle:nth-child(1) { left: 5%; animation-delay: 0s; animation-duration: 12s; }
.particle:nth-child(2) { left: 10%; animation-delay: 1s; animation-duration: 14s; }
.particle:nth-child(3) { left: 15%; animation-delay: 2s; animation-duration: 11s; }
.particle:nth-child(4) { left: 20%; animation-delay: 0.5s; animation-duration: 16s; }
.particle:nth-child(5) { left: 25%; animation-delay: 3s; animation-duration: 13s; }
.particle:nth-child(6) { left: 30%; animation-delay: 1.5s; animation-duration: 15s; }
.particle:nth-child(7) { left: 35%; animation-delay: 2.5s; animation-duration: 12s; }
.particle:nth-child(8) { left: 40%; animation-delay: 0.8s; animation-duration: 14s; }
.particle:nth-child(9) { left: 45%; animation-delay: 3.5s; animation-duration: 11s; }
.particle:nth-child(10) { left: 50%; animation-delay: 1.2s; animation-duration: 16s; }
.particle:nth-child(11) { left: 55%; animation-delay: 2.8s; animation-duration: 13s; }
.particle:nth-child(12) { left: 60%; animation-delay: 0.3s; animation-duration: 15s; }
.particle:nth-child(13) { left: 65%; animation-delay: 1.8s; animation-duration: 12s; }
.particle:nth-child(14) { left: 70%; animation-delay: 3.2s; animation-duration: 14s; }
.particle:nth-child(15) { left: 75%; animation-delay: 0.6s; animation-duration: 11s; }
.particle:nth-child(16) { left: 80%; animation-delay: 2.2s; animation-duration: 16s; }
.particle:nth-child(17) { left: 85%; animation-delay: 1.1s; animation-duration: 13s; }
.particle:nth-child(18) { left: 90%; animation-delay: 3.8s; animation-duration: 15s; }
.particle:nth-child(19) { left: 93%; animation-delay: 0.9s; animation-duration: 12s; }
.particle:nth-child(20) { left: 97%; animation-delay: 2.6s; animation-duration: 14s; }

/* ━━━ 手机适配 ━━━ */
@media (max-width: 768px) {
  .welcome-title {
    font-size: 22px;
    line-height: 1.4;
    padding: 0 10px;
  }
  .welcome-subtitle {
    font-size: 13px;
    margin-bottom: 35px;
    letter-spacing: 1px;
    padding: 0 10px;
  }
  .enter-btn {
    padding: 12px 36px;
    font-size: 16px;
  }
  .particle {
    width: 4px;
    height: 4px;
  }
}
</style>