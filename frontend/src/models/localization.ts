import { EnglishDictionary } from '@/dictionaries/en';

// ------------------------------------------------------

// The UI is English-only; changeLanguage is kept as a no-op for API compatibility.
const useLocalization = () => {
  const language = 'en';
  const dictionary = EnglishDictionary;

  const changeLanguage = (_language?: string) => {};

  return {
    language,
    dictionary,
    changeLanguage,
  };
};

export default useLocalization;
