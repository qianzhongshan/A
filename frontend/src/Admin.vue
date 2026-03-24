<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-white shadow">
      <div class="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-gray-800">MBTI 系统管理</h1>
        <button
          @click="logout"
          class="text-sm text-gray-600 hover:text-gray-800"
        >
          退出
        </button>
      </div>
    </header>

    <main class="max-w-6xl mx-auto px-4 py-8">
      <!-- 控制面板 -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <h2 class="text-lg font-bold mb-4">系统控制</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="border rounded p-4">
            <div class="text-sm text-gray-600 mb-2">API状态</div>
            <div class="flex items-center gap-2">
              <span
                :class="apiEnabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                class="px-3 py-1 rounded-full text-sm font-medium"
              >
                {{ apiEnabled ? '运行中' : '已禁用' }}
              </span>
              <button
                @click="toggleApi"
                :class="apiEnabled ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'"
                class="text-white px-4 py-1 rounded text-sm transition"
              >
                {{ apiEnabled ? '禁用' : '启用' }}
              </button>
            </div>
          </div>

          <div class="border rounded p-4">
            <div class="text-sm text-gray-600 mb-2">今日会话数</div>
            <div class="text-3xl font-bold">{{ stats.today?.sessions || 0 }}</div>
          </div>

          <div class="border rounded p-4">
            <div class="text-sm text-gray-600 mb-2">今日API调用</div>
            <div class="text-3xl font-bold">{{ stats.today?.api_calls || 0 }}</div>
          </div>
        </div>
      </div>

      <!-- 配置面板 -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <h2 class="text-lg font-bold mb-4">系统配置</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="border rounded p-4">
            <div class="text-sm text-gray-600 mb-2">DeepSeek API Key</div>
            <input
              v-model="config.deepseek_api_key"
              @change="saveConfig('deepseek_api_key', config.deepseek_api_key)"
              type="password"
              placeholder="输入你的 DeepSeek API Key"
              class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div class="text-xs text-gray-500 mt-1">
              在 https://platform.deepseek.com 申请
            </div>
          </div>

          <div class="border rounded p-4">
            <div class="text-sm text-gray-600 mb-2">模型名称</div>
            <input
              v-model="config.deepseek_model"
              @change="saveConfig('deepseek_model', config.deepseek_model)"
              type="text"
              placeholder="如: deepseek-chat"
              class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div class="border rounded p-4">
            <div class="text-sm text-gray-600 mb-2">API 基础URL</div>
            <input
              v-model="config.deepseek_base_url"
              @change="saveConfig('deepseek_base_url', config.deepseek_base_url)"
              type="text"
              placeholder="https://api.deepseek.com"
              class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div class="border rounded p-4">
            <div class="text-sm text-gray-600 mb-2">每次调用成本(元)</div>
            <input
              v-model.number="config.cost_per_call"
              @change="saveConfig('cost_per_call', config.cost_per_call)"
              type="number"
              step="0.001"
              min="0"
              class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div class="border rounded p-4">
            <div class="text-sm text-gray-600 mb-2">每日API调用上限</div>
            <input
              v-model.number="config.daily_api_limit"
              @change="saveConfig('daily_api_limit', config.daily_api_limit)"
              type="number"
              min="1"
              class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div class="border rounded p-4">
            <div class="text-sm text-gray-600 mb-2">会话超时时间(小时)</div>
            <input
              v-model.number="config.session_timeout_hours"
              @change="saveConfig('session_timeout_hours', config.session_timeout_hours)"
              type="number"
              min="1"
              class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <!-- 统计面板 -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <h2 class="text-lg font-bold mb-4">数据统计</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="text-center p-4 bg-gray-50 rounded">
            <div class="text-2xl font-bold text-gray-800">{{ stats.total?.sessions || 0 }}</div>
            <div class="text-sm text-gray-600">总会话数</div>
          </div>
          <div class="text-center p-4 bg-green-50 rounded">
            <div class="text-2xl font-bold text-green-600">{{ stats.total?.completed || 0 }}</div>
            <div class="text-sm text-gray-600">已完成测试</div>
          </div>
          <div class="text-center p-4 bg-blue-50 rounded">
            <div class="text-2xl font-bold text-blue-600">{{ stats.total?.api_calls || 0 }}</div>
            <div class="text-sm text-gray-600">总API调用</div>
          </div>
          <div class="text-center p-4 bg-amber-50 rounded">
            <div class="text-2xl font-bold text-amber-600">¥{{ stats.total?.cost?.toFixed(2) || '0.00' }}</div>
            <div class="text-sm text-gray-600">预估成本</div>
          </div>
        </div>
      </div>

      <!-- 最近会话 -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-bold mb-4">最近会话</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-2 text-left">会话ID</th>
                <th class="px-4 py-2 text-left">创建时间</th>
                <th class="px-4 py-2 text-left">最后活跃</th>
                <th class="px-4 py-2 text-center">状态</th>
                <th class="px-4 py-2 text-right">答题数</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="session in recentSessions" :key="session.id" class="border-t">
                <td class="px-4 py-3 font-mono text-xs">{{ session.id.substring(0, 12) }}...</td>
                <td class="px-4 py-3">{{ formatDate(session.created_at) }}</td>
                <td class="px-4 py-3">{{ formatDate(session.last_active) }}</td>
                <td class="px-4 py-3 text-center">
                  <span
                    :class="session.completed ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'"
                    class="px-2 py-1 rounded-full text-xs"
                  >
                    {{ session.completed ? '已完成' : '进行中' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right">{{ session.answers_count }}</td>
              </tr>
              <tr v-if="recentSessions.length === 0">
                <td colspan="5" class="px-4 py-8 text-center text-gray-500">
                  暂无会话数据
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const stats = ref({ today: {}, total: {} })
const recentSessions = ref([])
const apiEnabled = ref(true)
const config = ref({
  deepseek_api_key: '',
  deepseek_base_url: 'https://api.deepseek.com',
  deepseek_model: 'deepseek-chat',
  cost_per_call: 0.001,
  daily_api_limit: 10000,
  session_timeout_hours: 24
})

async function fetchStats() {
  try {
    const res = await axios.get(`${API_BASE}/admin/stats`)
    stats.value = res.data
    recentSessions.value = res.data.recent_sessions
    apiEnabled.value = res.data.config?.api_enabled ?? true
  } catch (err) {
    console.error('Failed to fetch stats:', err)
  }
}

async function fetchConfig() {
  try {
    const res = await axios.get(`${API_BASE}/admin/config`)
    const cfg = res.data
    config.value = {
      deepseek_api_key: cfg.deepseek_api_key || '',
      deepseek_base_url: cfg.deepseek_base_url || 'https://api.deepseek.com',
      deepseek_model: cfg.deepseek_model || 'deepseek-chat',
      cost_per_call: cfg.cost_per_call ?? 0.001,
      daily_api_limit: cfg.daily_api_limit ?? 10000,
      session_timeout_hours: cfg.session_timeout_hours ?? 24
    }
  } catch (err) {
    console.error('Failed to fetch config:', err)
  }
}

async function saveConfig(key, value) {
  try {
    await axios.post(`${API_BASE}/admin/config`, {
      key,
      value,
      description: `Updated from admin panel`
    })
    // 如果更新的是API key或开关，立即刷新状态
    if (key === 'api_enabled') {
      apiEnabled.value = value
    }
  } catch (err) {
    alert('保存配置失败: ' + err.response?.data?.detail || err.message)
    // 回滚本地值
    fetchConfig()
  }
}

async function toggleApi() {
  await saveConfig('api_enabled', !apiEnabled.value)
}

function formatDate(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  return d.toLocaleString('zh-CN')
}

function logout() {
  localStorage.removeItem('admin_token')
  window.location.href = '/'
}

onMounted(() => {
  fetchStats()
  fetchConfig()
  // 每30秒刷新一次
  setInterval(fetchStats, 30000)
})
</script>

<style scoped>
/* 可添加自定义样式 */
</style>
