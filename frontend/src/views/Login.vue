<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">
          <el-icon :size="32" color="#2563eb"><Aim /></el-icon>
        </div>
        <h1>AI采购商雷达</h1>
        <p>智能海外采购商发现与管理系统</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleLogin"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            placeholder="密码"
            type="password"
            size="large"
            show-password
            :prefix-icon="Lock"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-alert
          v-if="errorMsg"
          :title="errorMsg"
          type="error"
          :closable="true"
          show-icon
          class="login-error"
          @close="errorMsg = ''"
        />

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../services/api'
import { User, Lock, Aim } from '@element-plus/icons-vue'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const errorMsg = ref('')

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  errorMsg.value = ''

  try {
    const res = await authAPI.login(form.username, form.password)
    const token = res.token || res.access_token
    if (token) {
      localStorage.setItem('token', token)
      if (res.username) {
        localStorage.setItem('username', res.username)
      } else {
        localStorage.setItem('username', form.username)
      }
      router.push('/')
    } else {
      errorMsg.value = '登录响应异常，请重试'
    }
  } catch (e) {
    const detail = e.response?.data?.detail
    if (typeof detail === 'string') {
      errorMsg.value = detail
    } else if (e.response?.status === 401) {
      errorMsg.value = '用户名或密码错误'
    } else {
      errorMsg.value = '登录失败，请检查网络连接'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f6f8;
  position: relative;
  overflow: hidden;
}

.login-page::before {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(37,99,235,0.06) 0%, transparent 70%);
  top: -200px;
  right: -100px;
  pointer-events: none;
}

.login-page::after {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(37,99,235,0.05) 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
  pointer-events: none;
}

.login-card {
  width: 400px;
  max-width: 90vw;
  background: #ffffff;
  border: 1px solid #e8eaed;
  border-radius: 16px;
  padding: 48px 40px;
  box-shadow: 0 8px 32px rgba(16, 24, 40, 0.08);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-logo {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: #2563eb;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.login-logo .el-icon {
  color: white !important;
}

.login-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1a2332;
  margin-bottom: 6px;
}

.login-header p {
  font-size: 13px;
  color: #8a94a3;
}

.login-form {
  display: flex;
  flex-direction: column;
}

.login-form .el-form-item {
  margin-bottom: 20px;
}

.login-error {
  margin-bottom: 16px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px;
}
</style>
