import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import { FilePreview } from '../FilePreview'
import { ErrorDisplay } from '../ErrorDisplay'

describe('FilePreview', () => {
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })

    it('renders file information correctly', () => {
        render(<FilePreview file={file} onRemove={vi.fn()} />)
        expect(screen.getByText('test.pdf')).toBeInTheDocument()
        expect(screen.getByText(/7 Bytes/i)).toBeInTheDocument()
    })

    it('calls onRemove when remove button is clicked', () => {
        const onRemove = vi.fn()
        render(<FilePreview file={file} onRemove={onRemove} />)
        const removeBtn = screen.getByTitle('Remove file')
        fireEvent.click(removeBtn)
        expect(onRemove).toHaveBeenCalled()
    })
})

describe('ErrorDisplay', () => {
    it('renders error message', () => {
        render(<ErrorDisplay message="Something went wrong" onClose={vi.fn()} />)
        expect(screen.getByText('Something went wrong')).toBeInTheDocument()
        expect(screen.getByText(/Process Disturbance/i)).toBeInTheDocument()
    })

    it('calls onClose when close button is clicked', () => {
        const onClose = vi.fn()
        render(<ErrorDisplay message="Error" onClose={onClose} />)
        const closeBtn = screen.getByRole('button')
        fireEvent.click(closeBtn)
        expect(onClose).toHaveBeenCalled()
    })
})
