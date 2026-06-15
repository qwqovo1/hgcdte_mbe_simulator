<template>
  <div class="layout">
    <Sidebar />
    <main class="main-content">
      <div class="header">
        <button @click="$router.push('/reports')" class="btn-back">⬅ 返回</button>
        <h2>报告管理</h2>
      </div>

      <div class="table-wrapper">
        <!-- 桌面端表格 -->
        <div class="table-scroll desktop-table">
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

        <!-- 手机端卡片列表 -->
        <div class="mobile-cards">
          <div v-for="file in files" :key="'m-'+file.name" class="file-card">
            <div class="file-card-header" @click="viewFile(file.name)">
              <span class="file-card-name">📄 {{ file.name }}</span>
            </div>
            <div class="file-card-meta">
              <span>{{ file.size }}</span>
              <span>{{ file.time }}</span>
            </div>
            <div class="file-card-ops">
              <button @click="download(file.name)">下载</button>
              <button @click="del(file.name)" class="btn-del">删除</button>
            </div>
          </div>
          <div v-if="files.length === 0" class="empty-tip">暂无报告文件</div>
        </div>
      </div>

      <!-- 预览模态框 -->
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
.main-content { flex: 1; margin-left: var(--sidebar-width); padding: 20px; transition: margin-left 0.3s ease; }

.header { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; color: white; }
.header h2 { margin: 0; font-size: 20px; }
.btn-back {
  background: rgba(22, 22, 37, 0.8);
  border: 1px solid #2d2d44;
  color: #00c7ff;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.table-wrapper { background: #11111d; border: 1px solid #333; border-radius: 8px; overflow: hidden; }
.table-scroll { overflow-x: auto; }

.t-row {
  display: grid;
  grid-template-columns: 2fr 80px 150px 150px;
  padding: 15px 20px;
  border-bottom: 1px solid #222;
  color: #ccc;
  align-items: center;
}
.t-head { background: #1a1a2e; color: #00c7ff; font-weight: bold; }
.fname { color: #00ff88; cursor: pointer; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fsize { font-size: 13px; }
.ftime { font-size: 13px; }
.fops { display: flex; gap: 10px; }
.fops button { background: #222; border: 1px solid #444; color: #eee; padding: 5px 10px; cursor: pointer; border-radius: 4px; font-size: 12px; }
.btn-del { border-color: #ff3d00 !important; color: #ff3d00 !important; }

/* 手机端卡片 - 默认隐藏 */
.mobile-cards { display: none; }

.file-card {
  background: #161625;
  border: 1px solid #2d2d44;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
}
.file-card-header { margin-bottom: 8px; }
.file-card-name { color: #00ff88; font-size: 14px; font-weight: 500; word-break: break-all; }
.file-card-meta { display: flex; gap: 15px; font-size: 12px; color: #6a6a85; margin-bottom: 10px; }
.file-card-ops { display: flex; gap: 10px; }
.file-card-ops button { background: #222; border: 1px solid #444; color: #eee; padding: 6px 14px; cursor: pointer; border-radius: 6px; font-size: 12px; }
.file-card-ops .btn-del { border-color: #ff3d00 !important; color: #ff3d00 !important; }
.empty-tip { text-align: center; color: #6a6a85; padding: 30px; font-size: 14px; }

/* 弹窗 */
.modal { position: fixed; inset: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 15px; }
.modal-box { background: #11111d; width: 80%; max-width: 800px; max-height: 80vh; display: flex; flex-direction: column; border: 1px solid #444; border-radius: 12px; overflow: hidden; }
.m-head { padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; color: white; }
.m-head h3 { margin: 0; font-size: 16px; word-break: break-all; }
.m-head button { background: #333; border: 1px solid #555; color: #eee; padding: 6px 14px; border-radius: 4px; cursor: pointer; }
.m-body { flex: 1; padding: 15px; overflow: auto; background: #000; color: #00ff88; font-family: monospace; font-size: 13px; }

/* ━━━ 手机适配 ━━━ */
@media (max-width: 768px) {
  .main-content { margin-left: 60px; padding: 12px; }
  .header { gap: 12px; }
  .header h2 { font-size: 16px; }

  /* 桌面表格隐藏，卡片显示 */
  .desktop-table { display: none; }
  .mobile-cards { display: block; padding: 12px; }

  .modal-box { width: 95%; max-height: 85vh; }
  .m-head { padding: 12px 14px; }
  .m-head h3 { font-size: 14px; }
  .m-body { font-size: 11px; padding: 10px; }
}
</style>