export const cutString = (originString: string, lengthLimited: number) => {
  let newString = '';
  if (!originString) {
    return newString;
  }
  if (originString[lengthLimited]) {
    newString = `${originString.substr(0, lengthLimited)}...`;
  } else {
    newString = originString;
  }
  return newString;
};

export const cutStringByCharType = (
  originString: string,
  wideCharLimit: number = 16,
  latinLimit: number = 22,
) => {
  if (!originString) {
    return '';
  }

  // Strings containing CJK unified ideographs (U+4E00-U+9FA5) render wider, so use a shorter limit.
  const hasWideChars = /[\u4e00-\u9fa5]/.test(originString);
  const lengthLimit = hasWideChars ? wideCharLimit : latinLimit;

  if (originString.length > lengthLimit) {
    return `${originString.substring(0, lengthLimit)}...`;
  }

  return originString;
};
