export type LoginCredentials = {
  phoneNumber: string;
  password: string;
  areaCode: string;
};

export type AuthTokens = {
  accessToken: string;
  refreshToken: string;
};

export type LoginResponse = {
  code: number;
  data: AuthTokens;
  message?: string;
};

export type DecodedToken = {
  userId: string;
  exp: number;
  permissions: string[];
};

export type UserInfo = {
  id: string;
  userName: string;
  phoneNumber: string;
  createdAt: string;
  updatedAt: string;
};

export type ValidationRule<T> = {
  validate: (value: T) => boolean;
  message: string;
};

export type FieldValidation<T> = {
  value: T;
  rules: ValidationRule<T>[];
  isValid: boolean;
  error: string;
  isTouched: boolean;
};

export type LoginFormState = {
  phoneNumber: FieldValidation<string>;
  password: FieldValidation<string>;
  areaCode: FieldValidation<string>;
};

export type ValidationResult = {
  isValid: boolean;
  error: string;
};
