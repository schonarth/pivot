export function parseNumericInput(value: string): string {
  let s = value.trim()
  s = s.replace(/\s/g, '')
  if (!s) return '0'

  const hasDot = s.includes('.')
  const hasComma = s.includes(',')

  if (hasDot && hasComma) {
    const lastDot = s.lastIndexOf('.')
    const lastComma = s.lastIndexOf(',')
    if (lastComma > lastDot) {
      s = s.replace(/\./g, '').replace(',', '.')
    } else {
      s = s.replace(/,/g, '')
    }
  } else if (hasComma) {
    s = s.replace(',', '.')
  } else if (hasDot) {
    const parts = s.split('.')
    if (parts.length === 2 && parts[1].length === 3 && parts[0].length >= 1 && /^\d+$/.test(parts[1])) {
      s = s.replace('.', '')
    }
  }

  return s
}

export function formatCurrency(value: string | number, currency?: string, locale?: string): string {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '-'
  const loc = locale || (currency === 'BRL' ? 'pt-BR' : currency === 'GBP' ? 'en-GB' : currency === 'EUR' ? 'de-DE' : 'en-US')
  return num.toLocaleString(loc, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function parseSubmitValue(value: string): string {
  return parseNumericInput(value)
}