import { Terminal, Circle } from 'lucide-react'
import { motion } from 'framer-motion'

export function ProgressSection({ progress, statusMessage, currentPage, totalPages }) {
    const percentage = Math.round(progress * 100)

    return (
        <div className="space-y-12 py-12">
            <div className="text-center space-y-8">
                <div className="relative inline-flex flex-col items-center justify-center">
                    {/* Elaborate Progress Ring */}
                    <svg className="w-56 h-56 transform -rotate-90 drop-shadow-[0_0_15px_rgba(199,239,78,0.2)]">
                        <circle
                            cx="112"
                            cy="112"
                            r="104"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="transparent"
                            className="text-jungle/5 dark:text-lime/5"
                        />
                        <motion.circle
                            cx="112"
                            cy="112"
                            r="104"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="transparent"
                            strokeDasharray={653.45}
                            initial={{ strokeDashoffset: 653.45 }}
                            animate={{ strokeDashoffset: 653.45 * (1 - progress) }}
                            transition={{ duration: 1.5, ease: "easeInOut" }}
                            className="text-lime"
                            strokeLinecap="round"
                        />

                        {/* Decorative Outer Ring */}
                        <circle
                            cx="112"
                            cy="112"
                            r="108"
                            stroke="currentColor"
                            strokeWidth="1"
                            fill="transparent"
                            className="text-lime/20"
                            strokeDasharray="4 8"
                        />
                    </svg>

                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
                        <motion.span
                            initial={{ opacity: 0, scale: 0.5 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="text-6xl font-serif font-bold text-jungle dark:text-lime"
                        >
                            {percentage}<span className="text-3xl opacity-50">%</span>
                        </motion.span>
                    </div>
                </div>

                <div className="space-y-4">
                    <h2 className="text-3xl font-serif font-medium text-jungle dark:text-white">Synthesizing Cards</h2>
                    {currentPage && totalPages && (
                        <div className="inline-flex items-center gap-2 px-6 py-2 rounded-full bg-lime/10 border border-lime/20 text-lime font-bold tracking-widest uppercase text-xs">
                            <Circle size={10} className="fill-current animate-pulse" />
                            Page {currentPage} of {totalPages}
                        </div>
                    )}
                </div>
            </div>

            <div className="bg-black/80 backdrop-blur-xl border border-white/5 rounded-3xl p-8 shadow-3xl relative overflow-hidden group">
                <div className="flex items-center gap-4 text-lime/60 mb-6 px-1">
                    <Terminal size={18} strokeWidth={1.5} />
                    <span className="text-xs font-sans font-bold tracking-[0.2em] uppercase">Computational Log</span>
                </div>
                <div className="font-mono text-sm text-lime-light/80 leading-relaxed min-h-[60px] flex items-center px-1">
                    <span className="text-lime mr-3">❯</span>
                    {statusMessage || 'Orchestrating AI generation...'}
                    <span className="w-2.5 h-6 bg-lime/40 ml-3 animate-pulse rounded-sm" />
                </div>

                {/* Visual texture */}
                <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                    <Terminal size={120} />
                </div>
            </div>

            <div className="text-center font-serif italic text-jungle/40 dark:text-lime/40">
                <p className="text-sm">
                    Moments of patience lead to mastery.
                </p>
            </div>
        </div>
    )
}
