import { Download, CheckCircle2, RotateCcw } from 'lucide-react'

export function ResultsSection({ jobId, onReset }) {
    const handleDownload = async () => {
        try {
            const response = await fetch(`/api/download/${jobId}`)
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
        <div className="py-10 text-center space-y-10 animate-in zoom-in-95 duration-500">
            <div className="flex flex-col items-center gap-4">
                <div className="p-4 bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-full animate-bounce">
                    <CheckCircle2 size={64} />
                </div>
                <div className="space-y-2">
                    <h2 className="text-3xl font-black text-gray-900 dark:text-white">Deck Ready!</h2>
                    <p className="text-gray-600 dark:text-gray-400 font-medium">
                        Your AI-generated flashcards are ready for download.
                    </p>
                </div>
            </div>

            <div className="space-y-4">
                <button
                    onClick={handleDownload}
                    className="w-full py-4 px-6 bg-green-600 hover:bg-green-700 text-white rounded-2xl font-bold text-xl transition-all shadow-lg hover:shadow-green-500/50 flex items-center justify-center gap-3 transform hover:-translate-y-1"
                >
                    <Download size={24} />
                    Download .apkg file
                </button>

                <button
                    onClick={onReset}
                    className="w-full py-4 px-6 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-2 border-gray-200 dark:border-gray-700 rounded-2xl font-bold flex items-center justify-center gap-3 transition-all hover:bg-gray-50 dark:hover:bg-gray-700/50"
                >
                    <RotateCcw size={20} />
                    Start New Project
                </button>
            </div>

            <div className="p-6 bg-indigo-50 dark:bg-indigo-900/20 rounded-2xl border border-indigo-100 dark:border-indigo-900/30 text-left">
                <h4 className="font-bold text-indigo-900 dark:text-indigo-300 mb-2 flex items-center gap-2">
                    Next Steps:
                </h4>
                <ol className="text-sm text-indigo-800 dark:text-indigo-400 space-y-2 list-decimal list-inside">
                    <li>Open Anki on your desktop.</li>
                    <li>Click "Import File" from the main menu.</li>
                    <li>Select the downloaded <b>.apkg</b> file.</li>
                    <li>Start studying with your new AI-powered deck!</li>
                </ol>
            </div>
        </div>
    )
}
