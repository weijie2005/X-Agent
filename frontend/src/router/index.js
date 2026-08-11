import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'chat',
    component: ChatView,
    meta: { requiresAuth: true }
  },
  {
    path: '/user-management',
    name: 'user-management',
    component: () => import('../views/UserManagement.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/sessions',
    name: 'sessions',
    component: () => import('../views/SessionsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/knowledge-base',
    name: 'knowledge-base',
    component: () => import('../views/KnowledgeBase.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：检查用户是否已登录
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = localStorage.getItem('user')
  
  // 如果路由需要认证
  if (to.meta.requiresAuth) {
    if (!token || !user) {
      // 未登录，跳转到登录页
      next('/login')
    } else {
      // 已登录，继续导航
      next()
    }
  } else {
    // 不需要认证的路由
    if (to.path === '/login' && token && user) {
      // 已登录用户访问登录页，跳转到首页
      next('/')
    } else {
      next()
    }
  }
})

export default router