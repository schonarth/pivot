import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '../App.vue'
import { createRouter, createMemoryHistory, Router } from 'vue-router'

describe('App', () => {
  let router: Router

  beforeEach(() => {
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: { template: '<div>Home</div>' } },
        { path: '/login', component: { template: '<div>Login</div>' } },
      ],
    })
  })

  it('renders main app container', () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.find('#app-layout').exists()).toBe(true)
  })

  it('renders without crashing', () => {
    expect(() => {
      mount(App, {
        global: {
          plugins: [router],
        },
      })
    }).not.toThrow()
  })
})
