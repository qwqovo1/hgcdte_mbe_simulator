<template>
  <div class="layout">
    <Sidebar />
    <main class="main-content">
      <div class="header">
        <button @click="$router.push('/reports')" class="btn-back">⬅ 返回</button>
        <h2>报告管理</h2>
      </div>

      <!-- 手机端自动开启横向滚动 -->
      <div class="table-wrapper">
        <div class="table-scroll">
          <div class="t-row t-head">
            <span>文件名</span><span>大小</span><span>日期</span><span>操作</span>
          </div>
          <div v-for="file in files" :key="file.name" class="t-row">
            <span class="fname" @click="viewFile(file.name)">{{ file.name }}</span>
            <span class="fsize">{{ file.size }}</span>
            <span class="ftime">{{ file.time }}</span>
            <div class="fops">
              <button @click="download(file.name)">下载</button>
              <button @click="del(file.name)" class="btn-del">删除</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 预览模态框自适应 -->
      <div v-if="viewer.show" class="modal">
        <div class="modal-box">
          <div class="m-head">
            <h3>{{ viewer.name }}</h3>
            <button @click="viewer.show = false">关闭</button>
          </div>
          <div class="m-body">
            <pre>{{ viewer.content }}</pre>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'
import axios from 'axios'
export default {
  components: { Sidebar },
  data() { return { files: [], viewer: { show: false, name: '', content: '' } } },
  mounted() { this.refresh() },
  methods: {
    async refresh() { const res = await axios.get("/api/experiment/files"); this.files = res.data; },
    async viewFile(name) {
      const res = await axios.get(`/api/experiment/files/${name}`);
      this.viewer = { show: true, name, content: res.data.content };
    },
    download(name) { window.open(`/api/experiment/download/${name}`) },
    async del(name) { if(confirm('删除?')) { await axios.delete(`/api/experiment/files/${name}`); this.refresh(); } }
  }
}
</script>

<style scoped>
.layout { display: flex; background: #05050a; min-height: 100vh; }
.main-content { flex: 1; margin-left: var(--sidebar-width); padding: 20px; transition: 0.3s; }

.header { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; color: white; }
.table-wrapper { background: #11111d; border: 1px solid #333; border-radius: 8px; overflow: hidden; }
.table-scroll { overflow-x: auto; } /* 关键：允许横向滚动 */

.t-row {
  display: grid;
  grid-template-columns: 250px 80px 150px 150px; /* 固定宽度，防止手机端挤压变形 */
  padding: 15px; border-bottom: 1px solid #222; color: #ccc; align-items: center;
}
.t-head { background: #1a1a2e; color: #00c7ff; font-weight: bold; }
.fname { color: #00ff88; cursor: pointer; overflow: hidden; text-overflow: ellipsis; }
.fops { display: flex; gap: 10px; }
.fops button { background: #222; border: 1px solid #444; color: #eee; padding: 5px 10px; cursor: pointer; }
.btn-del { border-color: #ff3d00 !important; color: #ff3d00 !important; }

@media (max-width: 768px) {
  .main-content { margin-left: 70px; padding: 10px; }
  .modal-box { width: 95% !important; margin: 10px; }
}

.modal { position: fixed; inset: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 2000; }
.modal-box { background: #11111d; width: 80%; max-height: 80vh; display: flex; flex-direction: column; border: 1px solid #444; }
.m-head { padding: 15px; display: flex; justify-content: space-between; border-bottom: 1px solid #333; color: white; }
.m-body { flex: 1; padding: 15px; overflow-y: auto; background: #000; color: #00ff88; font-family: monospace; }
</style>