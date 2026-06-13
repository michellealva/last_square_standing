import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('./views/Home.vue') },
  {
    path: '/:roomCode',
    name: 'Room',
    component: () => import('./views/Room.vue'),
    props: true,
  },
]

export default createRouter({
  history: createWebHistory('/lss'),
  routes,
})
