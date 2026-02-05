import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import { ConfigForm } from '../ConfigForm'

describe('ConfigForm', () => {
    const defaultConfig = {
        startPage: 1,
        endPage: 5,
        difficulty: 'intermediate',
        cardsPerPage: 3
    }

    it('renders all configuration fields', () => {
        render(<ConfigForm config={defaultConfig} setConfig={vi.fn()} disabled={false} />)

        expect(screen.getByText(/Page Range/i)).toBeInTheDocument()
        expect(screen.getByText(/Mastery Depth/i)).toBeInTheDocument()
        expect(screen.getByText(/Knowledge Density/i)).toBeInTheDocument()

        expect(screen.getByDisplayValue('1')).toBeInTheDocument()
        expect(screen.getByDisplayValue('5')).toBeInTheDocument()
    })

    it('calls setConfig when difficulty is changed', () => {
        const setConfig = vi.fn()
        render(<ConfigForm config={defaultConfig} setConfig={setConfig} disabled={false} />)

        const advancedBtn = screen.getByText('advanced')
        fireEvent.click(advancedBtn)

        expect(setConfig).toHaveBeenCalled()
    })

    it('disables inputs when disabled prop is true', () => {
        render(<ConfigForm config={defaultConfig} setConfig={vi.fn()} disabled={true} />)

        const inputs = screen.getAllByRole('spinbutton')
        inputs.forEach(input => expect(input).toBeDisabled())

        const buttons = screen.getAllByRole('button')
        buttons.forEach(btn => expect(btn).toBeDisabled())
    })
})
