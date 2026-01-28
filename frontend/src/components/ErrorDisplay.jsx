import { AlertCircle, X } from 'lucide-react'
import { motion } from 'framer-motion'

export function ErrorDisplay({ message, onClose }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 bg-red-500/10 backdrop-blur-md border border-red-500/20 rounded-[2rem] flex items-start gap-4 text-red-600 dark:text-red-400 mb-8 shadow-xl shadow-red-500/5"
        >
            <div className="p-2 bg-red-500 text-white rounded-xl shadow-lg shadow-red-500/20">
                <AlertCircle size={24} strokeWidth={2} />
            </div>
            <div className="flex-1">
                <p className="text-sm font-bold tracking-widest uppercase mb-1">Process Disturbance</p>
                <p className="text-lg font-serif italic text-red-600/80 dark:text-red-400/80 leading-snug">{message}</p>
            </div>
            {onClose && (
                <button
                    onClick={onClose}
                    className="p-2 hover:bg-red-500/10 rounded-xl transition-colors text-red-600/50"
                >
                    <X size={20} strokeWidth={2.5} />
                </button>
            )}
        </motion.div>
    )
}
