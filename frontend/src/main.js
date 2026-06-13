import './index.css'

import { createApp } from 'vue'
import {
  FrappeUI,
  Button,
  FormControl,
  Input,
  Dialog,
  Badge,
  setConfig,
  frappeRequest,
} from 'frappe-ui'

import App from './App.vue'
import router from './router'

setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
app.use(FrappeUI)
app.use(router)
app.component('Button', Button)
app.component('FormControl', FormControl)
app.component('Input', Input)
app.component('Dialog', Dialog)
app.component('Badge', Badge)
app.mount('#app')

// PWA: register the service worker, scoped to the game only. Served from the site
// root (/lss-sw.js) so its max scope covers /lss/; we narrow it to /lss/.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/lss-sw.js', { scope: '/lss/' })
      .catch(() => {
        /* PWA is progressive enhancement; ignore registration failures */
      })
  })
}
