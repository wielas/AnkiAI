import React, { useState } from 'react';
import { Download, CheckCircle2, RefreshCw, Loader2 } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

export function ResultsSection({ jobId, onReset }) {
    const [downloading, setDownloading] = useState(false);

    const handleDownload = async () => {
        setDownloading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/download/${jobId}`);
            if (!response.ok) throw new Error('Download failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `flashcards-${jobId.slice(0, 8)}.apkg`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (err) {
            console.error(err);
            alert('Failed to download file. Please try again.');
        } finally {
            setDownloading(false);
        }
    };

    return (
        <div className="glass-card p-10 text-center space-y-8 animate-in fade-in zoom-in-95 duration-500">
            <div className="mx-auto w-20 h-20 bg-emerald-500/20 rounded-3xl flex items-center justify-center animate-bounce">
                <CheckCircle2 className="w-10 h-10 text-emerald-500" />
            </div>

            <div className="space-y-2">
                <h2 className="text-3xl font-bold text-white">Generation Complete!</h2>
                <p className="text-slate-400">Your Anki deck is ready for import.</p>
            </div>

            <div className="flex flex-col gap-4">
                <button
                    onClick={handleDownload}
                    disabled={downloading}
                    className="primary-button py-4 rounded-xl flex items-center justify-center gap-3 text-lg font-bold w-full"
                >
                    {downloading ? (
                        <Loader2 className="w-6 h-6 animate-spin" />
                    ) : (
                        <Download className="w-6 h-6" />
                    )}
                    {downloading ? 'Downloading...' : 'Download .apkg File'}
                </button>

                <button
                    onClick={onReset}
                    className="flex items-center justify-center gap-2 text-slate-400 hover:text-white transition-colors py-2"
                >
                    <RefreshCw className="w-4 h-4" />
                    Generate more flashcards
                </button>
            </div>
        </div>
    );
}
