<template>
  <div class="layout">
    <Sidebar />
    <main class="main-content">
      <div class="experiment-wrapper">
        <h1 class="art-title">HgCdTe 实验控制台</h1>

        <div class="workspace">
          <!-- 仿真视觉区 -->
          <div class="display-container" ref="displayBox">
            <div class="placeholder-3d">
              <div class="scanner-line" v-if="isExperimenting && !isPaused"></div>
              <div class="status-tag" :class="statusClass">{{ statusText }}</div>
              <span class="status-info">{{ isExperimenting ? (isPaused ? '生长已挂起' : 'HgCdTe 原子层沉积中...') : '系统待命' }}</span>
            </div>
            <!-- 连线：仅在非手机端计算展示 -->
            <svg class="connection-svg">
              <line v-for="(pos, index) in linePositions" :key="index"
                :x1="pos.x1" :y1="pos.y1" :x2="pos.x2" :y2="pos.y2"
                class="draw-line" :class="{ 'active-line': isExperimenting && !isPaused }" />
            </svg>
          </div>

          <!-- 工艺参数控制区 -->
          <div class="control-panel">
            <div class="param-grid">
              <div v-for="(param, index) in parameters" :key="index" class="param-unit" :ref="`param-${index}`">
                <input type="number" v-model.number="param.value" @input="checkSafety(param)" class="param-input" />
                <button class="param-btn" @click="focusInput(index)">{{ param.label }}</button>
                <div v-if="param.warning" class="mini-warn">{{ param.warning }}</div>
              </div>
            </div>
          </div>

          <!-- 控制中心 -->
          <div class="bottom-console">
            <div class="action-buttons">
              <button v-if="!isExperimenting" class="action-btn predict-btn" @click="handleAction('start')">开始生长</button>
              <template v-else>
                <button class="action-btn pause-btn" @click="handleAction('togglePause')">
                  {{ isPaused ? '继续实验' : '暂停实验' }}
                </button>
                <button class="action-btn stop-btn" @click="handleAction('stop')">停止</button>
              </template>
              <button class="action-btn reset-btn" @click="handleAction('reset')">重置</button>
            </div>

            <div class="monitor-display">
              <div class="info-group">
                <span class="time-label">用时: {{ elapsed }}s</span>
                <span class="thickness-label">实时膜厚 (nm)</span>
              </div>
              <div class="digital-screen" :class="{ 'paused-screen': isPaused }">{{ currentThickness.toFixed(4) }}</div>
              <button v-if="!isExperimenting && elapsed > 0" class="export-btn" @click="exportData">📥 保存报告</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 报警遮罩 -->
      <div v-if="alertMsg" class="alert-overlay">
        <div class="alert-box">
          <h3>🚨 硬件保护性停机</h3>
          <p>{{ alertMsg }}</p>
          <button @click="alertMsg = null">确定</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'
import axios from 'axios'

