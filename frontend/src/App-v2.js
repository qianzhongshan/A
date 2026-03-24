import { ref, computed, onMounted } from 'vue'
import MBTIEvaluator from './evaluator.js'
import questionsData from '../mbti_93_questions.json'

const API_BASE = import.meta.env.VITE_API_BASE || ''

const router = useRouter()

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
const showApiSettings = ref(false)
const apiKey = ref(localStorage.getItem('openai_api_key') || '')
const apiBase = ref(localStorage.getItem('openai_api_base') || 'https://api.deepseek.com')
const apiModel = ref(localStorage.getItem('openai_api_model') || 'deepseek-chat')
const evaluator = ref(null)

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
  questions.value = questionsData.questions
  started.value = true
  saveProgress()
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

  // 检查API密钥
  if (!apiKey.value) {
    showMessage('请先配置API密钥')
    showApiSettings.value = true
    return
  }

  evaluating.value = true
  try {
    // 初始化评估器
    evaluator.value = new MBTIEvaluator()
    evaluator.value.apiKey = apiKey.value
    evaluator.value.baseUrl = apiBase.value
    evaluator.value.model = apiModel.value

    // 保存API设置
    localStorage.setItem('openai_api_key', apiKey.value)
    localStorage.setItem('openai_api_base', apiBase.value)
    localStorage.setItem('openai_api_model', apiModel.value)

    // 评估所有题目
    const assessments = []
    for (const question of questions.value) {
      const answer = answers.value[question.id]
      if (answer) {
        const assessment = await evaluator.value.evaluateSingleQuestion(question, answer)
        assessments.push(assessment)
      }
    }

    // 计算维度得分
    const dimensionData = { EI: [], SN: [], TF: [], JP: [] }
    assessments.forEach(a => {
      if (dimensionData[a.dimension]) {
        dimensionData[a.dimension].push([a.score, a.confidence])
      }
    })

    const dimensionScores = {}
    ;['EI', 'SN', 'TF', 'JP'].forEach(dim => {
      const scores = dimensionData[dim]
      if (scores.length > 0) {
        const weightedSum = scores.reduce((sum, [s, c]) => sum + s * c, 0)
        const totalWeight = scores.reduce((sum, [, c]) => sum + c, 0)
        dimensionScores[dim] = totalWeight > 0 ? weightedSum / totalWeight : 5
      } else {
        dimensionScores[dim] = 5
      }
    })

    // 生成最终报告
    const report = await evaluator.value.generateFinalReport(assessments, dimensionScores)

    results.value = {
      mbti_type: evaluator.value.scoresToType(dimensionScores),
      dimension_scores: dimensionScores,
      assessments: assessments,
      report: report
    }

    completed.value = true
    evaluating.value = false

    // 清理本地存储的答案（已上传）
    localStorage.removeItem('mbti_answers')
  } catch (err) {
    evaluating.value = false
    console.error('评估失败:', err)
    showMessage('评估失败: ' + (err.message || '未知错误'))
  }
}

function saveAndExit() {
  saveProgress()
  showMessage('进度已保存，可以随时回来继续')
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
  // Admin functionality removed in static version
  showMessage('管理面板在此版本中不可用')
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

function saveApiSettings() {
  localStorage.setItem('openai_api_key', apiKey.value)
  localStorage.setItem('openai_api_base', apiBase.value)
  localStorage.setItem('openai_api_model', apiModel.value)
  showMessage('API设置已保存')
  showApiSettings.value = false
}

function showMessage(msg) {
  message.value = msg
  setTimeout(() => {
    message.value = ''
  }, 3000)
}

onMounted(async () => {
  // 加载题目
  questions.value = questionsData.questions
  totalQuestions.value = questions.value.length

  // 加载进度
  if (loadProgress()) {
    hasSavedProgress.value = true
  }

  // 加载API设置
  apiKey.value = localStorage.getItem('openai_api_key') || ''
  apiBase.value = localStorage.getItem('openai_api_base') || 'https://api.deepseek.com'
  apiModel.value = localStorage.getItem('openai_api_model') || 'deepseek-chat'
})