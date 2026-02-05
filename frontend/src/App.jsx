import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { UploadSection } from './components/UploadSection'
import { ProgressSection } from './components/ProgressSection'
import { ResultsSection } from './components/ResultsSection'
import { ErrorDisplay } from './components/ErrorDisplay'
import { useWebSocket } from './hooks/useWebSocket'
import { apiEndpoint } from './config'

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
            const response = await fetch(apiEndpoint('/api/upload'), {
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
            const response = await fetch(apiEndpoint(`/api/generate/${fileId}`), {
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

    const pageVariants = {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
        exit: { opacity: 0, y: -20, transition: { duration: 0.4, ease: "easeIn" } }
    }

    return (
        <div className="min-h-screen selection:bg-lime selection:text-jungle overflow-x-hidden">
            {/* Background Decorative Elements */}
            <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_right,rgba(199,239,78,0.1),transparent_40%),radial-gradient(circle_at_bottom_left,rgba(0,51,16,0.05),transparent_40%)]" />

            <div className="max-w-4xl mx-auto px-4 py-12 md:py-20 space-y-12">
                <motion.header
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="text-center space-y-4"
                >
                    <h1 className="text-6xl md:text-7xl font-serif font-bold tracking-tight text-jungle dark:text-lime">
                        Anki AI
                    </h1>
                    <p className="text-xl md:text-2xl text-jungle/60 dark:text-lime/60 font-serif italic">
                        Synthesizing knowledge, swiftly.
                    </p>
                </motion.header>

                <main className="relative">
                    <AnimatePresence mode="wait">
                        {error && (
                            <motion.div
                                key="error"
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                className="mb-8"
                            >
                                <ErrorDisplay message={error} onClose={() => setError(null)} />
                            </motion.div>
                        )}

                        {!generating && !completed ? (
                            <motion.div
                                key="upload"
                                variants={pageVariants}
                                initial="initial"
                                animate="animate"
                                exit="exit"
                                className="bg-white/40 dark:bg-jungle-light/20 backdrop-blur-xl rounded-[2rem] border border-jungle/5 dark:border-lime/10 shadow-2xl p-8 md:p-12"
                            >
                                <UploadSection
                                    selectedFile={selectedFile}
                                    onFileSelect={handleFileUpload}
                                    uploading={uploading}
                                    config={config}
                                    setConfig={setConfig}
                                    onStart={handleStartGeneration}
                                    disabled={!fileId || uploading}
                                />
                            </motion.div>
                        ) : generating ? (
                            <motion.div
                                key="progress"
                                variants={pageVariants}
                                initial="initial"
                                animate="animate"
                                exit="exit"
                                className="bg-white/40 dark:bg-jungle-light/20 backdrop-blur-xl rounded-[2rem] border border-jungle/5 dark:border-lime/10 shadow-2xl p-8 md:p-12"
                            >
                                <ProgressSection
                                    progress={progress}
                                    statusMessage={statusMessage}
                                    currentPage={currentPage}
                                    totalPages={totalPages}
                                />
                            </motion.div>
                        ) : (
                            <motion.div
                                key="results"
                                variants={pageVariants}
                                initial="initial"
                                animate="animate"
                                exit="exit"
                                className="bg-white/40 dark:bg-jungle-light/20 backdrop-blur-xl rounded-[2rem] border border-jungle/5 dark:border-lime/10 shadow-2xl p-8 md:p-12"
                            >
                                <ResultsSection
                                    jobId={jobId}
                                    onReset={handleReset}
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </main>

                <footer className="text-center">
                    <p className="text-sm tracking-widest uppercase font-sans text-jungle/30 dark:text-lime/30">
                        ~ Learn Efficiently • Study Anki Decks ~
                    </p>
                </footer>
            </div>
        </div>
    )
}

export default App
