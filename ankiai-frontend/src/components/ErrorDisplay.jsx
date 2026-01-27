import React from 'react';
import { AlertCircle, RefreshCcw } from 'lucide-react';

export function ErrorDisplay({ message, onRetry }) {
    return (
        <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-6 mb-8 flex items-start gap-4 animate-in shake duration-500">
            <div className="p-2 bg-red-500/20 rounded-lg">
                <AlertCircle className="w-6 h-6 text-red-500" />
            </div>
            <div className="flex-grow">
                <h3 className="text-lg font-bold text-red-400">Something went wrong</h3>
                <p className="text-red-200/80 mt-1">{message}</p>
                <button
                    onClick={onRetry}
                    className="mt-4 flex items-center gap-2 text-sm font-medium text-red-400 hover:text-red-300 transition-colors"
                >
                    <RefreshCcw className="w-4 h-4" />
                    Try again
                </button>
            </div>
        </div>
    );
}
