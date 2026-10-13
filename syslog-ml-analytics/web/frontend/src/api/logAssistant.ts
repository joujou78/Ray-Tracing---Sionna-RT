import { apiClient } from './client'
import type { AskResponse } from '../types'

export const logAssistantApi = {
  ask: (question: string) => apiClient.post<AskResponse>('/log-assistant/ask', { question }).then((r) => r.data),
}
