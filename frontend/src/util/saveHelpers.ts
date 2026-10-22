export const downloadImageWithBase64 = (base64Url, fileName = 'unname') => {
  const a = document.createElement('a');
  const event = new MouseEvent('click');
  a.download = fileName;
  a.href = base64Url;
  a.dispatchEvent(event);
};

export const downloadText = (text: string, fileName: string, otherOptions: any = {}) => {
  const initOptions = {
    type: 'text/plain',
  };
  const blob = new Blob([text], {
    ...initOptions,
    ...otherOptions,
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(url);
};

export const downloadJsonText = (json: any, fileName: string) => {
  let _json: any = json;
  if (typeof _json === 'string') {
    _json = JSON.parse(_json);
  }
  const text = JSON.stringify(_json, null, 2);
  downloadText(text, `${fileName}.json`, { type: 'application/json' });
};
