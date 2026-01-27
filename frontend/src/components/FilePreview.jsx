import { FileText, X } from 'lucide-react'

export function FilePreview({ file, onRemove }) {
    const formatSize = (bytes) => {
        if (bytes === 0) return '0 Bytes'
        const k = 1024
        const sizes = ['Bytes', 'KB', 'MB', 'GB']
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    return (
        <div className="p-4 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-2xl flex items-center justify-between group">
            <div className="flex items-center gap-4">
                <div className="p-3 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-xl">
                    <FileText size={28} />
                </div>
                <div>
                    <p className="font-semibold truncate max-w-[200px] md:max-w-md">
                        {file.name}
                    </p>
                    <p className="text-xs text-gray-500 font-medium">
                        {formatSize(file.size)}
                    </p>
                </div>
            </div>
            <button
                onClick={onRemove}
                className="p-2 hover:bg-white dark:hover:bg-gray-800 rounded-full transition-colors text-gray-400 hover:text-red-500"
                title="Remove file"
            >
                <X size={20} />
            </button>
        </div>
    )
}
