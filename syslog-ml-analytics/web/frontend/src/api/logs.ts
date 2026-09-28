import { apiClient } from './client'
import type { LogSearchFilters, LogSearchResponse } from '../types'

export const logsApi = {
  search: (filters: LogSearchFilters) =>
    apiClient
      .get<LogSearchResponse>('/logs/search', {
        params: {
          ...filters,
          // Drop empty-string filters rather than sending them -- an empty
          // hostname/q would otherwise become a literal ILIKE '%%' filter.
          source_ip: filters.source_ip || undefined,
          hostname: filters.hostname || undefined,
          severity: filters.severity || undefined,
          program: filters.program || undefined,
          predicted_category: filters.predicted_category || undefined,
          q: filters.q || undefined,
        },
      })
      .then((r) => r.data),
}
