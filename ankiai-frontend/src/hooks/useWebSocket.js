import { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

export function useWebSocket(jobId) {
    const [progress, setProgress] = useState(0);
    const [status, setStatus] = useState('idle');
    const [currentPage, setCurrentPage] = useState(null);
    const [totalPages, setTotalPages] = useState(null);
    const [message, setMessage] = useState('');
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!jobId) return;

        let socket = null;
        let retryCount = 0;
        const maxRetries = 3;

        const connect = () => {
            socket = new WebSocket(`${WS_BASE_URL}/ws/progress/${jobId}`);

            socket.onopen = () => {
                console.log('WebSocket Connected');
                setStatus('processing');
                setError(null);
                retryCount = 0;
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('WS Message:', data);

                if (data.type === 'progress') {
                    setProgress(data.progress || 0);
                    setCurrentPage(data.current_page);
                    setTotalPages(data.total_pages);
                    setMessage(data.message || '');
                } else if (data.type === 'complete') {
                    setProgress(1);
                    setStatus('completed');
                    setMessage('Generation complete!');
                    socket.close();
                } else if (data.type === 'error') {
                    setError(data.error || 'Generation failed');
                    setStatus('failed');
                    socket.close();
                }
            };

            socket.onerror = (err) => {
                console.error('WebSocket Error:', err);
                // Don't set error yet, let onclose handle retry
            };

            socket.onclose = (event) => {
                console.log('WebSocket Closed:', event);
                if (status !== 'completed' && status !== 'failed' && retryCount < maxRetries) {
                    retryCount++;
                    console.log(`Retrying connection... (${retryCount}/${maxRetries})`);
                    setTimeout(connect, 2000);
                } else if (status !== 'completed' && status !== 'failed') {
                    setError('Connection lost. Please check your network.');
                    setStatus('failed');
                }
            };
        };

        connect();

        return () => {
            if (socket) {
                socket.close();
            }
        };
    }, [jobId]);

    return { progress, status, currentPage, totalPages, message, error };
}
