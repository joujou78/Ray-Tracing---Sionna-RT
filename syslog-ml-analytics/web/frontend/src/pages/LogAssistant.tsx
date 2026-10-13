import { useState } from 'react'
import type { FormEvent } from 'react'
import { logAssistantApi } from '../api/logAssistant'
import type { ChatMessage } from '../types'

export function LogAssistant() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendQuestion = async (e: FormEvent) => {
    e.preventDefault()
    const question = input.trim()
    if (!question || loading) return

    setMessages((m) => [...m, { role: 'user', content: question }])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const response = await logAssistantApi.ask(question)
      setMessages((m) => [...m, { role: 'assistant', content: response.answer, sources: response.sources }])
    } catch {
      setError('Could not reach the Log Assistant — is Ollama/OpenSearch reachable from the API?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Log Assistant</h2>
      <p className="page-hint">
        Ask questions about recent syslog events in plain language. Answers are grounded only in log excerpts
        retrieved by semantic search — the assistant says so when it can't find enough evidence rather than
        guessing.
      </p>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.length === 0 && !loading && (
            <p className="page-hint">e.g. "any authentication failures on core-switch-1 today?"</p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`chat-message chat-message-${m.role}`}>
              <div className="chat-message-content">{m.content}</div>
              {m.sources && m.sources.length > 0 && (
                <details className="chat-sources">
                  <summary>
                    {m.sources.length} source log{m.sources.length === 1 ? '' : 's'}
                  </summary>
                  <ul>
                    {m.sources.map((s, j) => (
                      <li key={j} className="chat-source-item">
                        <span className="mono">{new Date(s.event_time).toLocaleString()}</span>{' '}
                        <strong>{s.hostname}</strong> ({s.severity}/{s.program}): {s.message}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          ))}
          {loading && <div className="chat-message chat-message-assistant chat-message-pending">Thinking…</div>}
        </div>

        {error && <p className="form-error">{error}</p>}

        <form className="chat-input-row" onSubmit={sendQuestion}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about recent logs…"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  )
}
