import { useState, useCallback, useMemo } from 'react';
import type { FieldValidation, ValidationRule } from '@/services/auth/types';
import { debounce } from 'lodash';

export function useFormValidation<T extends Record<string, any>>(
  initialState: Record<keyof T, FieldValidation<any>>,
  onValidationComplete?: (isValid: boolean) => void,
) {
  const [formState, setFormState] = useState(initialState);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateField = useCallback(
    (fieldName: keyof T, value: any, rules: ValidationRule<any>[]) => {
      for (const rule of rules) {
        if (!rule.validate(value)) {
          return {
            isValid: false,
            error: rule.message,
          };
        }
      }
      return {
        isValid: true,
        error: '',
      };
    },
    [],
  );

  const debouncedValidation = useMemo(
    () =>
      debounce((fieldName: keyof T, value: any, rules: ValidationRule<any>[]) => {
        const validationResult = validateField(fieldName, value, rules);
        setFormState((prev) => ({
          ...prev,
          [fieldName]: {
            ...prev[fieldName],
            isValid: validationResult.isValid,
            error: validationResult.error,
          },
        }));
      }, 300),
    [validateField],
  );

  const handleFieldChange = useCallback(
    (fieldName: keyof T, value: any) => {
      setFormState((prev) => ({
        ...prev,
        [fieldName]: {
          ...prev[fieldName],
          value,
          isTouched: true,
        },
      }));

      debouncedValidation(fieldName, value, formState[fieldName].rules);
    },
    [formState, debouncedValidation],
  );

  const validateForm = useCallback(() => {
    const newFormState = { ...formState };
    let isValid = true;

    for (const fieldName in formState) {
      const field = formState[fieldName];
      const validationResult = validateField(fieldName, field.value, field.rules);

      newFormState[fieldName] = {
        ...field,
        isValid: validationResult.isValid,
        error: validationResult.error,
        isTouched: true,
      };

      if (!validationResult.isValid) {
        isValid = false;
      }
    }

    setFormState(newFormState);
    onValidationComplete?.(isValid);
    return isValid;
  }, [formState, validateField, onValidationComplete]);

  const resetForm = useCallback(() => {
    setFormState(initialState);
    setIsSubmitting(false);
  }, [initialState]);

  const getFieldProps = useCallback(
    (fieldName: keyof T) => ({
      value: formState[fieldName].value,
      onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
        handleFieldChange(fieldName, e.target.value),
      onBlur: () =>
        setFormState((prev) => ({
          ...prev,
          [fieldName]: {
            ...prev[fieldName],
            isTouched: true,
          },
        })),
      status: formState[fieldName].isTouched && !formState[fieldName].isValid ? 'error' : '',
    }),
    [formState, handleFieldChange],
  );

  return {
    formState,
    isSubmitting,
    setIsSubmitting,
    handleFieldChange,
    validateForm,
    resetForm,
    getFieldProps,
  };
}
