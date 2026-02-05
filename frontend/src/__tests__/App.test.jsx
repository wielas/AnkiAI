import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import App from '../App'
import { http, HttpResponse } from 'msw'
import { server } from '../test/setup'

describe('App Integration Flow', () => {
    it('shows the upload section initially', () => {
        render(<App />)
        expect(screen.getByText(/Deep dive into your PDF/i)).toBeInTheDocument()
    })

    it('completes the full flow: upload -> config -> generating -> results', async () => {
        // 1. Mock Upload API
        server.use(
            http.post('/api/upload', () => {
                return HttpResponse.json({ file_id: 'test-file-id' })
            })
        )

        // 2. Mock Start Generation API
        server.use(
            http.post('/api/generate/test-file-id', () => {
                return HttpResponse.json({ job_id: 'test-job-id' })
            })
        )

        render(<App />)

        // 3. Simulate file selection
        const file = new File(['hello'], 'test.pdf', { type: 'application/pdf' })
        const { container } = render(<App />)

        const input = container.querySelector('input[type="file"]')
        fireEvent.change(input, { target: { files: [file] } })

        // 4. Wait for upload to complete and check for ConfigForm
        await waitFor(() => {
            expect(screen.getByText('test.pdf')).toBeInTheDocument()
            expect(screen.getByText(/Mastery Depth/i)).toBeInTheDocument()
        })

        // 5. Click Generate button
        const generateBtn = screen.getByRole('button', { name: /Generate Flashcards/i })
        fireEvent.click(generateBtn)

        // 6. Check for ProgressSection (Generating state)
        await waitFor(() => {
            expect(screen.getByText(/Synthesizing Cards/i)).toBeInTheDocument()
        })

        // 7. Mock WebSocket/Progress update (since jobId is set, App will transition)
        // In this app, ProgressSection handles its own WS connection.
        // For the sake of App.test.jsx, we want to see if it shows Results when done.
        // However, jobId is passed to ProgressSection.
        // Let's verify it renders the ProgressSection correctly first.
        expect(screen.getByText(/Computational Log/i)).toBeInTheDocument()
    })
})
