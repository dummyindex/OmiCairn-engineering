import type { ValidationRule } from '@/services/auth/types';

export const createPhoneValidators = (areaCode: string): ValidationRule<string>[] => {
  const baseValidators: ValidationRule<string>[] = [
    {
      validate: (value: string) => value.length > 0,
      message: 'Phone number is required',
    },
  ];

  // Country-agnostic check: national subscriber number of 4-14 digits (E.164 allows at most
  // 15 digits including the country calling code).
  const numberValidators: ValidationRule<string>[] = [
    {
      validate: (value: string) => /^\d{4,14}$/.test(value),
      message: 'Invalid phone number format',
    },
  ];

  return areaCode ? [...baseValidators, ...numberValidators] : baseValidators;
};

export const passwordValidators: ValidationRule<string>[] = [
  {
    validate: (value: string) => value.length > 0,
    message: 'Password is required',
  },
  {
    validate: (value: string) => value.length >= 8,
    message: 'Password must be at least 8 characters',
  },
  {
    validate: (value: string) => /[A-Z]/.test(value),
    message: 'Password must contain at least one uppercase letter',
  },
  {
    validate: (value: string) => /[a-z]/.test(value),
    message: 'Password must contain at least one lowercase letter',
  },
  {
    validate: (value: string) => /\d/.test(value),
    message: 'Password must contain at least one number',
  },
  {
    validate: (value: string) => /[!@#$%^&*(),.?":{}|<>]/.test(value),
    message: 'Password must contain at least one special character',
  },
];

export const areaCodeValidators: ValidationRule<string>[] = [
  {
    validate: (value: string) => /^\+\d{1,4}$/.test(value),
    message: 'Invalid area code',
  },
];
