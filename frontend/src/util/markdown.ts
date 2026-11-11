type ReportContentSection = {
  type: 'markdown' | 'figure';
  content: string;
  nodeId?: string;
  nodeName?: string;
  alt?: string;
};

export const processFigurePlaceholders = async (
  markdownContent: string,
  zip: any,
): Promise<ReportContentSection[]> => {
  const figurePlaceholderRegex = /\[Figure\s+(\d+),\s*([^,]+),\s*([^\]]+)\]/gi;

  const figureFiles = Object.keys(zip.files).filter(
    (filename) => filename.startsWith('figures/') && /\.(png|jpg|jpeg|gif|svg)$/i.test(filename),
  );

  const matches: {
    fullMatch: string;
    figureNum: string;
    nodeName: string;
    description: string;
    startIndex: number;
    endIndex: number;
  }[] = [];
  let match;
  while ((match = figurePlaceholderRegex.exec(markdownContent)) !== null) {
    matches.push({
      fullMatch: match[0],
      figureNum: match[1],
      nodeName: match[2].trim(),
      description: match[3].trim(),
      startIndex: match.index,
      endIndex: match.index + match[0].length,
    });
  }

  const sections: ReportContentSection[] = [];
  let currentIndex = 0;

  for (const matchInfo of matches) {
    if (matchInfo.startIndex > currentIndex) {
      let markdownSection = markdownContent.substring(currentIndex, matchInfo.startIndex);

      markdownSection = markdownSection.replace(/^\s*-\s*$/gm, '');

      if (markdownSection.trim()) {
        sections.push({
          type: 'markdown' as const,
          content: markdownSection,
        });
      }
    }

    const { figureNum, nodeName } = matchInfo;

    let matchingFigure = figureFiles.find((filename) => {
      const fileBaseName = filename.split('/').pop() || '';
      return fileBaseName.toLowerCase().startsWith(`figure_${figureNum}_`);
    });

    if (!matchingFigure) {
      matchingFigure = figureFiles.find((filename) => {
        const fileBaseName = filename.split('/').pop() || '';
        return fileBaseName.toLowerCase().includes(`figure_${figureNum}`);
      });
    }

    if (!matchingFigure && parseInt(figureNum) <= figureFiles.length) {
      const sortedFiles = figureFiles.sort();
      matchingFigure = sortedFiles[parseInt(figureNum) - 1];
    }

    if (matchingFigure) {
      try {
        const imageBlob = await zip.file(matchingFigure)?.async('blob');

        if (imageBlob) {
          const arrayBuffer = await imageBlob.arrayBuffer();
          const base64 = btoa(
            new Uint8Array(arrayBuffer).reduce(
              (data, byte) => data + String.fromCharCode(byte),
              '',
            ),
          );
          const mimeType = imageBlob.type || 'image/png';
          const dataUrl = `data:${mimeType};base64,${base64}`;

          sections.push({
            type: 'figure' as const,
            content: dataUrl,
            nodeId: undefined,
            nodeName: nodeName || undefined,
            alt: matchInfo.description || `Figure ${figureNum}`,
          });
        } else {
          sections.push({
            type: 'markdown' as const,
            content: `\n\n*[Figure ${figureNum} - Image not available]*\n\n`,
          });
        }
      } catch (error) {
        console.error(`Error processing figure ${figureNum}:`, error);
        sections.push({
          type: 'markdown' as const,
          content: `\n\n*[Figure ${figureNum} - Image not available]*\n\n`,
        });
      }
    } else {
      sections.push({
        type: 'markdown' as const,
        content: `\n\n*[Figure ${figureNum}, ${nodeName} - Figure not found]*\n\n`,
      });
    }

    currentIndex = matchInfo.endIndex;
  }

  if (currentIndex < markdownContent.length) {
    let remainingContent = markdownContent.substring(currentIndex);

    remainingContent = remainingContent.replace(/^\s*-\s*$/gm, '');

    if (remainingContent.trim()) {
      sections.push({
        type: 'markdown' as const,
        content: remainingContent,
      });
    }
  }

  if (sections.length === 0) {
    sections.push({
      type: 'markdown' as const,
      content: markdownContent,
    });
  }

  return sections;
};
