

import React from 'react'
import { render } from '@testing-library/react'
import App from './App'
import test, { describe } from "node:test"

// Minimal smoke test to ensure the App mounts in a jsdom environment
// Docs:
// - React Testing Library example & APIs: https://testing-library.com/docs/react-testing-library/example-intro/
// - Vitest test environment (jsdom): https://vitest.dev/guide/environment

describe('App', () => {
  test('renders without crashing', () => {
    const { container } = render(<App />)
    // container is appended to document.body by default
    expect(container).toBeTruthy()
    expect(container.firstChild).not.toBeNull()
  })
})
