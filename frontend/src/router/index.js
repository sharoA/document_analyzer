import { createRouter, createWebHistory } from 'vue-router'
import DocumentAnalysis from '../components/DocumentAnalysis.vue'
import ChatInterface from '../components/ChatInterface.vue'

const routes = [
  {
    path: '/',
    name: 'Chat',
    component: ChatInterface
  },
  {
    path: '/document-analysis',
    name: 'DocumentAnalysis',
    component: DocumentAnalysis
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 