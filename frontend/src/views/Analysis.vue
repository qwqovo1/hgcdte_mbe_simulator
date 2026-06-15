<template>
  <div class="layout">
    <Sidebar />
    <main class="main-content">
      <div class="analysis-wrapper">
        <h1 class="page-title">🤖 智能分析和建议</h1>

        <div class="chat-container">
          <!-- 聊天消息区域 -->
          <div class="chat-messages" ref="messagesContainer">
            <div class="welcome-message">
              <div class="ai-avatar">🤖</div>
              <div class="message-content">
                <div class="message-bubble ai-message">
                  <p>您好！我是 MBE 智能分析助手。</p>
                  <p>我可以帮您分析实验数据、优化工艺参数、诊断设备状态等。</p>
                  <p>💡 点击 <strong>📂 加载实验报告</strong> 加载数据，开启 <strong>📚 论文佐证</strong> 让分析结果有据可依！</p>
                  <p style="font-size: 12px; color: rgba(255,255,255,0.4); margin-top: 8px;">
                    📚 论文佐证功能会自动检索 arXiv、Semantic Scholar 数据库，为 AI 分析提供学术文献支撑。
                  </p>
                </div>
                <div class="message-time">{{ getCurrentTime() }}</div>
              </div>
            </div>

            <!-- 动态消息列表 -->
            <div
              v-for="(message, index) in messages"
              :key="index"
              class="message-item"
              :class="{ 'user-message-item': message.type === 'user', 'ai-message-item': message.type === 'ai' }"
            >
              <div v-if="message.type === 'user'" class="user-avatar">👤</div>
              <div v-else class="ai-avatar">🤖</div>

              <div class="message-content">
                <div class="message-bubble" :class="message.type === 'user' ? 'user-message' : 'ai-message'">
                  <div v-html="message.content"></div>
                </div>

                <!-- 论文佐证状态指示 -->
                <div v-if="message.type === 'ai' && message.evidenceStatus" class="evidence-status-bar">
                  <span v-if="message.evidenceStatus === 'success'" class="status-success">
                    ✅ 已检索到 {{ message.papers.length }} 篇相关论文佐证
                  </span>
                  <span v-else-if="message.evidenceStatus === 'no_papers_found'" class="status-warning">
                    ⚠️ 未检索到高度相关论文（已使用搜索词：{{ message.searchKeywords?.join(', ') }}）
                  </span>
                  <span v-else-if="message.evidenceStatus === 'disabled'" class="status-disabled">
                    💤 论文佐证未开启
                  </span>
                </div>

                <!-- 论文佐证卡片区域 -->
                <div v-if="message.type === 'ai' && message.papers && message.papers.length > 0" class="papers-section">
                  <div class="papers-header" @click="message.showPapers = !message.showPapers">
                    <span class="papers-toggle">{{ message.showPapers ? '▼' : '▶' }}</span>
                    <span class="papers-title">📚 学术论文佐证 ({{ message.papers.length }}篇)</span>
                    <span class="papers-badge">来自 arXiv / Semantic Scholar</span>
                  </div>

                  <div class="papers-list" v-show="message.showPapers">
                    <div
                      v-for="(paper, pIdx) in message.papers"
                      :key="pIdx"
                      class="paper-card"
                    >
                      <div class="paper-card-header">
                        <div class="paper-source-badge" :class="getSourceClass(paper.source)">
                          {{ paper.source }}
                        </div>
                        <div class="paper-relevance-tag" v-if="paper.relevance">
                          {{ paper.relevance }}
                        </div>
                      </div>

                      <div class="paper-title">
                        <a :href="paper.url" target="_blank" rel="noopener">
                          📄 {{ paper.title }}
                        </a>
                      </div>

                      <div class="paper-authors">
                        👥 {{ paper.authors }} ({{ paper.year }})
                      </div>

                      <div class="paper-abstract" v-if="paper.abstract">
                        <span class="abstract-label">摘要：</span>
                        {{ paper.abstract.slice(0, 200) }}{{ paper.abstract.length > 200 ? '...' : '' }}
                      </div>

                      <div class="paper-meta">
                        <span v-if="paper.citation_count > 0" class="meta-item citations">
                          📈 被引 {{ paper.citation_count }} 次
                        </span>
                        <span v-if="paper.arxiv_id" class="meta-item">
                          🔗 arXiv:{{ paper.arxiv_id }}
                        </span>
                        <span v-if="paper.doi" class="meta-item">
                          🔗 DOI:{{ paper.doi }}
                        </span>
                        <a :href="paper.url" target="_blank" class="meta-item paper-link">
                          🌐 查看原文 →
                        </a>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="message-time">{{ message.time }}</div>
              </div>
            </div>

            <!-- AI 正在处理指示器 -->
            <div v-if="isTyping" class="message-item ai-message-item">
              <div class="ai-avatar">🤖</div>
              <div class="message-content">
                <div class="message-bubble ai-message typing-indicator">
                  <div class="typing-dots">
                    <span></span><span></span><span></span>
                  </div>
                  <div class="typing-label" v-if="typingStage">{{ typingStage }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 快捷建议按钮（可收起） -->
          <div class="quick-suggestions" v-if="messages.length === 0">
            <div class="suggestions-header" @click="showSuggestions = !showSuggestions">
              <h3>💡 常见问题</h3>
              <span class="suggestions-toggle">{{ showSuggestions ? '▲ 收起' : '▼ 展开' }}</span>
            </div>
            <transition name="suggestions-slide">
              <div class="suggestion-buttons" v-show="showSuggestions">
                <button
                  v-for="suggestion in quickSuggestions"
                  :key="suggestion.id"
                  class="suggestion-btn"
                  @click="sendQuickMessage(suggestion.text)"
                >
                  <span class="suggestion-icon">{{ suggestion.icon }}</span>
                  <span class="suggestion-text">{{ suggestion.text }}</span>
                </button>
              </div>
            </transition>
          </div>

          <!-- 工具栏 -->
          <div class="report-toolbar">
            <div class="loaded-reports" v-if="loadedReports.length > 0">
              <span class="loaded-label">📋 已加载：</span>
              <span
                v-for="(rpt, idx) in loadedReports"
                :key="idx"
                class="report-tag"
              >
                {{ rpt.name }}
                <span class="tag-remove" @click="removeReport(idx)">✕</span>
              </span>
            </div>

            <div class="toolbar-actions">
              <button
                class="load-report-btn"
                @click="openReportModal"
                :disabled="isTyping"
              >
                📂 加载实验报告
              </button>

              <!-- 论文佐证开关 -->
              <button
                class="evidence-toggle-btn"
                :class="{ active: enableEvidence }"
                @click="toggleEvidence"
                :title="enableEvidence ? '点击关闭论文佐证' : '点击开启论文佐证（自动检索学术论文支撑分析）'"
              >
                📚 论文佐证
                <span class="toggle-indicator" :class="{ on: enableEvidence }">
                  {{ enableEvidence ? 'ON' : 'OFF' }}
                </span>
              </button>

              <!-- 独立论文搜索 -->
              <button
                class="search-paper-btn"
                @click="showPaperSearch = !showPaperSearch"
                title="手动搜索学术论文"
              >
                🔍 搜索论文
              </button>
            </div>
          </div>

          <!-- 独立论文搜索栏 -->
          <div class="paper-search-bar" v-if="showPaperSearch">
            <input
              v-model="paperSearchQuery"
              @keydown.enter="doManualPaperSearch"
              placeholder="输入关键词搜索论文，如: HgCdTe MBE growth temperature"
              class="paper-search-input"
            />
            <button @click="doManualPaperSearch" :disabled="!paperSearchQuery.trim() || paperSearching" class="paper-search-submit">
              {{ paperSearching ? '搜索中...' : '搜索' }}
            </button>
          </div>

          <!-- 输入区域 -->
          <div class="chat-input-area">
            <div class="input-container">
              <textarea
                v-model="inputMessage"
                @keydown="handleKeyDown"
                @input="adjustTextareaHeight"
                ref="messageInput"
                placeholder="请输入您的问题或需求..."
                class="message-input"
                rows="1"
                :disabled="isTyping"
              ></textarea>

              <div class="input-actions">
                <button
                  class="send-btn"
                  @click="sendMessage"
                  :disabled="!inputMessage.trim() || isTyping"
                  :class="{ 'active': inputMessage.trim() && !isTyping }"
                >
                  <span class="send-icon">📤</span>
                </button>
              </div>
            </div>

            <div class="input-footer">
              <div class="input-tips">
                <span class="tip-text">
                  💡 Ctrl+Enter 发送 |
                  论文佐证
                  <span :style="{ color: enableEvidence ? '#81c784' : 'rgba(255,255,255,0.4)' }">
                    {{ enableEvidence ? '🟢 已开启' : '⚪ 已关闭' }}
                  </span>
                </span>
                <span class="model-status">
                  <span class="status-dot" :class="apiOnline ? 'online' : 'offline'"></span>
                  {{ apiOnline ? `已连接 ${apiModel}` : '模型未接入' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 报告选择弹窗 -->
    <div class="modal-overlay" v-if="showReportModal" @click.self="showReportModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>📂 选择实验报告</h3>
          <button class="modal-close" @click="showReportModal = false">✕</button>
        </div>

        <div class="modal-body">
          <div v-if="reportListLoading" class="modal-loading">
            <div class="typing-dots"><span></span><span></span><span></span></div>
            <p>正在加载报告列表...</p>
          </div>

          <div v-else-if="reportList.length === 0" class="modal-empty">
            <p>📭 Data/ 目录下暂无实验报告文件</p>
            <p class="modal-hint">请先在「仿真实验」页面完成一次实验并导出报告</p>
          </div>

          <div v-else class="report-list">
            <div
              v-for="report in reportList"
              :key="report.name"
              class="report-item"
              :class="{ 'selected': selectedReports.includes(report.name) }"
              @click="toggleReportSelect(report.name)"
            >
              <div class="report-checkbox">
                <span v-if="selectedReports.includes(report.name)">☑</span>
                <span v-else>☐</span>
              </div>
              <div class="report-info">
                <div class="report-name">{{ report.name }}</div>
                <div class="report-meta">
                  <span>📅 {{ report.time }}</span>
                  <span>📦 {{ report.size }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <div class="modal-footer-info">已选 {{ selectedReports.length }} 份报告</div>
          <div class="modal-footer-actions">
            <button class="modal-btn cancel" @click="showReportModal = false">取消</button>
            <button
              class="modal-btn confirm"
              :disabled="selectedReports.length === 0 || reportContentLoading"
              @click="confirmLoadReports"
            >
              {{ reportContentLoading ? '加载中...' : '✅ 确认加载并分析' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'
import axios from 'axios'

export default {
  name: 'Analysis',
  components: { Sidebar },
  data() {
    return {
      inputMessage: '',
      isTyping: false,
      typingStage: '',
      messages: [],
      apiOnline: false,
      apiModel: '',
      chatHistory: [],

      // 常见问题展开/收起
      showSuggestions: true,

      // 报告
      showReportModal: false,
      reportList: [],
      reportListLoading: false,
      selectedReports: [],
      reportContentLoading: false,
      loadedReports: [],

      // 论文佐证
      enableEvidence: true,

      // 独立论文搜索
      showPaperSearch: false,
      paperSearchQuery: '',
      paperSearching: false,

      quickSuggestions: [
        { id: 1, icon: '📊', text: '分析我的实验数据，给出优化建议' },
        { id: 2, icon: '🌡️', text: '衬底温度185°C对HgCdTe生长有什么影响？' },
        { id: 3, icon: '⚗️', text: 'Hg/Te通量比如何影响组分均匀性？' },
        { id: 4, icon: '🔬', text: 'RHEED图案如何判断生长模式？' },
        { id: 5, icon: '⚠️', text: 'Hg空位缺陷如何抑制？' },
        { id: 6, icon: '📈', text: '如何提高长波HgCdTe的截止波长精度？' }
      ]
    }
  },
  mounted() {
    this.adjustTextareaHeight()
    this.checkApiHealth()
    // 手机端默认收起常见问题
    if (window.innerWidth <= 768) {
      this.showSuggestions = false
    }
  },
  methods: {
    getCurrentTime() {
      return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    },

    async checkApiHealth() {
      try {
        const { data } = await axios.get('/api/ai/health')
        this.apiOnline = data.status === 'ok'
        this.apiModel = data.model || 'DeepSeek'
      } catch {
        this.apiOnline = false
      }
    },

    toggleEvidence() {
      this.enableEvidence = !this.enableEvidence
    },

    getSourceClass(source) {
      if (source === 'arXiv') return 'arxiv'
      if (source === 'Semantic Scholar') return 'semantic'
      if (source === 'CrossRef') return 'crossref'
      return 'generic'
    },

    sendMessage() {
      if (!this.inputMessage.trim() || this.isTyping) return

      const userText = this.inputMessage.trim()
      this.messages.push({
        type: 'user',
        content: userText,
        time: this.getCurrentTime()
      })

      this.chatHistory.push({ role: 'user', content: userText })
      this.inputMessage = ''
      this.adjustTextareaHeight()
      this.callAI()
      this.$nextTick(() => { this.scrollToBottom() })
    },

    sendQuickMessage(text) {
      this.inputMessage = text
      this.sendMessage()
    },

    async callAI() {
      this.isTyping = true
      this.typingStage = ''

      try {
        let aiText = ''
        let papers = []
        let searchKeywords = []
        let evidenceStatus = 'disabled'

        if (this.enableEvidence) {
          this.typingStage = '🤔 AI 分析中...'
          await this.sleep(500)
          this.typingStage = '🔍 正在检索 arXiv / Semantic Scholar 论文...'

          const { data } = await axios.post('/api/ai/chat-with-evidence', {
            messages: this.chatHistory,
            enable_evidence: true,
            max_papers: 5
          })

          aiText = data.response
          papers = data.papers || []
          searchKeywords = data.search_keywords || []
          evidenceStatus = data.evidence_status || 'success'

        } else {
          this.typingStage = '🤔 AI 分析中...'

          const { data } = await axios.post('/api/ai/chat', {
            messages: this.chatHistory,
            stream: false
          })

          aiText = data.response
          evidenceStatus = 'disabled'
        }

        this.chatHistory.push({ role: 'assistant', content: aiText })

        const formatted = this.formatMarkdown(aiText)

        this.messages.push({
          type: 'ai',
          content: formatted,
          time: this.getCurrentTime(),
          papers: papers,
          searchKeywords: searchKeywords,
          evidenceStatus: evidenceStatus,
          showPapers: papers.length > 0
        })

      } catch (err) {
        const detail = err.response?.data?.detail || err.message || '未知错误'
        this.messages.push({
          type: 'ai',
          content: `⚠️ 请求失败：${detail}<br><br>请检查：<br>• 后端是否已启动<br>• DEEPSEEK_API_KEY 是否已配置<br>• 网络是否正常（论文检索需要外网）`,
          time: this.getCurrentTime(),
          papers: [],
          evidenceStatus: 'error',
          showPapers: false
        })
      } finally {
        this.isTyping = false
        this.typingStage = ''
        this.$nextTick(() => { this.scrollToBottom() })
      }
    },

    async doManualPaperSearch() {
      if (!this.paperSearchQuery.trim() || this.paperSearching) return

      this.paperSearching = true
      try {
        const { data } = await axios.post('/api/ai/search-papers', {
          query: this.paperSearchQuery.trim(),
          max_results: 5,
          sources: ['arxiv', 'semantic_scholar']
        })

        const papers = data.papers || []

        let content = `🔍 手动搜索论文：<strong>"${this.paperSearchQuery}"</strong><br>`
        if (papers.length === 0) {
          content += '<br>❌ 未找到相关论文，请尝试更换关键词（建议使用英文）。'
        } else {
          content += `<br>✅ 找到 ${papers.length} 篇相关论文（见下方卡片）`
        }

        this.messages.push({
          type: 'ai',
          content: content,
          time: this.getCurrentTime(),
          papers: papers,
          searchKeywords: [this.paperSearchQuery],
          evidenceStatus: papers.length > 0 ? 'success' : 'no_papers_found',
          showPapers: true
        })

        this.paperSearchQuery = ''
        this.$nextTick(() => { this.scrollToBottom() })

      } catch (err) {
        this.messages.push({
          type: 'ai',
          content: `⚠️ 论文搜索失败：${err.message}`,
          time: this.getCurrentTime(),
          papers: [],
          evidenceStatus: 'error',
          showPapers: false
        })
      } finally {
        this.paperSearching = false
      }
    },

    formatMarkdown(text) {
      return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
        .replace(/^### (.+)$/gm, '<h4 style="color:#00c7ff;margin:12px 0 6px;">$1</h4>')
        .replace(/^## (.+)$/gm, '<h3 style="color:#00c7ff;margin:14px 0 8px;">$1</h3>')
        .replace(/^# (.+)$/gm, '<h2 style="color:#00c7ff;margin:16px 0 10px;">$1</h2>')
        .replace(/\n/g, '<br>')
    },

    async openReportModal() {
      this.showReportModal = true
      this.selectedReports = []
      this.reportListLoading = true
      try {
        const { data } = await axios.get('/api/ai/reports')
        this.reportList = data
      } catch {
        this.reportList = []
      } finally {
        this.reportListLoading = false
      }
    },

    toggleReportSelect(name) {
      const idx = this.selectedReports.indexOf(name)
      if (idx >= 0) this.selectedReports.splice(idx, 1)
      else this.selectedReports.push(name)
    },

    async confirmLoadReports() {
      this.reportContentLoading = true

      try {
        const newReports = []
        for (const name of this.selectedReports) {
          if (this.loadedReports.find(r => r.name === name)) continue
          const { data } = await axios.get(`/api/ai/reports/${encodeURIComponent(name)}`)
          newReports.push({ name: data.filename, content: data.content })
        }

        if (newReports.length === 0) {
          this.showReportModal = false
          this.reportContentLoading = false
          return
        }

        this.loadedReports.push(...newReports)

        const reportNames = newReports.map(r => r.name).join('、')
        const reportTexts = newReports.map(r => `══════ ${r.name} ══════\n${r.content}`).join('\n\n')

        const injectedContent =
          `以下是用户加载的实验报告数据，请基于这些数据进行专业分析：\n\n${reportTexts}\n\n` +
          `请你：\n1. 概括每份报告的关键工艺参数\n2. 评估参数是否在最优工艺窗口内\n` +
          `3. 指出潜在的问题或改进方向\n4. 如果有多份报告，进行对比分析`

        const displayMsg = `📂 已加载 ${newReports.length} 份实验报告：${reportNames}，请帮我分析。`
        this.messages.push({ type: 'user', content: displayMsg, time: this.getCurrentTime() })
        this.chatHistory.push({ role: 'user', content: injectedContent })

        this.showReportModal = false
        this.callAI()

      } catch (err) {
        console.error('加载报告失败', err)
        this.messages.push({
          type: 'ai',
          content: '⚠️ 加载报告失败，请检查后端服务。',
          time: this.getCurrentTime(),
          papers: [],
          showPapers: false
        })
      } finally {
        this.reportContentLoading = false
      }
    },

    removeReport(idx) {
      this.loadedReports.splice(idx, 1)
    },

    handleKeyDown(e) {
      if (e.key === 'Enter') {
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault()
          this.sendMessage()
        } else if (!e.shiftKey) {
          e.preventDefault()
          this.sendMessage()
        }
      }
    },

    adjustTextareaHeight() {
      this.$nextTick(() => {
        const textarea = this.$refs.messageInput
        if (textarea) {
          textarea.style.height = 'auto'
          textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
        }
      })
    },

    scrollToBottom() {
      const container = this.$refs.messagesContainer
      if (container) container.scrollTop = container.scrollHeight
    },

    sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms))
    }
  }
}
</script>

<style scoped>
/* ━━━ 基础布局 ━━━ */
.layout {
  display: flex;
  min-height: 100vh;
  background-color: #05050a;
  color: white;
}

.main-content {
  margin-left: var(--sidebar-width);
  flex: 1;
  padding: 25px;
  overflow: hidden;
  transition: margin-left 0.3s ease;
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 70px;
    padding: 15px;
  }
}

.analysis-wrapper {
  max-width: 1000px;
  margin: 0 auto;
  height: calc(100vh - 50px);
  display: flex;
  flex-direction: column;
}

.page-title {
  text-align: center;
  font-size: 32px;
  background: linear-gradient(135deg, #00c7ff 0%, #0099cc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 25px;
  letter-spacing: 2px;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(10, 10, 20, 0.8);
  border: 1px solid #1e1e35;
  border-radius: 12px;
  overflow: hidden;
}

/* ━━━ 消息区域 ━━━ */
.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  scroll-behavior: smooth;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 199, 255, 0.3);
  border-radius: 3px;
}

.welcome-message,
.message-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.user-message-item {
  flex-direction: row-reverse;
}

.ai-avatar,
.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.ai-avatar {
  background: linear-gradient(135deg, #00c7ff 0%, #0099cc 100%);
}

.user-avatar {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
}

.message-content {
  max-width: 78%;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.user-message-item .message-content {
  align-items: flex-end;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 18px;
  line-height: 1.7;
  word-wrap: break-word;
  font-size: 14px;
}

.ai-message {
  background: rgba(0, 199, 255, 0.08);
  border: 1px solid rgba(0, 199, 255, 0.15);
  color: #e8f4f8;
}

.user-message {
  background: rgba(255, 107, 107, 0.08);
  border: 1px solid rgba(255, 107, 107, 0.15);
  color: #ffe8e8;
}

.message-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  padding: 0 8px;
}

/* 正在输入 */
.typing-indicator {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00c7ff;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.typing-label {
  font-size: 12px;
  color: rgba(0, 199, 255, 0.8);
  white-space: nowrap;
}

/* ━━━ 佐证状态条 ━━━ */
.evidence-status-bar {
  padding: 4px 12px;
  font-size: 11px;
  border-radius: 6px;
}

.status-success {
  color: #81c784;
}

.status-warning {
  color: #ffb74d;
}

.status-disabled {
  color: rgba(255, 255, 255, 0.3);
}

/* ━━━ 论文佐证卡片 ━━━ */
.papers-section {
  margin-top: 10px;
  border: 1px solid rgba(76, 175, 80, 0.35);
  border-radius: 14px;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.05), rgba(56, 142, 60, 0.03));
  box-shadow: 0 2px 12px rgba(76, 175, 80, 0.08);
}

.papers-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  user-select: none;
  background: rgba(76, 175, 80, 0.08);
  border-bottom: 1px solid rgba(76, 175, 80, 0.15);
}

.papers-header:hover {
  background: rgba(76, 175, 80, 0.12);
}

.papers-toggle {
  font-size: 10px;
  color: #81c784;
  transition: transform 0.2s;
}

.papers-title {
  font-size: 14px;
  font-weight: 600;
  color: #81c784;
}

.papers-badge {
  margin-left: auto;
  font-size: 10px;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.4);
}

.papers-list {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.paper-card {
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  transition: all 0.2s;
}

.paper-card:hover {
  border-color: rgba(76, 175, 80, 0.35);
  background: rgba(76, 175, 80, 0.04);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.paper-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.paper-source-badge {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.paper-source-badge.arxiv {
  background: rgba(180, 30, 30, 0.2);
  color: #ef9a9a;
  border: 1px solid rgba(180, 30, 30, 0.3);
}

.paper-source-badge.semantic {
  background: rgba(33, 150, 243, 0.2);
  color: #90caf9;
  border: 1px solid rgba(33, 150, 243, 0.3);
}

.paper-source-badge.crossref {
  background: rgba(255, 152, 0, 0.2);
  color: #ffcc80;
  border: 1px solid rgba(255, 152, 0, 0.3);
}

.paper-source-badge.generic {
  background: rgba(158, 158, 158, 0.2);
  color: #bdbdbd;
  border: 1px solid rgba(158, 158, 158, 0.3);
}

.paper-relevance-tag {
  font-size: 10px;
  padding: 2px 8px;
  background: rgba(0, 199, 255, 0.1);
  border: 1px solid rgba(0, 199, 255, 0.2);
  border-radius: 8px;
  color: rgba(0, 199, 255, 0.8);
}

.paper-title {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.5;
  margin-bottom: 6px;
}

.paper-title a {
  color: #e0e0e0;
  text-decoration: none;
  transition: color 0.2s;
}

.paper-title a:hover {
  color: #81c784;
  text-decoration: underline;
}

.paper-authors {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 8px;
}

.paper-abstract {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  line-height: 1.5;
  margin-bottom: 8px;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  border-left: 3px solid rgba(76, 175, 80, 0.3);
}

.abstract-label {
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
}

.paper-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 3px;
}

.meta-item.citations {
  color: #ffb74d;
  font-weight: 500;
}

.paper-link {
  color: #81c784;
  text-decoration: none;
  margin-left: auto;
  transition: color 0.2s;
}

.paper-link:hover {
  color: #a5d6a7;
  text-decoration: underline;
}

/* ━━━ 快捷建议（可收起） ━━━ */
.quick-suggestions {
  padding: 12px 20px;
  border-top: 1px solid #1e1e35;
}

.suggestions-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: 4px 0;
  user-select: none;
  transition: opacity 0.2s;
}

.suggestions-header:active {
  opacity: 0.7;
}

.suggestions-header h3 {
  margin: 0;
  font-size: 16px;
  color: #00c7ff;
}

.suggestions-toggle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  transition: color 0.2s;
  padding: 4px 8px;
  border-radius: 4px;
}

.suggestions-header:hover .suggestions-toggle {
  color: #00c7ff;
  background: rgba(0, 199, 255, 0.1);
}

.suggestion-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.suggestion-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 15px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #ccc;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  text-align: left;
}

