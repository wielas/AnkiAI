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
        <div className="space-y-10">
            {!selectedFile ? (
                <FileDropzone onFileSelect={onFileSelect} uploading={uploading} />
            ) : (
                <div className="space-y-8">
                    <FilePreview file={selectedFile} onRemove={() => onFileSelect(null)} />
                    <ConfigForm config={config} setConfig={setConfig} disabled={uploading} />

                    <button
                        onClick={onStart}
                        disabled={disabled}
                        className="btn-primary w-full text-xl py-5"
                    >
                        {uploading ? 'Preparing your session...' : 'Generate Flashcards'}
                    </button>

                    <p className="text-center text-xs text-jungle/40 dark:text-lime/40 font-sans tracking-wide">
                        Your document will be processed locally and securely.
                    </p>
                </div>
            )}
        </div>
    )
}
