import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/query' },
    { path: '/query', name: 'QueryTest', component: () => import('../views/QueryTest.vue') },
    { path: '/profiles', name: 'Profiles', component: () => import('../views/Profiles.vue') },
    { path: '/documents', name: 'Documents', component: () => import('../views/Documents.vue') },
    { path: '/chunks', name: 'Chunks', component: () => import('../views/Chunks.vue') },
    { path: '/experiments', name: 'Experiments', component: () => import('../views/Experiments.vue') },
  ],
})

export default router
