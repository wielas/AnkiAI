import { useState, useEffect, useRef } from 'react'
import { wsEndpoint } from '../config'

export function useWebSocket(jobId) {
    const [progress, setProgress] = useState(0)
    const [statusMessage, setStatusMessage] = useState('')
    const [currentPage, setCurrentPage] = useState(null)
    const [totalPages, setTotalPages] = useState(null)
    const [wsError, setWsError] = useState(null)
    const ws = useRef(null)

    useEffect(() => {
        if (!jobId) {
            setProgress(0)
            setStatusMessage('')
            setCurrentPage(null)
            setTotalPages(null)
            setWsError(null)
            return
        }

        const wsUrl = wsEndpoint(`/ws/progress/${jobId}`)
        console.log(`Connecting to WebSocket: ${wsUrl}`)

        ws.current = new WebSocket(wsUrl)

        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data)
            console.log('WS Message:', data)

            if (data.type === 'progress') {
                setProgress(data.progress)
                setStatusMessage(data.message)
                setCurrentPage(data.current_page)
                setTotalPages(data.total_pages)
            } else if (data.type === 'complete') {
                setProgress(1)
                setStatusMessage('Generation complete!')
            } else if (data.type === 'error') {
                setWsError(data.error)
            }
        }

        ws.current.onerror = (error) => {
            console.error('WS Error:', error)
            setWsError('WebSocket connection failed')
        }

        ws.current.onclose = () => {
            console.log('WebSocket closed')
        }

        return () => {
            if (ws.current) {
                ws.current.close()
            }
        }
    }, [jobId])

    return { progress, statusMessage, currentPage, totalPages, wsError }
}
