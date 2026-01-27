import { FileDropzone } from './FileDropzone'
import { FilePreview } from './FilePreview'
import { ConfigForm } from './ConfigForm'

export function UploadSection({
    selectedFile,
    onFileSelect,
    uploading,
    config,
    setConfig,
    onStart,
    disabled
}) {
    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {!selectedFile ? (
                <FileDropzone onFileSelect={onFileSelect} uploading={uploading} />
            ) : (
                <div className="space-y-6">
                    <FilePreview file={selectedFile} onRemove={() => onFileSelect(null)} />
                    <ConfigForm config={config} setConfig={setConfig} disabled={uploading} />

                    <button
                        onClick={onStart}
                        disabled={disabled}
                        className={`w-full py-4 px-6 rounded-xl font-bold text-lg transition-all transform active:scale-95 shadow-lg ${disabled
                                ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed shadow-none'
                                : 'bg-indigo-600 hover:bg-indigo-700 text-white hover:shadow-indigo-500/50'
                            }`}
                    >
                        {uploading ? 'Uploading PDF...' : 'Generate Flashcards'}
                    </button>
                </div>
            )}
        </div>
    )
}
