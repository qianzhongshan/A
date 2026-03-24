<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
    <!-- Header -->
    <header class="bg-white shadow-sm">
      <div class="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-gray-800">MBTI 深度测试</h1>
        <div class="flex items-center gap-4">
          <span class="text-sm text-gray-600">
            进度: {{ progressPercent }}% ({{ answeredCount }}/{{ totalQuestions }})
          </span>
          <button
            v-if="isAdminMode"
            @click="goToAdmin"
            class="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded"
          >
            管理面板
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-8">
      <!-- 欢迎页 -->
      <div v-if="!started" class="bg-white rounded-lg shadow-lg p-8 text-center">
        <h2 class="text-2xl font-bold mb-4">欢迎参加MBTI深度测试</h2>
        <div class="mb-6 text-gray-600 space-y-2">
          <p>本测试包含 <strong>93 道论述题</strong></p>
          <p>你需要详细描述你的想法、感受和行为</p>
          <p>预计完成时间：<strong>60-90分钟</strong></p>
          <p class="text-sm text-amber-600 mt-4">
            ⚠️ 请确保有足够的时间，可以随时保存进度
          </p>
        </div>
        <div class="flex gap-4 justify-center">
          <button
            @click="startTest"
            class="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-8 rounded-lg transition"
          >
            开始测试
          </button>
          <button
            v-if="hasSavedProgress"
            @click="continueTest"
            class="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-8 rounded-lg transition"
          >
            继续上次进度
          </button>
        </div>
      </div>

      <!-- 答题页 -->
      <div v-else-if="!completed" class="bg-white rounded-lg shadow-lg p-6">
        <!-- 进度条 -->
        <div class="mb-6">
          <div class="flex justify-between text-sm text-gray-600 mb-2">
            <span>题目 {{ currentQuestionIndex + 1 }} / {{ totalQuestions }}</span>
            <span>{{ progressPercent }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div
              class="bg-indigo-600 h-2 rounded-full transition-all"
              :style="{ width: progressPercent + '%' }"
            ></div>
          </div>
        </div>

        <!-- 题目卡片 -->
        <div class="mb-6">
          <h3 class="text-lg font-semibold mb-4 text-gray-800">
            {{ currentQuestion?.open_ended }}
          </h3>
          <div class="text-sm text-gray-500 mb-4">
            考察维度：{{ currentQuestion?.dimension }} | {{ currentQuestion?.sub_aspect }}
          </div>
          <textarea
            v-model="currentAnswer"
            placeholder="请详细描述你的想法、经历和感受...（建议200字以上）"
            class="w-full h-64 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
          ></textarea>
          <div class="text-right text-sm text-gray-500 mt-1">
            {{ currentAnswer.length }} 字
          </div>
        </div>

        <!-- 导航按钮 -->
        <div class="flex justify-between items-center">
          <button
            v-if="currentQuestionIndex > 0"
            @click="prevQuestion"
            class="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            上一题
          </button>
          <div v-else></div>

          <div class="flex gap-3">
            <button
              @click="saveAndExit"
              class="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
            >
              保存并退出
            </button>
            <button
              v-if="!isLastQuestion"
              @click="nextQuestion"
              :disabled="!currentAnswer.trim()"
              class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              下一题
            </button>
            <button
              v-else
              @click="submitAll"
              :disabled="!canSubmit"
              class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              提交并评估
            </button>
          </div>
        </div>
      </div>

      <!-- 评估中 -->
      <div v-else-if="evaluating" class="bg-white rounded-lg shadow-lg p-12 text-center">
        <div class="mb-4">
          <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
        <h3 class="text-xl font-semibold mb-2">正在分析你的答案...</h3>
        <p class="text-gray-600">
          这可能需要几分钟时间，取决于当前负载
          <br>
          <span class="text-sm">已评估 {{ evaluatedCount }} / {{ totalQuestions }} 题</span>
        </p>
        <div class="mt-6 max-w-md mx-auto">
          <div class="w-full bg-gray-200 rounded-full h-3">
            <div
              class="bg-indigo-600 h-3 rounded-full transition-all"
              :style="{ width: (evaluatedCount / totalQuestions * 100) + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- 结果页 -->
      <div v-else-if="completed && results" class="space-y-6">
        <!-- 结果摘要卡片 -->
        <div class="bg-white rounded-lg shadow-lg p-8 text-center">
          <h2 class="text-3xl font-bold mb-2">你的MBTI类型是</h2>
          <div class="text-6xl font-bold text-indigo-600 mb-6">
            {{ results.mbti_type }}
          </div>
          <div class="grid grid-cols-2 gap-4 mb-6">
            <div v-for="(score, dim) in results.dimension_scores" :key="dim" class="bg-gray-50 p-4 rounded">
              <div class="text-sm text-gray-600">{{ getDimensionName(dim) }}</div>
              <div class="text-2xl font-bold text-gray-800">{{ score.toFixed(1) }}</div>
              <div class="text-xs text-gray-500 mt-1">
                {{ getDimensionAnchor(dim, score) }}
              </div>
            </div>
          </div>
          <button
            @click="shareResults"
            class="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-8 rounded-lg transition"
          >
            分享结果
          </button>
        </div>

        <!-- 详细报告 -->
        <div class="bg-white rounded-lg shadow-lg p-8">
          <h3 class="text-xl font-bold mb-4">📋 详细分析报告</h3>

          <!-- 人格概览 -->
          <div class="mb-6">
            <h4 class="font-semibold text-lg mb-2">整体性格特征</h4>
            <p class="text-gray-700 leading-relaxed">
              {{ results.report?.personality_summary || '暂无数据' }}
            </p>
          </div>

          <!-- 分维度分析 -->
          <div class="mb-6 space-y-4">
            <h4 class="font-semibold text-lg">各维度分析</h4>
            <div v-for="(analysis, dim) in results.report?.dimension_analysis || {}" :key="dim" class="border-l-4 border-indigo-500 pl-4 py-2">
              <div class="font-medium text-gray-800">{{ getDimensionName(dim) }}</div>
              <div class="text-gray-600">{{ analysis }}</div>
            </div>
          </div>

          <!-- 注意事项 -->
          <div v-if="results.report?.caveats" class="mb-6 bg-yellow-50 border border-yellow-200 rounded p-4">
            <h4 class="font-semibold text-yellow-800 mb-2">⚠️ 注意事项</h4>
            <p class="text-yellow-700 text-sm">{{ results.report.caveats }}</p>
          </div>

          <!-- 建议 -->
          <div v-if="results.report?.recommendations" class="bg-blue-50 border border-blue-200 rounded p-4">
            <h4 class="font-semibold text-blue-800 mb-2">💡 建议</h4>
            <p class="text-blue-700 text-sm">{{ results.report.recommendations }}</p>
          </div>

          <!-- 原始数据 -->
          <div class="mt-8 pt-6 border-t">
            <button
              @click="showRawData = !showRawData"
              class="text-sm text-gray-500 hover:text-gray-700"
            >
              {{ showRawData ? '隐藏' : '显示' }}原始评估数据
            </button>
            <div v-if="showRawData" class="mt-4 bg-gray-50 p-4 rounded overflow-auto max-h-96">
              <pre class="text-xs text-gray-600">{{ JSON.stringify(results, null, 2) }}</pre>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex justify-center gap-4">
          <button
            @click="restart"
            class="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            重新测试
          </button>
          <button
            @click="downloadResults"
            class="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            下载报告
          </button>
        </div>
      </div>
    </main>

    <!-- 提示消息 -->
    <div v-if="message" class="fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded shadow-lg">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'pinia'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const router = useRouter()
const store = useStore()

// 响应式数据
const started = ref(false)
const completed = ref(false)
const evaluating = ref(false)
const currentQuestionIndex = ref(0)
const answers = ref({})
const results = ref(null)
const message = ref('')
const showRawData = ref(false)
const isAdminMode = ref(false)

// 计算属性
const totalQuestions = ref(93)
const questions = ref([])

const answeredCount = computed(() => Object.keys(answers.value).length)
const progressPercent = computed(() => Math.round((answeredCount.value / totalQuestions.value) * 100))
const currentQuestion = computed(() => questions.value[currentQuestionIndex.value])
const currentAnswer = computed({
  get: () => answers.value[currentQuestion.value?.id] || '',
  set: (val) => {
    answers.value[currentQuestion.value.id] = val
  }
})
const isLastQuestion = computed(() => currentQuestionIndex.value >= totalQuestions.value - 1)
const canSubmit = computed(() => answeredCount.value === totalQuestions.value)
const hasSavedProgress = computed(() => Object.keys(answers.value).length > 0)
const evaluatedCount = computed(() => {
  if (!results.value?.assessments) return 0
  return results.value.assessments.length
})

// 方法
async function startTest() {
  try {
    const res = await axios.get(`${API_BASE}/questions?offset=0&limit=93`)
    questions.value = res.data.questions
    started.value = true
    saveProgress()
  } catch (err) {
    showMessage('加载题目失败: ' + err.message)
  }
}

function continueTest() {
  started.value = true
  // 恢复进度到第一个未答题目
  for (let i = 0; i < questions.value.length; i++) {
    const qid = questions.value[i].id
    if (!answers.value[qid]) {
      currentQuestionIndex.value = i
      break
    }
  }
}

function nextQuestion() {
  if (currentQuestionIndex.value < totalQuestions.value - 1) {
    currentQuestionIndex.value++
    saveProgress()
  }
}

function prevQuestion() {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
  }
}

