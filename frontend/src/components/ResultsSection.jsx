import { Download, CheckCircle2, RotateCcw } from 'lucide-react'
import { motion } from 'framer-motion'
import { apiEndpoint } from '../config'

export function ResultsSection({ jobId, onReset }) {
    const handleDownload = async () => {
        try {
            const response = await fetch(apiEndpoint(`/api/download/${jobId}`))
            if (!response.ok) throw new Error('Download failed')

            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `flashcards-${jobId.slice(0, 8)}.apkg`
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
        } catch (err) {
            alert(`Error downloading file: ${err.message}`)
        }
    }

    return (
        <div className="py-4 text-center space-y-12">
            <div className="flex flex-col items-center gap-6">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{
                        type: "spring",
                        stiffness: 260,
                        damping: 20,
                        delay: 0.2
                    }}
                    className="p-8 bg-lime text-jungle rounded-full shadow-[0_0_40px_rgba(199,239,78,0.3)]"
                >
                    <CheckCircle2 size={64} strokeWidth={1.5} />
                </motion.div>
                <div className="space-y-3">
                    <h2 className="text-4xl font-serif font-bold text-jungle dark:text-white">Creation Complete</h2>
                    <p className="text-lg text-jungle/60 dark:text-lime/60 font-serif italic">
                        Your knowledge deck is now ready for mastery.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4 max-w-sm mx-auto">
                <button
                    onClick={handleDownload}
                    className="btn-primary w-full flex items-center justify-center gap-3 text-lg py-5"
                >
                    <Download size={24} strokeWidth={1.5} />
                    Download Deck
                </button>

                <button
                    onClick={onReset}
                    className="btn-secondary w-full flex items-center justify-center gap-3 text-lg py-5"
                >
                    <RotateCcw size={20} strokeWidth={1.5} />
                    New Project
                </button>
            </div>

            <div className="p-8 bg-black/5 dark:bg-white/5 rounded-[2rem] border border-jungle/5 dark:border-lime/5 text-left max-w-lg mx-auto">
                <h4 className="font-serif font-bold text-jungle dark:text-lime text-xl mb-4 flex items-center gap-3">
                    Next Masteries:
                </h4>
                <ol className="text-sm text-jungle/70 dark:text-lime/70 space-y-4 font-sans leading-relaxed">
                    <li className="flex gap-4">
                        <span className="flex-none w-6 h-6 rounded-full bg-lime/20 text-lime flex items-center justify-center font-bold text-xs">1</span>
                        <span>Open <b>Anki</b> on your workstation.</span>
                    </li>
                    <li className="flex gap-4">
                        <span className="flex-none w-6 h-6 rounded-full bg-lime/20 text-lime flex items-center justify-center font-bold text-xs">2</span>
                        <span>Import the <b>.apkg</b> from your downloads.</span>
                    </li>
                    <li className="flex gap-4">
                        <span className="flex-none w-6 h-6 rounded-full bg-lime/20 text-lime flex items-center justify-center font-bold text-xs">3</span>
                        <span>Embark on your journey of deep understanding.</span>
                    </li>
                </ol>
            </div>
        </div>
    )
}
