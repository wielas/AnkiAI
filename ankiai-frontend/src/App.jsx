import React, { useState, useCallback } from 'react';
import { UploadSection } from './components/UploadSection';
import { ProgressSection } from './components/ProgressSection';
import { ResultsSection } from './components/ResultsSection';
import { ErrorDisplay } from './components/ErrorDisplay';
import { useWebSocket } from './hooks/useWebSocket';
import { FileStack } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  // State
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  // Configuration State
  const [config, setConfig] = useState({
    startPage: 1,
    endPage: 1,
    difficulty: 'medium',
    cardsPerPage: 1,
  });

  // Progress State from Hook
  const { progress, status, currentPage, totalPages, message, error: wsError } = useWebSocket(jobId);

  // Derived State
  const currentError = error || wsError;
  const isGenerating = status === 'processing' || status === 'idle' && jobId;
  const isCompleted = status === 'completed';

  // Handlers
  const handleUpload = async (file) => {
    setUploading(true);
    setError(null);
    setSelectedFile(file);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      const data = await response.json();
      setFileId(data.file_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleStartGeneration = async () => {
    if (!fileId) return;

    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate/${fileId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_page: config.startPage,
          end_page: config.endPage,
          difficulty: config.difficulty,
          cards_per_page: config.cardsPerPage,
        }),
      });

      if (!response.ok) throw new Error('Failed to start generation');

      const data = await response.json();
      setJobId(data.job_id);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setFileId(null);
    setJobId(null);
    setError(null);
    // Don't reset config usually, better UX to keep it
  };

  return (
    <div className="min-h-screen p-4 md:p-8 flex flex-col items-center">
      <header className="w-full max-w-4xl mb-12 text-center">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="p-3 bg-indigo-500 rounded-2xl shadow-lg shadow-indigo-500/20">
            <FileStack className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight">AnkiAI</h1>
        </div>
        <p className="text-slate-400 text-lg">Transform your PDFs into high-quality flashcards with AI</p>
      </header>

      <main className="w-full max-w-2xl">
        {currentError && (
          <ErrorDisplay
            message={currentError}
            onRetry={jobId ? handleStartGeneration : handleReset}
          />
        )}

        {!jobId && !isCompleted && (
          <UploadSection
            selectedFile={selectedFile}
            uploading={uploading}
            fileId={fileId}
            onUpload={handleUpload}
            onGenerate={handleStartGeneration}
            config={config}
            setConfig={setConfig}
          />
        )}

        {jobId && !isCompleted && !currentError && (
          <ProgressSection
            progress={progress}
            message={message}
            currentPage={currentPage}
            totalPages={totalPages}
          />
        )}

        {isCompleted && (
          <ResultsSection
            jobId={jobId}
            onReset={handleReset}
          />
        )}
      </main>

      <footer className="mt-auto pt-12 text-slate-500 text-sm">
        &copy; 2026 AnkiAI Flashcard Generator
      </footer>
    </div>
  );
}

export default App;
