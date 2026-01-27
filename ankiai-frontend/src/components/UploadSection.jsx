import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, CheckCircle2, Loader2, Sparkles } from 'lucide-react';

export function UploadSection({
    selectedFile,
    uploading,
    fileId,
    onUpload,
    onGenerate,
    config,
    setConfig
}) {
    const onDrop = useCallback(acceptedFiles => {
        if (acceptedFiles?.length > 0) {
            onUpload(acceptedFiles[0]);
        }
    }, [onUpload]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'] },
        multiple: false,
        disabled: uploading || !!fileId
    });

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div
                {...getRootProps()}
                className={`glass-card p-10 border-2 border-dashed transition-all cursor-pointer text-center
          ${isDragActive ? 'border-indigo-500 bg-indigo-500/10' : 'border-slate-700 hover:border-slate-600'}
          ${fileId ? 'border-emerald-500/50 bg-emerald-500/5 cursor-default' : ''}
          ${uploading ? 'opacity-50 cursor-wait' : ''}
        `}
            >
                <input {...getInputProps()} />

                {!selectedFile && !uploading && (
                    <div className="space-y-4">
                        <div className="mx-auto w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center">
                            <Upload className="w-8 h-8 text-slate-400" />
                        </div>
                        <div>
                            <p className="text-xl font-medium">Click to upload or drag and drop</p>
                            <p className="text-slate-400 mt-1">PDF files only (max 50MB)</p>
                        </div>
                    </div>
                )}

                {uploading && (
                    <div className="space-y-4 py-4">
                        <Loader2 className="mx-auto w-12 h-12 text-indigo-500 animate-spin" />
                        <p className="text-xl font-medium text-indigo-400">Uploading Document...</p>
                    </div>
                )}

                {fileId && (
                    <div className="space-y-4">
                        <div className="mx-auto w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center">
                            <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                        </div>
                        <div>
                            <p className="text-xl font-medium text-emerald-400">File Uploaded Successfully</p>
                            <div className="flex items-center justify-center gap-2 mt-2 text-slate-300">
                                <File className="w-4 h-4" />
                                <span>{selectedFile?.name}</span>
                                <span className="text-slate-500">({(selectedFile?.size / 1024 / 1024).toFixed(2)} MB)</span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {fileId && (
                <div className="glass-card p-6 space-y-6 animate-in fade-in zoom-in-95 duration-300">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-400 block">Page Range</label>
                            <div className="flex items-center gap-2">
                                <input
                                    type="number"
                                    min="1"
                                    value={config.startPage}
                                    onChange={e => setConfig({ ...config, startPage: parseInt(e.target.value) || 1 })}
                                    className="w-full"
                                />
                                <span className="text-slate-500">to</span>
                                <input
                                    type="number"
                                    min="1"
                                    value={config.endPage}
                                    onChange={e => setConfig({ ...config, endPage: parseInt(e.target.value) || 1 })}
                                    className="w-full"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-400 block">Difficulty</label>
                            <select
                                value={config.difficulty}
                                onChange={e => setConfig({ ...config, difficulty: e.target.value })}
                                className="w-full"
                            >
                                <option value="easy">Easy (Conceptual)</option>
                                <option value="medium">Medium (Standard)</option>
                                <option value="hard">Hard (Detailed)</option>
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-400 block">Cards Per Page</label>
                            <div className="flex items-center gap-4">
                                <input
                                    type="range"
                                    min="1"
                                    max="5"
                                    step="1"
                                    value={config.cardsPerPage}
                                    onChange={e => setConfig({ ...config, cardsPerPage: parseInt(e.target.value) })}
                                    className="flex-grow accent-indigo-500"
                                />
                                <span className="text-xl font-bold w-4 text-indigo-400">{config.cardsPerPage}</span>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={onGenerate}
                        className="w-full primary-button py-4 rounded-xl flex items-center justify-center gap-2 text-lg font-bold"
                    >
                        <Sparkles className="w-5 h-5 text-indigo-200" />
                        Generate Flashcards
                    </button>
                </div>
            )}
        </div>
    );
}
