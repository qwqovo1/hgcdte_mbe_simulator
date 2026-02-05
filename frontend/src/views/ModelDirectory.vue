<template>
  <div class="layout">
    <Sidebar />
    <main class="main-content">
      <div class="page-container">
        <h1 class="page-title">模型目录</h1>
        <div class="directory-grid">
          <!-- 第一个入口：MBE 数字孪生设备预览 -->
          <div class="model-entry-card" @click="goToPreview">
            <div class="card-content">
              <div class="icon-box">📊</div>
              <h2 class="entry-title">MBE 数字孪生设备预览</h2>
              <div class="entry-desc">高保真 3D 模型渲染与实时状态监控</div>
            </div>
            <div class="card-footer-tag">GPU 实时渲染</div>
          </div>

          <!-- 占位入口（可根据需求扩展） -->
          <div class="model-entry-card disabled">
            <div class="card-content">
              <div class="icon-box">🛠️</div>
              <h2 class="entry-title">更多设备开发中...</h2>
              <div class="entry-desc">即将支持更多分子束外延组件</div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'

export default {
  name: 'ModelDirectory',
  components: { Sidebar },
  methods: {
    goToPreview() {
      this.$router.push('/model/preview')
    }
  }
}
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; background-color: #05050a; }
.main-content { margin-left: var(--sidebar-width); flex: 1; padding: 25px; }
.page-container { max-width: 1400px; margin: 0 auto; }
.page-title { color: #fff; margin-bottom: 30px; font-weight: 300; font-size: 28px; border-bottom: 2px solid #00c7ff; padding-bottom: 10px; display: inline-block;}

.directory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 30px;
  margin-top: 20px;
}

/* 按钮卡片设计：使用黄金比例 0.618 */
/* 宽度 320px，高度约 198px (320 * 0.618) */
.model-entry-card {
  width: 320px;
  height: 198px;
  background: linear-gradient(145deg, #161625, #11111d);
  border: 1px solid #2d2d44;
  border-radius: 12px;
  cursor: pointer;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.model-entry-card:hover {
  transform: translateY(-5px);
  border-color: #00c7ff;
  box-shadow: 0 10px 25px rgba(0, 199, 255, 0.2);
}

.model-entry-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.card-content {
  text-align: center;
  padding: 20px;
}

.icon-box {
  font-size: 32px;
  margin-bottom: 15px;
}

.entry-title {
  color: #fff;
  font-size: 18px;
  margin-bottom: 10px;
}

.entry-desc {
  color: #8888a0;
  font-size: 13px;
  line-height: 1.4;
}

.card-footer-tag {
  position: absolute;
  bottom: 0;
  width: 100%;
  background: rgba(0, 199, 255, 0.1);
  color: #00c7ff;
  font-size: 11px;
  padding: 5px 0;
  text-align: center;
  border-top: 1px solid rgba(0, 199, 255, 0.2);
}
</style>