import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders What can I do for your research? heading', () => {
  render(<App />);
  const headingElement = screen.getByText(/What can I do for your research?/i);
  expect(headingElement).toBeInTheDocument();
});