.suggestion-btn:hover {
  background: rgba(0, 199, 255, 0.1);
  border-color: rgba(0, 199, 255, 0.3);
  color: #00c7ff;
  transform: translateY(-1px);
}

/* 收起/展开动画 */
.suggestions-slide-enter-active,
.suggestions-slide-leave-active {
  transition: all 0.3s ease;
  max-height: 400px;
  overflow: hidden;
}

.suggestions-slide-enter-from,
.suggestions-slide-leave-to {
  max-height: 0;
  opacity: 0;
  margin-top: 0;
}

/* ━━━ 工具栏 ━━━ */
.report-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 20px;
  border-top: 1px solid #1e1e35;
  background: rgba(0, 0, 0, 0.2);
  flex-wrap: wrap;
}

.loaded-reports {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
}

.loaded-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  white-space: nowrap;
}

.report-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(0, 199, 255, 0.15);
  border: 1px solid rgba(0, 199, 255, 0.3);
  border-radius: 20px;
  font-size: 11px;
  color: #7dd3fc;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-remove {
  cursor: pointer;
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}

.tag-remove:hover {
  color: #ff6b6b;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.load-report-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(0, 199, 255, 0.2), rgba(0, 153, 204, 0.2));
  border: 1px solid rgba(0, 199, 255, 0.4);
  border-radius: 8px;
  color: #00c7ff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.load-report-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0, 199, 255, 0.3), rgba(0, 153, 204, 0.3));
  border-color: rgba(0, 199, 255, 0.6);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 199, 255, 0.2);
}

