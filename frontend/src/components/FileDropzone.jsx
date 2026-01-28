import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { FileUp, FileWarning } from 'lucide-react'
import { motion } from 'framer-motion'

export function FileDropzone({ onFileSelect, uploading }) {
    const onDrop = useCallback((acceptedFiles) => {
        if (acceptedFiles?.length > 0) {
            onFileSelect(acceptedFiles[0])
        }
    }, [onFileSelect])

    const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'] },
        maxFiles: 1,
        disabled: uploading
    })

    return (
        <div className="space-y-4">
            <motion.div
                {...getRootProps()}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                className={`border-2 border-dashed rounded-[2rem] p-16 text-center transition-all cursor-pointer group relative overflow-hidden ${isDragActive
                    ? 'border-lime bg-lime/10'
                    : 'border-jungle/10 dark:border-lime/10 hover:border-lime/40 hover:bg-lime/5'
                    }`}
            >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center space-y-6 relative z-10">
                    <div className={`p-6 rounded-3xl bg-lime/10 text-lime group-hover:bg-lime group-hover:text-jungle transition-all duration-500 ${isDragActive ? 'bg-lime text-jungle scale-110' : ''}`}>
                        <FileUp size={48} strokeWidth={1.5} />
                    </div>
                    <div className="space-y-2">
                        <p className="text-2xl font-serif font-medium text-jungle dark:text-white">
                            {isDragActive ? 'Release to begin' : 'Deep dive into your PDF'}
                        </p>
                        <p className="text-sm text-jungle/40 dark:text-lime/40 font-sans tracking-wide">
                            Drag & drop or click to explore
                        </p>
                    </div>
                </div>

                {/* Decorative subtle background icon */}
                <FileUp className="absolute -bottom-8 -right-8 text-jungle/5 dark:text-lime/5 w-48 h-48 -rotate-12" />
            </motion.div>

            {fileRejections.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-red-600 dark:text-red-400"
                >
                    <FileWarning size={20} />
                    <p className="text-sm font-medium">Please select a valid PDF file.</p>
                </motion.div>
            )}
        </div>
    )
}