async function submitAll() {
  if (!canSubmit.value) return

  evaluating.value = true
  try {
    // 创建或获取会话
    const sessionRes = await axios.post(`${API_BASE}/session/start`)
    const sessionId = sessionRes.data.session_id

    // 提交所有答案
    for (const [qid, answer] of Object.entries(answers.value)) {
      await axios.post(`${API_BASE}/session/${sessionId}/answer`, {
        question_id: qid,
        answer: answer
      })
    }

    // 触发评估
    const evalRes = await axios.post(`${API_BASE}/session/${sessionId}/evaluate`)
    results.value = evalRes.data
    completed.value = true
    evaluating.value = false

    // 清理本地存储的答案（已上传）
    localStorage.removeItem('mbti_answers')
  } catch (err) {
    evaluating.value = false
    showMessage('评估失败: ' + (err.response?.data?.detail || err.message))
  }
}

function saveAndExit() {
  saveProgress()
  showMessage('进度已保存，可以随时回来继续')
  setTimeout(() => window.close(), 1000)
}

function saveProgress() {
  localStorage.setItem('mbti_answers', JSON.stringify(answers.value))
}

function loadProgress() {
  const saved = localStorage.getItem('mbti_answers')
  if (saved) {
    try {
      answers.value = JSON.parse(saved)
      return true
    } catch (e) {
      return false
    }
  }
  return false
}

