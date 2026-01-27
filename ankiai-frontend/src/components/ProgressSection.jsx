import React from 'react';
import { Loader2 } from 'lucide-react';

export function ProgressSection({ progress, message, currentPage, totalPages }) {
    const percentage = Math.round(progress * 100);

    return (
        <div className="glass-card p-10 space-y-8 text-center animate-in fade-in zoom-in-95 duration-500">
            <div className="relative w-32 h-32 mx-auto">
                <svg className="w-full h-full" viewBox="0 0 100 100">
                    <circle
                        className="text-slate-800 stroke-current"
                        strokeWidth="8"
                        fill="transparent"
                        r="40"
                        cx="50"
                        cy="50"
                    />
                    <circle
                        className="text-indigo-500 stroke-current transition-all duration-500 ease-out"
                        strokeWidth="8"
                        strokeDasharray={2 * Math.PI * 40}
                        strokeDashoffset={2 * Math.PI * 40 * (1 - progress)}
                        strokeLinecap="round"
                        fill="transparent"
                        r="40"
                        cx="50"
                        cy="50"
                    />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-3xl font-bold">{percentage}%</span>
                </div>
            </div>

            <div className="space-y-4">
                <h2 className="text-2xl font-bold text-white flex items-center justify-center gap-3">
                    <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
                    Processing Document
                </h2>

                <div className="space-y-2">
                    <p className="text-indigo-400 font-medium text-lg">{message || 'Starting AI processing...'}</p>
                    {currentPage && totalPages && (
                        <p className="text-slate-500">Page {currentPage} of {totalPages}</p>
                    )}
                </div>

                <div className="w-full bg-slate-800 rounded-full h-2 mt-6 overflow-hidden">
                    <div
                        className="bg-indigo-500 h-full transition-all duration-500 ease-out"
                        style={{ width: `${percentage}%` }}
                    />
                </div>
            </div>

            <p className="text-slate-400 text-sm">
                Generating high-quality flashcards takes a moment.
                You can keep this window open or come back later.
            </p>
        </div>
    );
}
