import { useState, useCallback, useEffect } from 'react'
import { UploadSection } from './components/UploadSection'
import { ProgressSection } from './components/ProgressSection'
import { ResultsSection } from './components/ResultsSection'
import { ErrorDisplay } from './components/ErrorDisplay'
import { useWebSocket } from './hooks/useWebSocket'

function App() {
    const [selectedFile, setSelectedFile] = useState(null)
    const [fileId, setFileId] = useState(null)
    const [uploading, setUploading] = useState(false)

    const [config, setConfig] = useState({
        startPage: 1,
        endPage: 1,
        difficulty: 'intermediate',
        cardsPerPage: 1
    })

    const [jobId, setJobId] = useState(null)
    const [generating, setGenerating] = useState(false)
    const [completed, setCompleted] = useState(false)
    const [error, setError] = useState(null)

    const { progress, statusMessage, currentPage, totalPages, wsError } = useWebSocket(jobId)

    // Handle errors from WebSocket or APIs
    useEffect(() => {
        if (wsError) {
            setError(`Connection error: ${wsError}`)
        }
    }, [wsError])

    const handleFileUpload = async (file) => {
        setUploading(true)
        setError(null)
        setSelectedFile(file)

        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            })

            if (!response.ok) throw new Error('Upload failed')

            const data = await response.json()
            setFileId(data.file_id)
        } catch (err) {
            setError(err.message)
        } finally {
            setUploading(false)
        }
    }

    const handleStartGeneration = async () => {
        if (!fileId) return

        setGenerating(true)
        setError(null)

        try {
            const response = await fetch(`/api/generate/${fileId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_page: config.startPage,
                    end_page: config.endPage,
                    difficulty: config.difficulty,
                    cards_per_page: config.cardsPerPage
                }),
            })

            if (!response.ok) throw new Error('Failed to start generation')

            const data = await response.json()
            setJobId(data.job_id)
        } catch (err) {
            setError(err.message)
            setGenerating(false)
        }
    }

    useEffect(() => {
        if (progress === 1 && jobId) {
            setGenerating(false)
            setCompleted(true)
        }
    }, [progress, jobId])

    const handleReset = () => {
        setSelectedFile(null)
        setFileId(null)
        setJobId(null)
        setGenerating(false)
        setCompleted(false)
        setError(null)
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-4 md:p-8">
            <div className="max-w-3xl mx-auto space-y-8">
                <header className="text-center space-y-2">
                    <h1 className="text-4xl font-extrabold tracking-tight text-indigo-600 dark:text-indigo-400">
                        AnkiAI
                    </h1>
                    <p className="text-lg text-gray-600 dark:text-gray-400">
                        Transform your PDFs into high-quality Anki flashcards using AI.
                    </p>
                </header>

                <main className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 md:p-10 transition-all duration-300">
                    {error && <ErrorDisplay message={error} onClose={() => setError(null)} />}

                    {!generating && !completed && (
                        <UploadSection
                            selectedFile={selectedFile}
                            onFileSelect={handleFileUpload}
                            uploading={uploading}
                            config={config}
                            setConfig={setConfig}
                            onStart={handleStartGeneration}
                            disabled={!fileId || uploading}
                        />
                    )}

                    {generating && (
                        <ProgressSection
                            progress={progress}
                            statusMessage={statusMessage}
                            currentPage={currentPage}
                            totalPages={totalPages}
                        />
                    )}

                    {completed && (
                        <ResultsSection
                            jobId={jobId}
                            onReset={handleReset}
                        />
                    )}
                </main>

                <footer className="text-center text-sm text-gray-500 dark:text-gray-500">
                    Built with React & FastAPI
                </footer>
            </div>
        </div>
    )
}

export default App
