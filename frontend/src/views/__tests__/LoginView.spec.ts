import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginView from '../LoginView.vue'
import { createRouter, createMemoryHistory, Router } from 'vue-router'

describe('LoginView', () => {
  let router: Router

  beforeEach(() => {
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/login', component: LoginView },
        { path: '/', component: { template: '<div>Home</div>' } },
        { path: '/register', component: { template: '<div>Register</div>' } },
      ],
    })
  })

  it('renders login form', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router],
      },
    })
    expect(wrapper.find('.auth-container').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('Login')
    expect(wrapper.findAll('input').length).toBeGreaterThan(0)
  })

  it('has submit button', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router],
      },
    })
    const button = wrapper.find('button')
    expect(button.exists()).toBe(true)
    expect(button.text()).toContain('Login')
  })

  it('can input username', async () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router],
      },
    })
    const inputs = wrapper.findAll('input')
    const usernameInput = inputs[0]
    await usernameInput.setValue('testuser')
    expect((usernameInput.element as HTMLInputElement).value).toBe('testuser')
  })

  it('can input password', async () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router],
      },
    })
    const inputs = wrapper.findAll('input')
    const passwordInput = inputs[1]
    await passwordInput.setValue('password123')
    expect((passwordInput.element as HTMLInputElement).value).toBe('password123')
  })
})
