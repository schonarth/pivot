import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import RegisterView from '../RegisterView.vue'
import { createRouter, createMemoryHistory, Router } from 'vue-router'

describe('RegisterView', () => {
  let router: Router

  beforeEach(() => {
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/register', component: RegisterView },
        { path: '/', component: { template: '<div>Home</div>' } },
        { path: '/login', component: { template: '<div>Login</div>' } },
      ],
    })
  })

  it('renders registration form', () => {
    const wrapper = mount(RegisterView, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.find('.auth-container').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('Register')
    expect(wrapper.findAll('input').length).toBeGreaterThan(0)
  })

  it('has email, username, and password inputs', () => {
    const wrapper = mount(RegisterView, {
      global: {
        plugins: [router],
      },
    })

    const inputs = wrapper.findAll('input')
    expect(inputs.length).toBeGreaterThanOrEqual(3)
  })

  it('has submit button', () => {
    const wrapper = mount(RegisterView, {
      global: {
        plugins: [router],
      },
    })

    const button = wrapper.find('button')
    expect(button.exists()).toBe(true)
    expect(button.text()).toContain('Register')
  })
})
