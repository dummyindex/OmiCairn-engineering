import { render, screen } from '@testing-library/react';
import LoginByPasswordBox from '../src/pages/login/byPassword';
import '@testing-library/jest-dom';

test('renders login by password box', () => {
  render(<LoginByPasswordBox />);

  // Assert that the component renders without throwing any errors
  expect(screen.getByPlaceholderText('Enter your password')).toBeInTheDocument();
});

test('displays account input field', () => {
  render(<LoginByPasswordBox />);

  // Assert that the account input field is rendered
  expect(screen.getByPlaceholderText('Enter your account number')).toBeInTheDocument();
});
