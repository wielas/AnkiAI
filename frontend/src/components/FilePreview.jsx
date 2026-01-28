import { FileText, X } from 'lucide-react'
import { motion } from 'framer-motion'

export function FilePreview({ file, onRemove }) {
    const formatSize = (bytes) => {
        if (bytes === 0) return '0 Bytes'
        const k = 1024
        const sizes = ['Bytes', 'KB', 'MB', 'GB']
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-6 bg-white/50 dark:bg-jungle/40 backdrop-blur-sm border border-jungle/5 dark:border-lime/10 rounded-[2rem] flex items-center justify-between group shadow-lg"
        >
            <div className="flex items-center gap-6">
                <div className="p-4 bg-lime text-jungle rounded-2xl shadow-lime/20 shadow-xl">
                    <FileText size={32} strokeWidth={1.5} />
                </div>
                <div>
                    <p className="font-serif font-medium text-lg text-jungle dark:text-white truncate max-w-[200px] md:max-w-md">
                        {file.name}
                    </p>
                    <p className="text-xs font-sans tracking-widest uppercase text-jungle/40 dark:text-lime/40 mt-1">
                        {formatSize(file.size)}
                    </p>
                </div>
            </div>
            <button
                onClick={onRemove}
                className="p-3 bg-jungle/5 dark:bg-lime/5 hover:bg-red-500 hover:text-white rounded-2xl transition-all duration-300 text-jungle/30 dark:text-lime/30"
                title="Remove file"
            >
                <X size={20} strokeWidth={2.5} />
            </button>
        </motion.div>
    )
}
