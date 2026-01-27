import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { FileUp, FileWarning } from 'lucide-react'

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
            <div
                {...getRootProps()}
                className={`border-3 border-dashed rounded-3xl p-12 text-center transition-all cursor-pointer group ${isDragActive
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-gray-300 dark:border-gray-700 hover:border-indigo-400 hover:bg-gray-50 dark:hover:bg-gray-800/50'
                    }`}
            >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center space-y-4">
                    <div className={`p-4 rounded-2xl bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform duration-300 ${isDragActive ? 'scale-110' : ''}`}>
                        <FileUp size={48} />
                    </div>
                    <div className="space-y-1">
                        <p className="text-xl font-semibold">
                            {isDragActive ? 'Drop the PDF here' : 'Drop your PDF here, or click to browse'}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">
                            Only PDF files are supported
                        </p>
                    </div>
                </div>
            </div>

            {fileRejections.length > 0 && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl flex items-center gap-3 text-red-600 dark:text-red-400">
                    <FileWarning size={20} />
                    <p className="text-sm font-medium">Please select a valid PDF file.</p>
                </div>
            )}
        </div>
    )
}
