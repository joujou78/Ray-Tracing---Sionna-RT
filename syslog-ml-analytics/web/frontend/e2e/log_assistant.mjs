/**
 * Browser test of the Log Assistant chat page against a running instance of
 * the app (backend + frontend dev server, or a built+served frontend).
 *
 * Requires an existing admin account (see scripts/create_admin.py in
 * web/backend) for real Postgres-backed login, same as smoke.mjs. Unlike
 * smoke.mjs, it mocks the single /api/log-assistant/ask call rather than
 * hitting it for real: that endpoint depends on OpenSearch + Ollama, which
 * aren't infrastructure this test should require just to verify the page
 * wires requests/responses/errors correctly. It still exercises a real
 * question -> request -> rendered answer+sources round trip through actual
 * React state, just with a scripted response standing in for the LLM.
 *
 * Usage:
 *   BASE_URL=http://127.0.0.1:5173 ADMIN_USERNAME=admin ADMIN_PASSWORD=... \
 *     node e2e/log_assistant.mjs
 */
import { chromium } from 'playwright'

const base = process.env.BASE_URL ?? 'http://127.0.0.1:5173'
const username = process.env.ADMIN_USERNAME ?? 'admin'
const password = process.env.ADMIN_PASSWORD

if (!password) {
  console.error('Set ADMIN_PASSWORD to an existing admin account\'s password before running this script.')
  process.exit(1)
}

const browser = await chromium.launch()
const page = await browser.newPage()

const failedResponses = []
page.on('pageerror', (e) => failedResponses.push({ url: '(uncaught exception)', detail: String(e) }))
page.on('response', (response) => {
  if (response.status() >= 400) {
    failedResponses.push({ url: response.url(), status: response.status() })
  }
})

// /devices 500s happen whenever ClickHouse isn't running -- same expected
// failure smoke.mjs tolerates, unrelated to anything this test checks (login
// lands on the Devices page before we navigate away from it).
const isExpectedFailure = (f) => f.url.includes('/api/devices')

console.log('1. Log in as an existing admin (real Postgres-backed auth)')
await page.goto(base + '/login')
await page.fill('input[required]', username)
await page.fill('input[type=password]', password)
await page.click('button[type=submit]')
await page.waitForURL(base + '/')
console.log('   OK, logged in')

console.log('2. Nav shows the "Log Assistant" link')
const navText = await page.textContent('.app-nav')
if (!navText.includes('Log Assistant')) throw new Error('Log Assistant nav link missing')
console.log('   OK')

console.log('3. Navigate to /assistant')
await page.click('text=Log Assistant')
await page.waitForURL('**/assistant')
await page.waitForSelector('h2')
console.log('   OK, heading:', await page.textContent('h2'))

console.log('4. Ask a question (mocked /api/log-assistant/ask -- see file docstring)')
const question = 'any auth failures on core-switch-1?'
await page.route('**/api/log-assistant/ask', async (route) => {
  const body = route.request().postDataJSON()
  if (body.question !== question) throw new Error('unexpected question payload: ' + JSON.stringify(body))
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      answer: 'Yes — core-switch-1 logged 3 failed SSH authentication attempts between 02:14 and 02:17 today.',
      sources: [
        {
          event_time: '2026-10-13T02:14:00Z',
          hostname: 'core-switch-1',
          severity: 'warning',
          program: 'sshd',
          message: 'Failed password for admin from 10.0.0.5',
          predicted_category: 'AUTH',
          is_anomaly: true,
          score: 0.91,
        },
      ],
    }),
  })
})
await page.fill('input[placeholder="Ask about recent logs…"]', question)
await page.click('button:has-text("Send")')

console.log('5. User message bubble appears with the question text')
await page.waitForSelector('.chat-message-user')
const userText = await page.textContent('.chat-message-user')
if (!userText.includes(question)) throw new Error('user bubble missing question text')
console.log('   OK:', userText)

console.log('6. Assistant answer renders with its sources')
await page.waitForSelector('.chat-message-assistant .chat-message-content')
const answerText = await page.textContent('.chat-message-assistant .chat-message-content')
if (!answerText.includes('3 failed SSH authentication attempts')) throw new Error('assistant answer text missing/wrong')
console.log('   OK:', answerText)
await page.click('.chat-sources summary')
const sourceItem = await page.textContent('.chat-source-item')
if (!sourceItem.includes('core-switch-1') || !sourceItem.includes('Failed password for admin')) {
  throw new Error('source item missing expected fields: ' + sourceItem)
}
console.log('   OK, source item:', sourceItem)

console.log('7. Input clears and Send disables again once empty')
const inputValue = await page.inputValue('input[placeholder="Ask about recent logs…"]')
if (inputValue !== '') throw new Error('input not cleared after send')
if (!(await page.isDisabled('button:has-text("Send")'))) throw new Error('Send should disable when input is empty')
console.log('   OK')

console.log('8. Upstream failure (502) shows a clear error, not a crash')
await page.route('**/api/log-assistant/ask', (route) =>
  route.fulfill({ status: 502, contentType: 'application/json', body: JSON.stringify({ detail: 'Log Assistant backend error: connection refused' }) }),
)
await page.fill('input[placeholder="Ask about recent logs…"]', 'second question')
await page.click('button:has-text("Send")')
await page.waitForSelector('.form-error')
console.log('   OK, error shown:', await page.textContent('.form-error'))

await browser.close()

const unexpected = failedResponses.filter((f) => !isExpectedFailure(f) && !(f.url.includes('/log-assistant/ask') && f.status === 502))
if (unexpected.length) {
  console.log('\nUnexpected failed requests/exceptions:')
  for (const f of unexpected) console.log(' -', f.status ?? '', f.url, f.detail ?? '')
  process.exit(1)
}

console.log('\nALL LOG ASSISTANT CHECKS PASSED')
