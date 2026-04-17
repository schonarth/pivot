const expandedScopeKeys = new Set<string>()

export function scopeInsightMemoryKey(title: string, scopeLabel: string): string {
  return `${title}::${scopeLabel}`
}

export function hasExpandedScopeInsight(title: string, scopeLabel: string): boolean {
  return expandedScopeKeys.has(scopeInsightMemoryKey(title, scopeLabel))
}

export function markExpandedScopeInsight(title: string, scopeLabel: string): void {
  expandedScopeKeys.add(scopeInsightMemoryKey(title, scopeLabel))
}

export function clearScopeInsightMemory(): void {
  expandedScopeKeys.clear()
}