export default {
  name: 'Experiment',
  components: { Sidebar },
  data() {
    return {
      startTime: null,
      timer: null,
      elapsed: 0,
      currentThickness: 0.0000,
      isExperimenting: false,
      isPaused: false,
      alertMsg: null,
      linePositions: [],
      parameters: [
        { label: '衬底温度 Ts', value: 185, normal: 185 },
        { label: 'Hg 源温度', value: 80, normal: 80 },
        { label: 'CdTe 源温度', value: 450, normal: 450 },
        { label: 'Te2 源温度', value: 320, normal: 320 },
        { label: 'Hg 通量', value: 2.5, normal: 2.5 },
        { label: '背景真空', value: 1.0, normal: 1.0 },
        { label: '束流压力', value: 5.2, normal: 5.2 },
        { label: '转台转速', value: 12, normal: 12 },
        { label: '冷却水温', value: 16, normal: 16 },
        { label: '生长修正', value: 1.0, normal: 1.0 }
      ]
    }
  },
  computed: {
    statusText() {
      if (!this.isExperimenting) return '[ 待机 ]';
      return this.isPaused ? '[ 暂停 ]' : '[ 运行 ]';
    },
    statusClass() {
      return { 'status-growing': this.isExperimenting && !this.isPaused, 'status-paused': this.isPaused };
    }
  },
  mounted() {
    this.calculateLines();
    window.addEventListener('resize', this.calculateLines);
  },
  methods: {
    calculateLines() {
      // 手机端（屏幕小于768px）侧边栏变窄，不显示连线以节省性能和视觉空间
      if (!this.$refs.displayBox || window.innerWidth < 768) {
        this.linePositions = [];
        return;
      }
      const box = this.$refs.displayBox.getBoundingClientRect();
      this.linePositions = this.parameters.map((_, index) => {
        const el = this.$refs[`param-${index}`][0].getBoundingClientRect();
        return { x1: el.left + el.width / 2 - box.left, y1: el.top - box.top, x2: box.width / 2, y2: box.height };
      });
    },
    checkSafety(param) {
      const ratio = param.value / param.normal;
      if (ratio >= 2.0) {
        this.alertMsg = `${param.label} 超出安全阈值200%，系统已自动停机。`;
        if (this.isExperimenting && !this.isPaused) this.handleAction('togglePause');
        param.warning = "危急";
      } else if (ratio >= 1.5) { param.warning = "偏移"; }
      else { param.warning = null; }
    },
    handleAction(type) {
      if (type === 'start') {
        this.isExperimenting = true; this.isPaused = false;
        if (!this.startTime) this.startTime = new Date();
        this.startEngine();
      } else if (type === 'togglePause') {
        this.isPaused = !this.isPaused;
        this.isPaused ? clearInterval(this.timer) : this.startEngine();
      } else if (type === 'stop') {
        clearInterval(this.timer); this.isExperimenting = false;
      } else if (type === 'reset') {
        this.handleAction('stop');
        this.currentThickness = 0; this.elapsed = 0; this.startTime = null;
      }
    },
    startEngine() {
      clearInterval(this.timer);
      this.timer = setInterval(() => {
        const Ts = this.parameters[0].value;
        const hgFlux = this.parameters[4].value;
        const cdteTemp = this.parameters[2].value;
        const tempEfficiency = Math.max(0, 1 - Math.abs(Ts - 185) / 25);
        const cdteContribution = Math.pow(cdteTemp / 450, 4) * 0.003;
        const hgCoverage = Math.min(1, hgFlux / 2.0);
        this.currentThickness += cdteContribution * tempEfficiency * hgCoverage;
        this.elapsed += 1;
      }, 1000);
    },
    async exportData() {
      const payload = {
        name: "HgCdTe 穿透模拟实验",
        startTime: this.startTime.toLocaleString(),
        duration: `${this.elapsed}s`,
        parameters: this.parameters.reduce((acc, curr) => ({...acc, [curr.label]: curr.value}), {}),
        thickness: this.currentThickness.toFixed(4)
      };
      try {
        await axios.post('/api/experiment/export', payload);
        alert(`✅ 报告已保存至 Data 文件夹`);
      } catch (err) { alert('❌ 接口连接失败，请检查内网穿透'); }
    },
    focusInput(index) { this.$refs[`param-${index}`][0].querySelector('input').focus(); }
  }
}
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; background-color: #05050a; color: white; }

/* 主内容区：margin-left 必须跟随侧边栏宽度动态变化 */
.main-content {
  margin-left: var(--sidebar-width);
  flex: 1;
  padding: 25px;
  overflow-x: hidden;
  transition: margin-left 0.3s ease;
}

/* 响应式适配核心代码 */
@media (max-width: 768px) {
  /* 手机端侧边栏缩窄为 70px，主内容区同步调整 */
  .main-content {
    margin-left: 70px;
    padding: 15px;
  }

  .art-title {
    font-size: 22px !important;
    letter-spacing: 2px !important;
    margin-bottom: 15px !important;
  }

  .workspace { gap: 15px !important; }

  .display-container {
    height: 200px !important;
  }

  /* 参数网格在手机端变为 2 列 */
  .param-grid {
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 12px !important;
  }

  .param-unit { gap: 3px !important; }

  .param-btn {
    width: 100% !important;
    height: 40px !important;
    font-size: 12px !important;
  }

  .param-input {
    font-size: 13px !important;
  }

  /* 底部控制台：手机端由横向 Row 变为纵向 Column */
  .bottom-console {
    flex-direction: column !important;
    padding: 15px !important;
    gap: 15px !important;
    align-items: stretch !important;
  }

  .action-buttons {
    width: 100%;
    justify-content: space-between !important;
    gap: 8px !important;
  }

  .action-btn {
    flex: 1;
    padding: 0 !important;
    font-size: 13px !important;
    height: 45px !important;
    min-width: 60px;
  }

  .monitor-display {
    width: 100%;
    align-items: center !important;
    border-top: 1px solid #1e1e35;
    padding-top: 10px;
  }

  .digital-screen {
    width: 100%;
    font-size: 24px !important;
    min-width: unset !important;
  }

  .status-info {
    font-size: 13px;
  }
}

