import { Terminal } from 'lucide-react'

export function ProgressSection({ progress, statusMessage, currentPage, totalPages }) {
    const percentage = Math.round(progress * 100)

    return (
        <div className="space-y-10 py-10 animate-in fade-in duration-700">
            <div className="text-center space-y-4">
                <div className="relative inline-flex flex-col items-center justify-center">
                    <svg className="w-48 h-48 transform -rotate-90">
                        <circle
                            cx="96"
                            cy="96"
                            r="88"
                            stroke="currentColor"
                            strokeWidth="12"
                            fill="transparent"
                            className="text-gray-100 dark:text-gray-700"
                        />
                        <circle
                            cx="96"
                            cy="96"
                            r="88"
                            stroke="currentColor"
                            strokeWidth="12"
                            fill="transparent"
                            strokeDasharray={552.92}
                            strokeDashoffset={552.92 * (1 - progress)}
                            className="text-indigo-600 transition-all duration-1000 ease-out"
                            strokeLinecap="round"
                        />
                    </svg>
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
                        <span className="text-5xl font-black text-indigo-600 dark:text-indigo-400">
                            {percentage}%
                        </span>
                    </div>
                </div>

                <div className="space-y-2">
                    <h2 className="text-2xl font-bold">Generating Flashcards</h2>
                    {currentPage && totalPages && (
                        <p className="text-sm font-semibold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-3 py-1 rounded-full inline-block">
                            Page {currentPage} of {totalPages}
                        </p>
                    )}
                </div>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500" />
                <div className="flex items-center gap-3 text-indigo-400 mb-4">
                    <Terminal size={18} />
                    <span className="text-xs font-mono font-bold tracking-widest uppercase">Process Logs</span>
                </div>
                <div className="font-mono text-sm text-gray-300 leading-relaxed min-h-[60px] flex items-center">
                    {statusMessage || 'Initializing generation engine...'}
                    <span className="w-2 h-5 bg-indigo-500 ml-2 animate-pulse" />
                </div>
            </div>

            <div className="text-center">
                <p className="text-xs text-gray-500 italic">
                    Please keep this window open while we process your request.
                </p>
            </div>
        </div>
    )
}
