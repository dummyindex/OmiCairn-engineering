export const computeContrastColor = (r, g, b) => {
  const yiq = (r * 299 + g * 587 + b * 114) / 1000;
  return yiq >= 128 ? 'rgba(50,50,50,1)' : 'rgba(255,255,255,1)';
};