.load-report-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.evidence-toggle-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.evidence-toggle-btn.active {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.15), rgba(56, 142, 60, 0.15));
  border-color: rgba(76, 175, 80, 0.5);
  color: #81c784;
  box-shadow: 0 0 12px rgba(76, 175, 80, 0.15);
}

.evidence-toggle-btn:hover {
  transform: translateY(-1px);
}

.toggle-indicator {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.4);
}

.toggle-indicator.on {
  background: rgba(76, 175, 80, 0.3);
  color: #81c784;
}

.search-paper-btn {
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.search-paper-btn:hover {
  border-color: rgba(255, 152, 0, 0.4);
  color: #ffb74d;
  transform: translateY(-1px);
}

/* ━━━ 独立论文搜索栏 ━━━ */
.paper-search-bar {
  display: flex;
  gap: 10px;
  padding: 10px 20px;
  border-top: 1px solid #1e1e35;
  background: rgba(255, 152, 0, 0.03);
}

.paper-search-input {
  flex: 1;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 152, 0, 0.3);
  border-radius: 8px;
  color: white;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.paper-search-input:focus {
  border-color: rgba(255, 152, 0, 0.6);
}

.paper-search-input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.paper-search-submit {
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.2), rgba(255, 111, 0, 0.2));
  border: 1px solid rgba(255, 152, 0, 0.4);
  border-radius: 8px;
  color: #ffb74d;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.paper-search-submit:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.3), rgba(255, 111, 0, 0.3));
  transform: translateY(-1px);
}

