import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

test('renders app title', () => {
  render(<App />);
  const titleElement = screen.getByText(/Content Classification System/i);
  expect(titleElement).toBeInTheDocument();
});
