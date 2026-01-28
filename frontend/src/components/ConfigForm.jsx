import { Settings2, Layers, Cpu } from 'lucide-react'
import { motion } from 'framer-motion'

export function ConfigForm({ config, setConfig, disabled }) {
    const handleChange = (field, value) => {
        setConfig(prev => ({ ...prev, [field]: value }))
    }

    const inputClasses = "w-full p-4 rounded-2xl bg-white/50 dark:bg-jungle/30 border border-jungle/5 dark:border-lime/10 focus:border-lime focus:ring-4 focus:ring-lime/10 outline-none transition-all font-sans text-lg";

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 p-10 bg-black/5 dark:bg-white/5 rounded-[2rem] border border-jungle/5 dark:border-lime/5">
            <div className="space-y-4">
                <label className="flex items-center gap-3 text-sm font-bold tracking-widest uppercase text-jungle/60 dark:text-lime/60">
                    <Layers size={18} className="text-lime" />
                    Page Range
                </label>
                <div className="flex items-center gap-4">
                    <input
                        type="number"
                        min="1"
                        value={config.startPage}
                        onChange={(e) => handleChange('startPage', parseInt(e.target.value) || 1)}
                        disabled={disabled}
                        className={inputClasses}
                        placeholder="Start"
                    />
                    <span className="text-jungle/20 dark:text-lime/20 font-serif italic text-xl">to</span>
                    <input
                        type="number"
                        min="1"
                        value={config.endPage}
                        onChange={(e) => handleChange('endPage', parseInt(e.target.value) || 1)}
                        disabled={disabled}
                        className={inputClasses}
                        placeholder="End"
                    />
                </div>
            </div>

            <div className="space-y-4">
                <label className="flex items-center gap-3 text-sm font-bold tracking-widest uppercase text-jungle/60 dark:text-lime/60">
                    <Cpu size={18} className="text-lime" />
                    Mastery Depth
                </label>
                <div className="flex gap-3">
                    {['beginner', 'intermediate', 'advanced'].map((level) => (
                        <button
                            key={level}
                            type="button"
                            onClick={() => handleChange('difficulty', level)}
                            disabled={disabled}
                            className={`flex-1 py-4 px-2 rounded-2xl text-xs font-bold tracking-widest uppercase transition-all duration-300 ${config.difficulty === level
                                ? 'bg-jungle dark:bg-lime text-lime dark:text-jungle shadow-xl'
                                : 'bg-white/50 dark:bg-jungle/30 text-jungle/40 dark:text-lime/40 border border-jungle/5 dark:border-lime/10 hover:border-lime/30'
                                }`}
                        >
                            {level}
                        </button>
                    ))}
                </div>
            </div>

            <div className="space-y-6 md:col-span-2">
                <label className="flex items-center gap-3 text-sm font-bold tracking-widest uppercase text-jungle/60 dark:text-lime/60">
                    <Settings2 size={18} className="text-lime" />
                    Knowledge Density
                </label>
                <div className="flex flex-col gap-6">
                    <input
                        type="range"
                        min="1"
                        max="5"
                        step="1"
                        value={config.cardsPerPage}
                        onChange={(e) => handleChange('cardsPerPage', parseInt(e.target.value))}
                        disabled={disabled}
                        className="w-full h-1.5 bg-jungle/10 dark:bg-lime/10 rounded-full appearance-none cursor-pointer accent-lime"
                    />
                    <div className="flex justify-between items-center bg-white/50 dark:bg-jungle/30 p-6 rounded-2xl border border-jungle/5 dark:border-lime/10">
                        <div className="space-y-1">
                            <p className="font-serif font-medium text-lg">
                                {config.cardsPerPage} Flashcard{config.cardsPerPage > 1 ? 's' : ''} / Page
                            </p>
                            <p className="text-xs text-jungle/40 dark:text-lime/40 font-sans">
                                Optimized for high-retention learning.
                            </p>
                        </div>
                        <div className="w-12 h-12 flex items-center justify-center rounded-2xl bg-lime text-jungle font-serif font-bold text-xl shadow-lg ring-4 ring-lime/20">
                            {config.cardsPerPage}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
