import { Dropdown, Popover } from 'antd';
import { generateStaticResourceUrl } from '@/util/requestTools';

const CustomImage = ({ name, className, style, onClick, dropdownMenu, popoverContent }: any) => {
  const src = generateStaticResourceUrl(name);

  const imageElement = (
    <img
      src={src}
      alt="item icon load failure"
      className={className}
      style={style}
      onClick={onClick ? onClick : () => {}}
    />
  );

  if (dropdownMenu) {
    return (
      <Dropdown overlay={dropdownMenu} trigger={['hover']}>
        {imageElement}
      </Dropdown>
    );
  }

  if (popoverContent) {
    return (
      <Popover content={popoverContent} trigger="hover">
        {imageElement}
      </Popover>
    );
  }

  return imageElement;
};

export default CustomImage;