/* 原有 PC 端样式保留 */
.art-title { text-align: center; font-size: 36px; background: linear-gradient(to bottom, #fff, #00c7ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 25px; letter-spacing: 5px; }
.workspace { max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 25px; }
.display-container { height: 320px; background: rgba(10, 10, 20, 0.8); border: 1px solid #1e1e35; border-radius: 12px; position: relative; }
.placeholder-3d { height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px; }
.status-tag { padding: 4px 12px; border-radius: 4px; font-size: 12px; }
.status-growing { background: rgba(0, 255, 136, 0.1); color: #00ff88; border: 1px solid #00ff88; }
.status-paused { background: rgba(255, 145, 0, 0.1); color: #ff9100; border: 1px solid #ff9100; }
.scanner-line { position: absolute; width: 100%; height: 2px; background: #00c7ff; box-shadow: 0 0 15px #00c7ff; animation: scan 3s infinite linear; }
.connection-svg { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
.draw-line { stroke: rgba(0, 199, 255, 0.1); stroke-width: 1; }
.active-line { stroke: rgba(0, 255, 136, 0.4); stroke-dasharray: 4; animation: dash 5s linear infinite; }
.param-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; }
.param-unit { display: flex; flex-direction: column; gap: 5px; align-items: center; position: relative; }
.param-input { width: 100%; background: #000; border: 1px solid #2d2d44; color: #00ff88; text-align: center; border-radius: 4px; padding: 5px 0; }
.param-btn { width: 120px; height: 45px; background: #161625; border: 1px solid #3d3d5c; color: #aaaabf; border-radius: 6px; cursor: pointer; transition: 0.2s; }
.param-btn:active { transform: scale(0.95); }
.mini-warn { position: absolute; bottom: -18px; font-size: 10px; color: #ff3d00; }
.bottom-console { display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; background: #0a0a16; border-radius: 15px; border: 1px solid #1e1e35; }
.action-buttons { display: flex; gap: 10px; }
.action-btn { padding: 0 20px; height: 50px; border-radius: 8px; border: none; font-weight: bold; cursor: pointer; transition: 0.2s; }
.action-btn:active { transform: scale(0.95); }
.predict-btn { background: #00c7ff; }
.pause-btn { background: #ff9100; }
.stop-btn { background: #ff3d00; color: #fff; }
.reset-btn { background: #444; color: #fff; }
.monitor-display { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
.digital-screen { font-family: 'Courier New', monospace; font-size: 32px; color: #00ff88; background: #000; padding: 10px 20px; border-radius: 8px; border: 1px solid #00ff88; min-width: 180px; text-align: center; }
.paused-screen { filter: grayscale(1); opacity: 0.5; }
.export-btn { background: #00ff88; border: none; padding: 8px 15px; border-radius: 4px; font-weight: bold; cursor: pointer; margin-top: 5px; }
.alert-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 3000; }
.alert-box { background: #1a0000; border: 2px solid #ff3d00; padding: 30px; border-radius: 12px; text-align: center; box-shadow: 0 0 30px rgba(255,61,0,0.3); }
.alert-box h3 { color: #ff3d00; margin-bottom: 10px; }
.alert-box button { background: #ff3d00; color: white; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; margin-top: 15px; }

@keyframes scan { from { top: 0; } to { top: 100%; } }
@keyframes dash { from { stroke-dashoffset: 100; } to { stroke-dashoffset: 0; } }
</style>