<template>
  <div class="layout">
    <Sidebar />
    <main class="main-content">
      <div class="experiment-wrapper">
        <h1 class="art-title">HgCdTe 实验控制台</h1>

        <div class="workspace">
          <div class="display-container" ref="displayBox">
            <div class="scene-host" :class="{ 'scene-disabled': showModal || alertMsg }">
               <LabScene ref="labScene" :params="parameters" :growing="isExperimenting && !isPaused" :paused="isPaused" @device-click="handle3DDeviceClick" />
            </div>

            <div class="overlay-status">
              <div class="scanner-line" v-if="isExperimenting && !isPaused"></div>
              <div class="status-tag" :class="statusClass">{{ statusText }}</div>
              <span class="status-info">{{ isExperimenting ? (isPaused ? '生长已挂起' : 'HgCdTe 原子层沉积中...') : '系统就绪 - 点击设备可调节参数' }}</span>
            </div>

            <svg class="connection-svg">
              <line v-for="(pos, index) in linePositions" :key="index"
                :x1="pos.x1" :y1="pos.y1" :x2="pos.x2" :y2="pos.y2"
                class="draw-line" :class="{ 'active-line': isExperimenting && !isPaused }" />
            </svg>
          </div>

          <div class="control-panel">
            <div class="param-grid">
              <div v-for="(param, index) in parameters" :key="index" class="param-unit" :ref="'param-' + index">
                <input type="number" v-model.number="param.value" @input="checkSafety(param)" class="param-input" :class="{'editing-highlight': editingIndex === index}" />
                <button class="param-btn" @click="openEditModal(index)">{{ param.label }}</button>
                <div v-if="param.warning" class="mini-warn">{{ param.warning }}</div>
              </div>
            </div>
          </div>

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
              <button v-if="!isExperimenting && elapsed > 0" class="export-btn" @click="exportData">📋 保存报告</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 参数调节弹窗 -->
      <teleport to="body">
        <div v-if="showModal" class="modal-overlay" @click="handleOverlayClick" @mousedown.stop @mouseup.stop @touchstart.stop @touchend.stop>
          <div class="modal-box glass-effect" @click.stop @mousedown.stop @mouseup.stop>
            <div class="modal-header">
              <h3>⚙️ 参数调节: {{ parameters[editingIndex] ? parameters[editingIndex].label : '' }}</h3>
              <button type="button" class="close-btn" @click.stop.prevent="closeModal" tabindex="0">
                <span class="close-icon">×</span>
              </button>
            </div>
            <div class="modal-body">
              <div class="input-wrapper">
                <label>设定值</label>
                <input type="number" v-model.number="tempValue" class="large-input" @keyup.enter="saveParam" @keyup.esc="closeModal" />
              </div>

              <div class="slider-wrapper">
                <input type="range"
                  v-model.number="tempValue"
                  :min="0"
                  :max="parameters[editingIndex] ? parameters[editingIndex].normal * 2.5 : 100"
                  step="0.1"
                  class="range-slider"
                />
                <div class="range-labels">
                  <span>0</span>
                  <span>标准值: {{ parameters[editingIndex] ? parameters[editingIndex].normal : '' }}</span>
                  <span>MAX</span>
                </div>
              </div>

              <p class="safety-tip" v-if="parameters[editingIndex] && tempValue > parameters[editingIndex].normal * 1.5">
                ⚠️ 警告：当前设定值偏离标准工艺较大
              </p>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn-cancel" @click.stop.prevent="closeModal">取消</button>
              <button type="button" class="btn-confirm" @click.stop.prevent="saveParam">确认修改</button>
            </div>
          </div>
        </div>
      </teleport>

      <!-- 警告弹窗 -->
      <teleport to="body">
        <div v-if="alertMsg" class="alert-overlay" @click="handleAlertOverlayClick" @mousedown.stop @mouseup.stop @touchstart.stop @touchend.stop>
          <div class="alert-box" @click.stop @mousedown.stop @mouseup.stop>
            <button type="button" class="alert-close-btn" @click.stop.prevent="closeAlert">
              <span>×</span>
            </button>
            <h3>🚨 硬件保护性停机</h3>
            <p>{{ alertMsg }}</p>
            <button type="button" class="alert-confirm-btn" @click.stop.prevent="closeAlert">确定</button>
          </div>
        </div>
      </teleport>
    </main>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'
import LabScene from './LabScene.vue'
import axios from 'axios'

