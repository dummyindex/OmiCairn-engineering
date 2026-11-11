// import AddGeneDialog from '@/components/special/globalDialog/visualPanel/rightSiderBar/genesetAddDialog';
import style from './rightSiderBar/rightSider.less';
import Genesets from './rightSiderBar/genesets';
import SelectedCells from './rightSiderBar/selectedCells';
import CellsetsBar from './rightSiderBar/cellsets';

const RightSider = () => {
  return (
    <div className={style.rightSider}>
      <CellsetsBar />
      <Genesets />
      <SelectedCells />
    </div>
  );
};

export default RightSider;
