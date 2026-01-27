import { Settings2, Layers, Cpu } from 'lucide-react'

export function ConfigForm({ config, setConfig, disabled }) {
    const handleChange = (field, value) => {
        setConfig(prev => ({ ...prev, [field]: value }))
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 bg-gray-50 dark:bg-gray-900/30 rounded-2xl border border-gray-200 dark:border-gray-700">
            <div className="space-y-4">
                <label className="flex items-center gap-2 text-sm font-bold text-gray-700 dark:text-gray-300">
                    <Layers size={18} className="text-indigo-500" />
                    Page Range
                </label>
                <div className="flex items-center gap-3">
                    <input
                        type="number"
                        min="1"
                        value={config.startPage}
                        onChange={(e) => handleChange('startPage', parseInt(e.target.value) || 1)}
                        disabled={disabled}
                        className="w-full p-3 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                        placeholder="Start"
                    />
                    <span className="text-gray-400">to</span>
                    <input
                        type="number"
                        min="1"
                        value={config.endPage}
                        onChange={(e) => handleChange('endPage', parseInt(e.target.value) || 1)}
                        disabled={disabled}
                        className="w-full p-3 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                        placeholder="End"
                    />
                </div>
            </div>

            <div className="space-y-4">
                <label className="flex items-center gap-2 text-sm font-bold text-gray-700 dark:text-gray-300">
                    <Cpu size={18} className="text-indigo-500" />
                    Difficulty Level
                </label>
                <div className="flex gap-2">
                    {['easy', 'medium', 'hard'].map((level) => (
                        <button
                            key={level}
                            type="button"
                            onClick={() => handleChange('difficulty', level)}
                            disabled={disabled}
                            className={`flex-1 py-3 px-2 rounded-xl text-xs font-bold capitalize transition-all ${config.difficulty === level
                                    ? 'bg-indigo-600 text-white shadow-md'
                                    : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 hover:border-indigo-300'
                                }`}
                        >
                            {level}
                        </button>
                    ))}
                </div>
            </div>

            <div className="space-y-4 md:col-span-2">
                <label className="flex items-center gap-2 text-sm font-bold text-gray-700 dark:text-gray-300">
                    <Settings2 size={18} className="text-indigo-500" />
                    Cards Per Page
                </label>
                <div className="flex items-center gap-4">
                    <input
                        type="range"
                        min="1"
                        max="5"
                        step="1"
                        value={config.cardsPerPage}
                        onChange={(e) => handleChange('cardsPerPage', parseInt(e.target.value))}
                        disabled={disabled}
                        className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                    />
                    <span className="w-10 h-10 flex items-center justify-center rounded-xl bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 font-bold">
                        {config.cardsPerPage}
                    </span>
                </div>
                <p className="text-xs text-gray-500 font-medium">
                    How many unique flashcards to generate for each page of the PDF.
                </p>
            </div>
        </div>
    )
}
