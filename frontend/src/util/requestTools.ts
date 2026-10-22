import { StaticResourceBaseUrl } from '@/constants';

export const generateStaticResourceUrl = (filename: string) =>
  `${StaticResourceBaseUrl.replace(/\/$/, '')}/${filename}`;

export const generateStaticResourceUrls = (filenames: string[]) =>
  filenames.map((filename: string) => generateStaticResourceUrl(filename));
