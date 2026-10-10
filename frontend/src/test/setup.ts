import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Vitest globals are off, so RTL can't register its own cleanup. Do it here so DOM doesn't leak between tests.
afterEach(() => {
  cleanup()
})
