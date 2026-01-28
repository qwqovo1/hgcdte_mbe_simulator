<template>
  <div class="layout">
    <Sidebar />
    <main class="main-content">
      <div class="page-container">
        <h1 class="page-title">实验</h1>
        <div class="placeholder-content">
          <div class="placeholder-icon">🔬</div>
          <p>实验模块开发中...</p>
          <span>此页面将用于配置与运行MBE仿真实验</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'

export default {
  name: 'Experiment',
  components: {
    Sidebar
  }
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.main-content {
  margin-left: var(--sidebar-width);
  flex: 1;
  padding: 30px;
  background-color: var(--bg-color);
}

.page-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  color: var(--text-color);
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid var(--primary-color);
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.placeholder-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.placeholder-content p {
  font-size: 20px;
  color: var(--text-color);
  margin-bottom: 10px;
}

.placeholder-content span {
  font-size: 14px;
  color: #909399;
}
</style>