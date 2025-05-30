import { createRouter, createWebHistory } from 'vue-router'
import ChatInterface from '../components/ChatInterface.vue'

const routes = [
  {
    path: '/',
    name: 'Chat',
    component: ChatInterface
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 