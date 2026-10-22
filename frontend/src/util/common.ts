export const flatDict = (inflatDict: any) => {
  const allKeys = Object.keys(inflatDict);
  for (const key of allKeys) {
    const value = inflatDict[key];
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      const keys = Object.keys(value);
      for (const k of keys) {
        inflatDict[`${key}.${k}`] = value[k];
      }
      delete inflatDict[key];
    }
  }
  return inflatDict;
};

export const getUuid = () => {
  let random: number;
  let uuid = '';
  for (let i = 0; i < 32; i++) {
    random = (Math.random() * 16) | 0; // random hex digit 0-15
    if (i === 8 || i === 12 || i === 16 || i === 20) {
      // insert hyphens at the UUID group boundaries
      uuid += '-';
    }
    uuid += (i === 12 ? 4 : i === 16 ? (random & 3) | 8 : random).toString(16); // version nibble = 4; variant bits = 10xx
  }
  return uuid;
};

export const createImageWithPromise = (
  uri: string,
  width: number | undefined,
  height: number | undefined,
  extraAttribute: any = {},
) =>
  new Promise((resolve) => {
    const image = new Image(width, height);
    if (extraAttribute) {
      Object.keys(extraAttribute).forEach((extraAttributeKey) => {
        const extraAttributeValue = extraAttribute[extraAttributeKey];
        image.setAttribute(extraAttributeKey, extraAttributeValue);
      });
    }
    image.src = uri;
    image.onload = () => {
      resolve(image);
    };
  });

export const combinedImagesByOffsetAndSizeInfo = async (uriInformationList: any[]) => {
  const canvas = document.createElement('canvas');
  let canvasWidth = Number.MIN_VALUE;
  let canvasHeight = Number.MIN_VALUE;
  const context = canvas.getContext('2d');
  if (!context) {
    throw Error('created context is null when combined images');
  }
  const imagePromiseList = uriInformationList.map((uriInformation) => {
    const { uri, width, height, offsetX, offsetY } = uriInformation;
    canvasWidth = canvasWidth > offsetX + width ? canvasWidth : offsetX + width;
    canvasHeight = canvasHeight > offsetY + height ? canvasHeight : offsetY + height;
    return createImageWithPromise(uri, width, height, {
      offsetXOnCanvas: offsetX,
      offsetYOnCanvas: offsetY,
      widthOnCanvas: width,
      heightOnCanvas: height,
    });
  });
  canvas.width = canvasWidth;
  canvas.height = canvasHeight;
  const imageElementList = await Promise.all(imagePromiseList);
  imageElementList.forEach((imageElement: any) => {
    const offsetX = imageElement.getAttribute('offsetXOnCanvas');
    const offsetY = imageElement.getAttribute('offsetYOnCanvas');
    const width = imageElement.getAttribute('widthOnCanvas');
    const height = imageElement.getAttribute('heightOnCanvas');
    context.drawImage(imageElement, offsetX, offsetY, width, height);
  });
  const result = canvas.toDataURL('image/png');
  return result;
};

// Current time expressed in the backend's timezone (UMI_APP_SERVER_TIMEZONE, default UTC).
export const getServerTime = () => {
  const now = new Date();
  const options = {
    timeZone: process.env.UMI_APP_SERVER_TIMEZONE || 'UTC',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false, // use 24-hour clock
    hourCycle: 'h23', // force the 24-hour cycle (00-23)
    timeZoneName: 'short', // time-zone name can be shown if needed; not displayed here
  };
  let serverTimeFormatted = new Intl.DateTimeFormat('en-US', options).format(now);
  // convert hour 24 to 00
  // // extract the hour from the string
  const hour = serverTimeFormatted.slice(12, 14);
  // // convert the hour string to a number
  const hourNum = parseInt(hour);
  // // if the hour is 24, convert it to 0
  if (hourNum === 24) {
    serverTimeFormatted =
      serverTimeFormatted.slice(0, 12) + '00' + serverTimeFormatted.slice(14);
  }
  return new Date(serverTimeFormatted);
};

export const generateSequence = (start: number, end: number, step: number = 1) => {
  const sequence: number[] = [];
  for (let i = start; i <= end; i += step) {
    sequence.push(i);
  }
  return sequence;
};

// Utility to compute interaction duration
export const calculateInteractionDuration = (interaction): number => {
  if (interaction.start_time && interaction.end_time) {
    return interaction.end_time - interaction.start_time;
  }
  return 0;
};

// Format a duration as a human-readable string
export const formatDuration = (durationMs: number): string => {
  if (durationMs <= 0) return '--';

  const seconds = Math.floor(durationMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
};
