import React from 'react';
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders the placeholder root without crashing', () => {
    const { container } = render(<App />);

    expect(container).toBeTruthy();
    expect(container.innerHTML).toBe('');
  });
});
