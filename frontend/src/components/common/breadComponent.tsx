import { useRef } from 'react';

// const SEGMENT = 50;

export const BreadComponent = (props: any) => {
  const selectedsetRef = useRef<HTMLInputElement>(null!);
  const { boxWidth, selectedList, deletedSelected } = props;

  const deleteSet = (value: string) => () => {
    deletedSelected(value);
  };

  // const [showedList, setShowedList] = useState(new DataCol());
  // const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);

  // const [showedCount, setShowedCount] = useState(SEGMENT);

  // const list = Object.keys(selectedList);

  // const loadMoreData = () => {
  //   const moreList = showedList.concat(
  //     list.slice(showedList.getLength() - 1, showedList.getLength() - 1 + SEGMENT),
  //   );
  //   setShowedList(moreList);
  //   setShowedCount(showedCount + SEGMENT);
  // };

  return (
    <div
      style={{
        marginBottom: '5px',
        display: 'flex',
        flexWrap: 'wrap',
      }}
      onClick={(e) => {
        e.stopPropagation();
      }}
    >
      <div
        style={{
          width: '100%',
          height: '10vh',
          background: '#f1f3f4',
          overflow: 'auto',
        }}
        // onScroll={(e: any) => {
        //   // scroll height
        //   const scrollTop = e.target.scrollTop;

        //   // child element height
        //   const childClientHeight = e.target.children[0].children[0].clientHeight;

        //   // visible area height
        //   const clientHeight = e.target.clientHeight;

        //   if (scrollTop + clientHeight + 10 >= childClientHeight) {
        //     if (timer) {
        //       clearTimeout(timer);
        //     }
        //     setTimer(
        //       setTimeout(() => {
        //         loadMoreData();
        //       }, 500),
        //     );
        //   }
        // }}
      >
        <div
          style={{
            marginBottom: '1vh',
            display: 'flex',
            flexWrap: 'wrap',
          }}
        >
          {Array.from(Object.keys(selectedList)).map((item) => (
            <div
              key={item}
              style={{
                background: 'rgb(89, 126, 247)',
                width: `${boxWidth}vw`,
                display: 'flex',
                paddingLeft: '0.3vw',
                margin: '0.3vh 0.3vw 0',
                borderRadius: '5px',
                color: 'white',
              }}
            >
              <div
                style={{
                  width: `${boxWidth - 1}vw`,
                  height: '3vh',
                  lineHeight: '3vh',
                  overflow: 'hidden',
                  whiteSpace: 'nowrap',
                  textOverflow: 'ellipsis',
                }}
              >
                {item}
              </div>
              <div
                style={{
                  width: '1vw',
                  height: '3vh',
                  lineHeight: '3vh',
                  cursor: 'pointer',
                }}
                onClick={deleteSet(item)}
              >
                ×
              </div>
            </div>
          ))}
          <div
            ref={selectedsetRef}
            style={{
              clear: 'both',
            }}
          />
          <div />
        </div>
      </div>
    </div>
  );
};
