export const formatTimeTool = (data: any) => {
  let _data = data;
  if (String(data).length === 13) {
    _data = data;
  } else {
    _data = data * 1000;
  }
  const time = new Date(_data);
  const Y = time.getFullYear();
  const Mon = time.getMonth() + 1 < 10 ? `0${time.getMonth() + 1}` : time.getMonth() + 1;
  const Day = time.getDate() < 10 ? `0${time.getDate()}` : time.getDate();
  const H = time.getHours() < 10 ? `0${time.getHours()}` : time.getHours();
  const Min = time.getMinutes() < 10 ? `0${time.getMinutes()}` : time.getMinutes();
  const S = time.getSeconds() < 10 ? `0${time.getSeconds()}` : time.getSeconds();
  return `${Y}-${Mon}-${Day} ${H}:${Min}:${S}`;
};
