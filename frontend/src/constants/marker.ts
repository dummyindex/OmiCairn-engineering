type ConstantDictionary = Record<string, string>;

export const ChartsMarkerType: ConstantDictionary = {
  ARROWS: 'arrows',
  CIRCLES: 'circles',
  ROUNDRECT: 'roundRect',
  SQUARES: 'squares',
  DIAMONDS: 'diamonds',
  TRIANGLES: 'triangles',
};

export const MarkerMenuItems = Object.keys(ChartsMarkerType).map((key: string) => {
  return {
    key,
    label: ChartsMarkerType[key],
    value: ChartsMarkerType[key],
  };
});
