import { AlertCircle, X } from 'lucide-react'

export function ErrorDisplay({ message, onClose }) {
    return (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl flex items-start gap-3 text-red-600 dark:text-red-400 animate-in slide-in-from-top-2 duration-300 mb-6">
            <AlertCircle className="shrink-0 mt-0.5" size={20} />
            <div className="flex-1">
                <p className="text-sm font-bold">Process Error</p>
                <p className="text-sm opacity-90">{message}</p>
            </div>
            {onClose && (
                <button
                    onClick={onClose}
                    className="p-1 hover:bg-white dark:hover:bg-gray-800 rounded-lg transition-colors"
                >
                    <X size={16} />
                </button>
            )}
        </div>
    )
}
