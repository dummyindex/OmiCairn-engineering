import { BgColorsOutlined, FontSizeOutlined, QuestionOutlined } from '@ant-design/icons';

// Small icon set used by the cell-visualization toolbars. Previously loaded from a hosted
// iconfont project; now mapped to bundled @ant-design/icons so no external CDN is needed.
const iconMap: Record<string, any> = {
  'icon-text': FontSizeOutlined,
  'icon-drop': BgColorsOutlined,
};

export const ExtraIcon = ({ type, ...rest }: { type: string; [key: string]: any }) => {
  const Icon = iconMap[type] || QuestionOutlined;
  return <Icon {...rest} />;
};