export default {
  name: 'Experiment',
  components: { Sidebar, LabScene },
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
      ],
      showModal: false,
      editingIndex: 0,
      tempValue: 0,
      deviceMapping: {
        'Substrate_Heater': 0,
        'Hg_Source': 1,
        'CdTe_Source': 2,
        'Te_Source': 3,
        'Hg_Flux': 4,
        'Main_Chamber': 5,
        'Vacuum_Pump': 5,
        'Beam_Pressure': 6,
        'Rotation_Motor': 7,
        'Cooling_System': 8,
        'Growth_Controller': 9
      }
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
    // 添加ESC键关闭弹窗
    window.addEventListener('keydown', this.handleKeyDown);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.calculateLines);
    window.removeEventListener('keydown', this.handleKeyDown);
    if(this.timer) clearInterval(this.timer);
  },
  methods: {
    handleKeyDown(e) {
      if (e.key === 'Escape') {
        if (this.showModal) {
          this.closeModal();
        } else if (this.alertMsg) {
          this.closeAlert();
        }
      }
    },
    handle3DDeviceClick(deviceName) {
      // 如果弹窗已打开，不响应3D点击
      if (this.showModal || this.alertMsg) {
        return;
      }
      console.log("收到 3D 点击事件:", deviceName);
      if (this.deviceMapping.hasOwnProperty(deviceName)) {
        var index = this.deviceMapping[deviceName];
        this.openEditModal(index);
      }
    },
    openEditModal(index) {
      // 防止重复打开
      if (this.showModal) {
        return;
      }
      this.editingIndex = index;
      this.tempValue = this.parameters[index].value;
      this.showModal = true;
      // 禁用body滚动
      document.body.style.overflow = 'hidden';
    },
    closeModal() {
      this.showModal = false;
      // 恢复body滚动
      document.body.style.overflow = '';
    },
    handleOverlayClick(e) {
      // 只有点击蒙层本身才关闭
      if (e.target === e.currentTarget) {
        this.closeModal();
      }
    },
    handleAlertOverlayClick(e) {
      // 只有点击蒙层本身才关闭
      if (e.target === e.currentTarget) {
        this.closeAlert();
      }
    },
    closeAlert() {
      this.alertMsg = null;
      document.body.style.overflow = '';
    },
    saveParam() {
      if (this.parameters[this.editingIndex]) {
        this.parameters[this.editingIndex].value = parseFloat(this.tempValue);
        this.checkSafety(this.parameters[this.editingIndex]);
      }
      this.closeModal();
    },
    calculateLines() {
      if (!this.$refs.displayBox || window.innerWidth < 768) {
        this.linePositions = [];
        return;
      }
      var box = this.$refs.displayBox.getBoundingClientRect();
      var self = this;
      this.linePositions = this.parameters.map(function(_, index) {
        var ref = self.$refs['param-' + index];
        if (!ref || !ref[0]) return {x1:0,y1:0,x2:0,y2:0};
        var el = ref[0].getBoundingClientRect();
        return { x1: el.left + el.width / 2 - box.left, y1: el.top - box.top, x2: box.width / 2, y2: box.height };
      });
    },
    checkSafety(param) {
      var ratio = param.value / param.normal;
      if (ratio >= 2.0) {
        this.alertMsg = param.label + ' 超出安全阈值200%，系统已自动停机。';
        document.body.style.overflow = 'hidden';
        if (this.isExperimenting && !this.isPaused) this.handleAction('togglePause');
        param.warning = "危险";
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
      var self = this;
      clearInterval(this.timer);
      this.timer = setInterval(function() {
        var Ts = self.parameters[0].value;
        var hgFlux = self.parameters[4].value;
        var cdteTemp = self.parameters[2].value;
        var tempEfficiency = Math.max(0, 1 - Math.abs(Ts - 185) / 25);
        var cdteContribution = Math.pow(cdteTemp / 450, 4) * 0.003;
        var hgCoverage = Math.min(1, hgFlux / 2.0);
        self.currentThickness += cdteContribution * tempEfficiency * hgCoverage;
        self.elapsed += 1;
      }, 1000);
    },
    async exportData() {
      var payload = {
        name: "HgCdTe 穿透模拟实验",
        startTime: this.startTime.toLocaleString(),
        duration: this.elapsed + 's',
        parameters: this.parameters.reduce(function(acc, curr) { acc[curr.label] = curr.value; return acc; }, {}),
        thickness: this.currentThickness.toFixed(4)
      };
      try {
        await axios.post('/api/experiment/export', payload);
        alert('✅ 报告已保存至 Data 文件夹');
      } catch (err) { alert('❌ 接口连接失败，请检查内置穿透'); }
    },
    focusInput(index) {
      var ref = this.$refs['param-' + index];
      if (ref && ref[0]) {
        ref[0].querySelector('input').focus();
      }
    }
  }
}
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; background-color: #05050a; color: white; }

