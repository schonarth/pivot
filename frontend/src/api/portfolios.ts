import api from './client'
import type { Portfolio, PortfolioSummary, CashTransaction } from '@/types'

export async function getPortfolios(): Promise<Portfolio[]> {
  const { data } = await api.get('/portfolios/')
  return data.results ?? data
}

export async function getPortfolio(id: string): Promise<Portfolio> {
  const { data } = await api.get(`/portfolios/${id}/`)
  return data
}

export async function createPortfolio(name: string, market: string, initialCapital: string): Promise<Portfolio> {
  const { data } = await api.post('/portfolios/', { name, market, initial_capital: initialCapital })
  return data
}

export async function updatePortfolio(id: string, payload: Partial<Portfolio>): Promise<Portfolio> {
  const { data } = await api.patch(`/portfolios/${id}/`, payload)
  return data
}

export async function deletePortfolio(id: string): Promise<void> {
  await api.delete(`/portfolios/${id}/`)
}

export async function getPortfolioSummary(id: string): Promise<PortfolioSummary> {
  const { data } = await api.get(`/portfolios/${id}/summary/`)
  return data
}

export async function getPortfolioPerformance(id: string) {
  const { data } = await api.get(`/portfolios/${id}/performance/`)
  return data
}

export async function refreshPortfolioPrices(id: string) {
  const { data } = await api.post(`/portfolios/${id}/refresh_prices/`)
  return data
}

export async function deposit(id: string, amount: string) {
  const { data } = await api.post(`/portfolios/${id}/deposit/`, { amount })
  return data
}

export async function withdraw(id: string, amount: string) {
  const { data } = await api.post(`/portfolios/${id}/withdraw/`, { amount })
  return data
}

export async function getCashTransactions(id: string): Promise<CashTransaction[]> {
  const { data } = await api.get(`/portfolios/${id}/cash_transactions/`)
  return data.results ?? data
}

export async function getPortfolioTimeline(id: string) {
  const { data } = await api.get(`/portfolios/${id}/timeline/`)
  return data
}