.paper-search-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ━━━ 输入区域 ━━━ */
.chat-input-area {
  border-top: 1px solid #1e1e35;
  background: rgba(0, 0, 0, 0.3);
}

.input-container {
  padding: 15px 20px;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px 16px;
  color: white;
  font-size: 14px;
  line-height: 1.4;
  resize: none;
  outline: none;
  transition: all 0.2s;
  font-family: inherit;
  min-height: 20px;
  max-height: 120px;
}

.message-input:focus {
  border-color: rgba(0, 199, 255, 0.5);
  box-shadow: 0 0 0 2px rgba(0, 199, 255, 0.1);
}

.message-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.message-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.input-actions {
  display: flex;
  align-items: flex-end;
}

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-size: 16px;
}

.send-btn:hover:not(:disabled) {
  background: rgba(0, 199, 255, 0.2);
  color: #00c7ff;
  transform: scale(1.05);
}

.send-btn.active {
  background: #00c7ff;
  color: white;
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.input-footer {
  padding: 8px 20px 15px;
}

.input-tips {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.model-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot.offline {
  background: #ff6b6b;
  box-shadow: 0 0 6px rgba(255, 107, 107, 0.5);
}

.status-dot.online {
  background: #51cf66;
  box-shadow: 0 0 6px rgba(81, 207, 102, 0.5);
}

/* ━━━ 弹窗 ━━━ */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 560px;
  max-width: 90vw;
  max-height: 80vh;
  background: #0d0d1a;
  border: 1px solid #2a2a4a;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #1e1e35;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #00c7ff;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.modal-close:hover {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.modal-loading,
.modal-empty {
  text-align: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.5);
}

.modal-loading .typing-dots {
  justify-content: center;
  margin-bottom: 16px;
  display: flex;
}

.modal-hint {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.3);
  margin-top: 8px;
}