.main-content {
  margin-left: var(--sidebar-width);
  flex: 1;
  padding: 25px;
  overflow-x: hidden;
  transition: margin-left 0.3s ease;
}

@media (max-width: 768px) {
  .main-content { margin-left: 70px; padding: 15px; }
  .art-title { font-size: 22px !important; letter-spacing: 2px !important; margin-bottom: 15px !important; }
  .workspace { gap: 15px !important; }
  .display-container { height: 200px !important; }
  .param-grid { grid-template-columns: repeat(2, 1fr) !important; gap: 12px !important; }
  .param-unit { gap: 3px !important; }
  .param-btn { width: 100% !important; height: 40px !important; font-size: 12px !important; }
  .param-input { font-size: 13px !important; }
  .bottom-console { flex-direction: column !important; padding: 15px !important; gap: 15px !important; align-items: stretch !important; }
  .action-buttons { width: 100%; justify-content: space-between !important; gap: 8px !important; }
  .action-btn { flex: 1; padding: 0 !important; font-size: 13px !important; height: 45px !important; min-width: 60px; }
  .monitor-display { width: 100%; align-items: center !important; border-top: 1px solid #1e1e35; padding-top: 10px; }
  .digital-screen { width: 100%; font-size: 24px !important; min-width: unset !important; }
  .status-info { font-size: 13px; }
}

.art-title { text-align: center; font-size: 36px; background: linear-gradient(to bottom, #fff, #00c7ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 25px; letter-spacing: 5px; }
.workspace { max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 25px; }

.display-container {
    height: 400px;
    background: rgba(10, 10, 20, 0.8);
    border: 1px solid #1e1e35;
    border-radius: 12px;
    position: relative;
    overflow: hidden;
}

.scene-host {
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0; left: 0;
    z-index: 1;
    transition: opacity 0.2s;
}

.scene-host.scene-disabled {
    pointer-events: none;
    opacity: 0.6;
}

.overlay-status {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 5;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    pointer-events: none;
}

.placeholder-3d { display: none; }

.status-tag { padding: 4px 12px; border-radius: 4px; font-size: 12px; margin-bottom: 5px; backdrop-filter: blur(2px); }
.status-info { font-size: 12px; color: rgba(255,255,255,0.7); text-shadow: 0 1px 2px black; }

.status-growing { background: rgba(0, 255, 136, 0.2); color: #00ff88; border: 1px solid #00ff88; }
.status-paused { background: rgba(255, 145, 0, 0.2); color: #ff9100; border: 1px solid #ff9100; }
.scanner-line { position: absolute; top: 0; left:0; width: 100%; height: 2px; background: #00c7ff; box-shadow: 0 0 15px #00c7ff; animation: scan 3s infinite linear; z-index: 10; pointer-events: none; }

.connection-svg { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 2; }
.draw-line { stroke: rgba(0, 199, 255, 0.3); stroke-width: 1; }
.active-line { stroke: rgba(0, 255, 136, 0.6); stroke-dasharray: 4; animation: dash 5s linear infinite; }

.param-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; }
.param-unit { display: flex; flex-direction: column; gap: 5px; align-items: center; position: relative; }
.param-input { width: 100%; background: #000; border: 1px solid #2d2d44; color: #00ff88; text-align: center; border-radius: 4px; padding: 5px 0; transition: border-color 0.3s;}
.param-input.editing-highlight { border-color: #00c7ff; box-shadow: 0 0 8px rgba(0,199,255,0.3); }

.param-btn { width: 120px; height: 45px; background: #161625; border: 1px solid #3d3d5c; color: #aaaabf; border-radius: 6px; cursor: pointer; transition: 0.2s; }
.param-btn:active { transform: scale(0.95); }
.param-btn:hover { border-color: #00c7ff; color: white; }

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

/* ===== 弹窗蒙层和关闭按钮优化 ===== */

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}

.glass-effect {
  background: rgba(22, 22, 37, 0.98);
  border: 1px solid #00c7ff;
  box-shadow: 0 0 40px rgba(0,199,255,0.2), 0 8px 32px rgba(0,0,0,0.5);
}

.modal-box {
  width: 420px;
  max-width: 90vw;
  border-radius: 12px;
  overflow: hidden;
  animation: popIn 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
}

.modal-header {
  background: rgba(0, 199, 255, 0.1);
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #2d2d44;
  position: relative;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: #fff;
  flex: 1;
  padding-right: 40px;
}

.close-btn {
  position: absolute;
  top: 50%;
  right: 12px;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  padding: 0;
  z-index: 10;
}

.close-btn:hover {
  background: rgba(255, 61, 0, 0.3);
  border-color: #ff3d00;
}

.close-btn:active {
  transform: translateY(-50%) scale(0.92);
  background: rgba(255, 61, 0, 0.5);
}

.close-btn:focus {
  outline: 2px solid #00c7ff;
  outline-offset: 2px;
}

.close-btn .close-icon {
  font-size: 22px;
  font-weight: bold;
  color: #aaa;
  line-height: 1;
  transition: color 0.2s;
}

.close-btn:hover .close-icon {
  color: #fff;
}

.modal-body {
  padding: 25px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-wrapper label {
  display: block;
  color: #888;
  margin-bottom: 8px;
  font-size: 14px;
}

.large-input {
  width: 100%;
  background: #000;
  border: 1px solid #444;
  color: #00c7ff;
  font-size: 28px;
  text-align: center;
  padding: 10px;
  border-radius: 8px;
  font-family: monospace;
  box-sizing: border-box;
}

.large-input:focus {
  outline: none;
  border-color: #00c7ff;
  box-shadow: 0 0 10px rgba(0, 199, 255, 0.3);
}

.slider-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.range-slider {
  width: 100%;
  cursor: pointer;
  accent-color: #00c7ff;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.safety-tip {
  font-size: 12px;
  color: #ff9100;
  text-align: center;
  background: rgba(255, 145, 0, 0.1);
  padding: 8px;
  border-radius: 4px;
  margin: 0;
}

.modal-footer {
  padding: 16px 25px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid #2d2d44;
}

.btn-cancel {
  background: transparent;
  border: 1px solid #555;
  color: #ccc;
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-cancel:hover {
  border-color: #888;
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}

.btn-confirm {
  background: #00c7ff;
  border: none;
  color: #000;
  font-weight: bold;
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-confirm:hover {
  background: #00e1ff;
  box-shadow: 0 0 15px rgba(0, 199, 255, 0.5);
}

.btn-confirm:active {
  transform: scale(0.96);
}

/* ===== 警告弹窗优化 ===== */

.alert-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
}

.alert-box {
  background: linear-gradient(135deg, #1a0505 0%, #2a0a0a 100%);
  border: 2px solid #ff3d00;
  padding: 30px 35px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 0 40px rgba(255, 61, 0, 0.35), 0 8px 32px rgba(0,0,0,0.5);
  position: relative;
  max-width: 400px;
  animation: shake 0.5s ease-in-out;
}

.alert-close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  padding: 0;
  color: #aaa;
  font-size: 20px;
  font-weight: bold;
  line-height: 1;
}

.alert-close-btn:hover {
  background: rgba(255, 61, 0, 0.4);
  border-color: #ff3d00;
  color: #fff;
}

.alert-close-btn:active {
  transform: scale(0.9);
}

.alert-box h3 {
  color: #ff3d00;
  margin: 0 0 15px 0;
  font-size: 18px;
}

.alert-box p {
  color: #ffaa88;
  margin: 0 0 20px 0;
  font-size: 14px;
  line-height: 1.5;
}

.alert-confirm-btn {
  background: #ff3d00;
  color: white;
  border: none;
  padding: 10px 30px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: all 0.2s;
}

.alert-confirm-btn:hover {
  background: #ff5522;
  box-shadow: 0 0 15px rgba(255, 61, 0, 0.5);
}

.alert-confirm-btn:active {
  transform: scale(0.96);
}

@keyframes popIn {
  from {
    transform: scale(0.85);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

@keyframes scan {
  from { top: 0; }
  to { top: 100%; }
}

@keyframes dash {
  from { stroke-dashoffset: 100; }
  to { stroke-dashoffset: 0; }
}
</style>