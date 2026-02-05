import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import { FileDropzone } from '../FileDropzone'

describe('FileDropzone', () => {
    it('renders the dropzone area', () => {
        render(<FileDropzone onFileSelect={vi.fn()} uploading={false} />)
        expect(screen.getByText(/Deep dive into your PDF/i)).toBeInTheDocument()
        expect(screen.getByText(/Drag & drop or click to explore/i)).toBeInTheDocument()
    })

    it('renders the file input', () => {
        const { container } = render(<FileDropzone onFileSelect={vi.fn()} uploading={false} />)
        const input = container.querySelector('input[type="file"]')
        expect(input).toBeInTheDocument()
    })
})