function goToAdmin() {
  router.push('/admin')
}

function shareResults() {
  const text = `我的MBTI类型是 ${results.value.mbti_type}！基于93道论述题的深度分析，快来试试吧！`
  if (navigator.share) {
    navigator.share({
      title: '我的MBTI测试结果',
      text: text
    })
  } else {
    navigator.clipboard.writeText(text).then(() => {
      showMessage('结果已复制到剪贴板')
    })
  }
}

function downloadResults() {
  const data = {
    ...results.value,
    timestamp: new Date().toISOString()
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `mbti-results-${results.value.mbti_type}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function restart() {
  if (confirm('确定要重新开始测试吗？当前结果将丢失。')) {
    started.value = false
    completed.value = false
    results.value = null
    currentQuestionIndex.value = 0
    answers.value = {}
    localStorage.removeItem('mbti_answers')
  }
}

function getDimensionName(dim) {
  const names = {
    EI: '外向(E) / 内向(I)',
    SN: '实感(S) / 直觉(N)',
    TF: '思考(T) / 情感(F)',
    JP: '判断(J) / 感知(P)'
  }
  return names[dim] || dim
}

function getDimensionAnchor(dim, score) {
  if (score < 4) return getLeftAnchor(dim)
  if (score > 6) return getRightAnchor(dim)
  return '中间倾向'
}

function getLeftAnchor(dim) {
  const anchors = {
    EI: '外向(E)',
    SN: '实感(S)',
    TF: '思考(T)',
    JP: '判断(J)'
  }
  return anchors[dim]
}

function getRightAnchor(dim) {
  const anchors = {
    EI: '内向(I)',
    SN: '直觉(N)',
    TF: '情感(F)',
    JP: '感知(P)'
  }
  return anchors[dim]
}

function showMessage(msg) {
  message.value = msg
  setTimeout(() => {
    message.value = ''
  }, 3000)
}

onMounted(async () => {
  try {
    // 加载题目
    const res = await axios.get(`${API_BASE}/questions?offset=0&limit=93`)
    questions.value = res.data.questions
    totalQuestions.value = questions.value.length

    // 加载进度
    if (loadProgress()) {
      hasSavedProgress.value = true
    }
  } catch (err) {
    showMessage('初始化失败: ' + err.message)
  }
})
</script>