.report-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.report-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.report-item:hover {
  background: rgba(0, 199, 255, 0.05);
  border-color: rgba(0, 199, 255, 0.2);
}

.report-item.selected {
  background: rgba(0, 199, 255, 0.1);
  border-color: rgba(0, 199, 255, 0.4);
}

.report-checkbox {
  font-size: 18px;
  color: #00c7ff;
  flex-shrink: 0;
}

.report-info {
  flex: 1;
  overflow: hidden;
}

.report-name {
  font-size: 14px;
  color: #e0e0e0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.report-meta {
  display: flex;
  gap: 16px;
  margin-top: 4px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid #1e1e35;
}

.modal-footer-info {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.modal-footer-actions {
  display: flex;
  gap: 10px;
}

.modal-btn {
  padding: 8px 20px;
  border-radius: 8px;
  border: none;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-btn.cancel {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
}

.modal-btn.cancel:hover {
  background: rgba(255, 255, 255, 0.15);
}

.modal-btn.confirm {
  background: linear-gradient(135deg, #00c7ff, #0099cc);
  color: white;
  font-weight: 600;
}

.modal-btn.confirm:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(0, 199, 255, 0.4);
  transform: translateY(-1px);
}

.modal-btn.confirm:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ━━━ 响应式 ━━━ */
@media (max-width: 768px) {
  .page-title {
    font-size: 22px;
    margin-bottom: 12px;
  }

  .message-content {
    max-width: 92%;
  }

  .quick-suggestions {
    padding: 10px 16px;
  }

  .suggestions-header h3 {
    font-size: 14px;
  }

  .suggestion-buttons {
    grid-template-columns: 1fr;
    gap: 8px;
    margin-top: 10px;
    max-height: 200px;
    overflow-y: auto;
  }

  .suggestion-btn {
    padding: 8px 12px;
    font-size: 12px;
  }

  .input-tips {
    flex-direction: column;
    gap: 5px;
    align-items: flex-start;
  }

  .report-toolbar {
    flex-direction: column;
    align-items: stretch;
    padding: 10px 12px;
    gap: 8px;
  }

  .toolbar-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
    gap: 8px;
  }

  .load-report-btn,
  .evidence-toggle-btn,
  .search-paper-btn {
    padding: 6px 10px;
    font-size: 12px;
  }

  .modal-content {
    width: 95vw;
    max-height: 85vh;
  }

  .papers-badge {
    display: none;
  }

  .paper-search-bar {
    flex-direction: column;
    padding: 10px 12px;
  }

  .chat-messages {
    padding: 12px;
    gap: 14px;
  }

  .input-container {
    padding: 10px 12px;
  }

  .input-footer {
    padding: 6px 12px 10px;
  }
}
</style>