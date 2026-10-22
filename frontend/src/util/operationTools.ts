export const writeToClipboard = (text: string) => {
  if (!navigator.clipboard) {
    return new Promise((resolve, reject) => {
      try {
        const input = document.createElement('textarea');
        input.style.position = 'fixed';
        input.style.opacity = '0';
        input.value = text;
        document.body.appendChild(input);
        input.select();
        document.execCommand('Copy');
        document.body.removeChild(input);
        resolve(null);
      } catch (error) {
        reject(error);
      }
    });
  } else {
    return navigator.clipboard.writeText(text);
  }
};
