import { useState, useEffect, useRef } from 'react';

type Tab = {
  key: string;
  label: string;
};

const CustomTabSwitch = ({ tabs, activeKey, onChange }) => {
  const boxRef = useRef(null);
  const itemRefs = useRef({});
  const [sliderStyle, setSliderStyle] = useState({
    width: 0,
    left: 0,
  });

  useEffect(() => {
    const activeItem = itemRefs.current[activeKey];
    if (activeItem && boxRef.current) {
      const { offsetLeft: boxLeft } = boxRef.current;

      const { width, left } = activeItem.getBoundingClientRect();
      setSliderStyle({
        width: width,
        left: left - boxLeft,
      });
    }
  }, [activeKey, tabs]);

  return (
    <div
      style={{
        height: '100%',
      }}
      ref={boxRef}
    >
      <div
        style={{
          height: '4.5vh',
          display: 'flex',
          justifyContent: 'center',
          gap: '1.5em',
          fontSize: '1.5vh',
        }}
      >
        {tabs.map((tab: Tab) => {
          const active = tab.key === activeKey;
          return (
            <div
              key={tab.key}
              ref={(el) => (itemRefs.current[tab.key] = el)}
              style={{
                color: active ? '#000' : '#000',
                cursor: 'pointer',
                fontSize: '1.1em',
                fontWeight: active ? '600' : '400',
              }}
              onClick={() => {
                onChange(tab.key);
              }}
            >
              {tab.label}
            </div>
          );
        })}
      </div>
      <div
        style={{
          height: '1px',
        }}
      >
        <div
          style={{
            width: sliderStyle.width,
            height: '1px',
            backgroundColor: '#2368fd',
            transform: `translateX(${sliderStyle.left}px)`,
            transition: 'transform 0.3s',
          }}
        />
      </div>
    </div>
  );
};

export default CustomTabSwitch;
