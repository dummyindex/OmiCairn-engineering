import { useEffect, useState, useRef } from 'react';
import { Form, Input, InputNumber, Switch, Modal, Row, Col, Button } from 'antd';
import { ParamsRenderType } from '@/constants/functionBlock';
import { InfoCircleOutlined } from '@ant-design/icons';
import parameterBoxStyle from './parameterBox.less';

import AdataLayerKey from '@/components/highReuse/extraParameter/adataLayerKey';
import AdataObsGroup from '@/components/highReuse/extraParameter/adataObsGroup';
import AdataObsGroupList from '@/components/highReuse/extraParameter/adataObsGroupList';
import AdataObsKey from '@/components/highReuse/extraParameter/adataObsKey';
import AdataObsKeyList from '@/components/highReuse/extraParameter/adataObsKeyList';
import AdataObsmKey from '@/components/highReuse/extraParameter/adataObsmlKey';
import AdataUnsKey from '@/components/highReuse/extraParameter/adataUnsKey';
import AdataVarKey from '@/components/highReuse/extraParameter/adataVarKey';
import DataSelecter from '@/components/highReuse/extraParameter/dataSelecter';
import LibrarySelector from '@/components/highReuse/extraParameter/librarySelector/librarySelector';
import OrganismSelector from '@/components/highReuse/extraParameter/organismSelector';
import SingleCellSelector from '@/components/highReuse/extraParameter/singleCellSelector';
import SingleGeneSelector from '@/components/highReuse/extraParameter/singleGeneSelector';
import StrMultipleOptions from '@/components/highReuse/extraParameter/strMultipleOptions';
import StrOptions from '@/components/highReuse/extraParameter/strOptions';
import StrRadio from '@/components/highReuse/extraParameter/strRadio';

import ParamFileInput from '@/components/highReuse/extraParameter/paramFileInput';
import AdataVarKeyList from '@/components/highReuse/extraParameter/adataVarKeyList';

import CellsSelector from '@/components/highReuse/extraParameter/cellsSelector';
import GenesSelector from '@/components/highReuse/extraParameter/genesSelector';
import ListInput, { ElementType } from '@/components/highReuse/extraParameter/listInput';
import AdataObspKey from './extraParameter/adataObspKey';
import DictInput from './extraParameter/dictInput';
import AdataListInput from './extraParameter/adataListInput';
import AdataInput from './extraParameter/adataInput';
import APIKeyInput from './extraParameter/apiKeyInput';

const DescriptionModal = (props) => {
  const { description, setDescription } = props;

  return (
    <Modal
      title="Description"
      open={!!description}
      onCancel={() => {
        setDescription(null);
      }}
      cancelText="Close"
      okButtonProps={{ style: { display: 'none' } }}
      centered
    >
      {description}
    </Modal>
  );
};

const ParamLabel = (props) => {
  const { name, onDetailShow, isRecommended } = props;
  return (
    <div
      className={parameterBoxStyle.paramLabel}
      onClick={(e) => {
        e.stopPropagation();
      }}
    >
      <div className={parameterBoxStyle.paramName}>
        {name}
        {isRecommended && (
          <div
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              // Gradient, top to bottom, white to blue
              background: 'radial-gradient(circle at center top , #aaf,  #0011ff)',
              position: 'absolute',
              top: '0px',
              right: '0px',
            }}
          />
        )}
      </div>{' '}
      <Button
        size="small"
        type="text"
        icon={
          <InfoCircleOutlined
            style={{
              color: '#999',
            }}
          />
        }
        onClick={(e) => {
          e.stopPropagation();
          onDetailShow();
        }}
      />
    </div>
  );
};

export const FBParameterForm = (props: any) => {
  const { paramsList, dataStructure, nodeId, layout, disabled, form, recommendedParamDict } = props;
  const organismFormItemRef = useRef(null);
  const adataObsKeyRef = useRef(null);
  const [description, setDescription] = useState<string | null>(null);
  const [paramsDependenciesList, setParamsDependenciesList] = useState<any>([]);
  const [paramsDict, setParamsDict] = useState<any>({});

  useEffect(() => {
    setDescription(null);
  }, [nodeId]);

  const onFieldsChange = (changedFields: any[]) => {
    const dependencies = paramsDependenciesList || [];

    for (const changedField of changedFields) {
      const currentFieldName = changedField.name[0]; // Assuming name is an array

      const newValue = changedField.value;

      // Find the corresponding currentIndepend for this changed field
      const correspondingIndepend = dependencies.find(
        ([independ]) => independ === currentFieldName,
      );

      if (correspondingIndepend) {
        const associatedField = correspondingIndepend[1]; // The associated field

        if (associatedField) {
          const associatedFieldAlreadySet = changedFields.some(
            (field) => field.name[0] === associatedField,
          );

          if (!associatedFieldAlreadySet) {
            // Check if the current field value actually changed
            if (newValue !== paramsDict[currentFieldName.default_value]) {
              form.setFieldsValue({
                [associatedField]: null, // Clear the associated field
              });
            }
          }
        }
      }
    }
  };

  const openDescription = (description: string) => {
    setDescription(description);
  };

  const renderFormItem = (
    key: string,
    name: string,
    paramsRenderType: string,
    paramsOptional: boolean,
    labelCol: number,
    description: string,
    paramsOptionsDict: any[],
    filename?: string,
  ) => {
    const onDetailShow = () => {
      openDescription(description);
    };
    const paramLayerPath = name.split('#.?_');
    const rParamDict = recommendedParamDict || {};
    const isRecommended = !!rParamDict[paramLayerPath[0]];
    const paramLabel = (
      <ParamLabel name={key} onDetailShow={onDetailShow} isRecommended={isRecommended} />
    );
    switch (paramsRenderType) {
      case ParamsRenderType.SINGLE_CELL_SELECTOR: {
        return (
          <Form.Item
            key={key}
            name={name}
            label={paramLabel}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <SingleCellSelector dataStructure={dataStructure} />
          </Form.Item>
        );
      }
      case ParamsRenderType.SINGLE_GENE_SELECTOR: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <SingleGeneSelector dataStructure={dataStructure} />
          </Form.Item>
        );
      }
      case ParamsRenderType.STR_INPUT: {
        return (
          <Form.Item
            key={key}
            name={name}
            label={paramLabel}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <Input />
          </Form.Item>
        );
      }
      case ParamsRenderType.INT_INPUT: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        );
      }
      case ParamsRenderType.FLOAT_INPUT: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        );
      }
      case ParamsRenderType.BOOL_INPUT: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            valuePropName="checked"
            rules={[{ required: !paramsOptional }]}
          >
            <Switch />
          </Form.Item>
        );
      }
      case ParamsRenderType.STR_LIST_INPUT: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <ListInput elementType={ElementType.STRING} />
          </Form.Item>
        );
      }
      case 'str-list': {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <ListInput elementType={ElementType.STRING} />
          </Form.Item>
        );
      }
      case ParamsRenderType.INT_LIST_INPUT: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <ListInput elementType={ElementType.INT} />
          </Form.Item>
        );
      }
      case ParamsRenderType.GENES_SELECTOR: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <GenesSelector nodeId={nodeId} dataStructure={dataStructure} />
          </Form.Item>
        );
      }
      case ParamsRenderType.CELLS_SELECTOR: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <CellsSelector nodeId={nodeId} />
          </Form.Item>
        );
      }
      case ParamsRenderType.ORGANISM_SELECTOR: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <OrganismSelector organismFormItemRef={organismFormItemRef} />
          </Form.Item>
        );
      }
      case ParamsRenderType.LIBRARIES_SELECTOR: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <LibrarySelector organismFormItemRef={organismFormItemRef} />
          </Form.Item>
        );
      }
      case ParamsRenderType.STR_OPTIONS: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <StrOptions list={paramsOptionsDict} />
          </Form.Item>
        );
      }
      case ParamsRenderType.STR_RADIO: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <StrRadio list={paramsOptionsDict} />
          </Form.Item>
        );
      }
      case ParamsRenderType.STR_MULTIPLE_OPTIONS: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <StrMultipleOptions list={paramsOptionsDict} />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_OBS_KEY: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <AdataObsKey
              nodeId={nodeId}
              adataObsKeyRef={adataObsKeyRef}
              dataStructure={dataStructure}
            />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_VAR_KEY: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <AdataVarKey nodeId={nodeId} dataStructure={dataStructure} />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_OBSP_KEY: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <AdataObspKey nodeId={nodeId} dataStructure={dataStructure} />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_OBSM_KEY: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <AdataObsmKey nodeId={nodeId} dataStructure={dataStructure} />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_LAYER_KEY: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <AdataLayerKey nodeId={nodeId} dataStructure={dataStructure} />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_UNS_KEY: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <AdataUnsKey nodeId={nodeId} dataStructure={dataStructure} />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_OBS_KEY_LIST: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <AdataObsKeyList nodeId={nodeId} dataStructure={dataStructure} />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_VAR_KEY_LIST: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <AdataVarKeyList nodeId={nodeId} dataStructure={dataStructure} />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_OBS_GROUP: {
        return (
          <Form.Item
            name={name}
            key={key}
            label={paramLabel}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <AdataObsGroup nodeId={nodeId} dataStructure={dataStructure} />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_OBS_GROUP_LIST: {
        return (
          <Form.Item
            key={key}
            name={name}
            label={paramLabel}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <AdataObsGroupList
              nodeId={nodeId}
              adataObsKeyRef={adataObsKeyRef}
              dataStructure={dataStructure}
            />
          </Form.Item>
        );
      }
      case ParamsRenderType.DATASELECTER: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <DataSelecter />
          </Form.Item>
        );
      }
      case ParamsRenderType.FILE: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <ParamFileInput filename={filename} nodeId={nodeId} />
          </Form.Item>
        );
      }
      case ParamsRenderType.API_KEY_INPUT: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[{ required: !paramsOptional }]}
          >
            <APIKeyInput />
          </Form.Item>
        );
      }
      case ParamsRenderType.DICT_INPUT: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[
              {
                validator(_, value: any) {
                  return new Promise((resolve, reject) => {
                    if (typeof value !== 'object') {
                      reject('Please input a valid JSON string');
                      return;
                    }
                    resolve(true);
                  });
                },
              },
            ]}
          >
            <DictInput />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_LIST_INPUT: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[
              {
                validator(_, value: any) {
                  return new Promise((resolve, reject) => {
                    if (value.length === 0 && !paramsOptional) {
                      reject('Please input at least one file');
                      return;
                    }
                    resolve(true);
                  });
                },
              },
            ]}
          >
            <AdataListInput />
          </Form.Item>
        );
      }
      case ParamsRenderType.ADATA_INPUT: {
        return (
          <Form.Item
            key={key}
            label={paramLabel}
            name={name}
            labelCol={{ span: labelCol }}
            rules={[
              {
                validator(_, value: any) {
                  return new Promise((resolve, reject) => {
                    if (!value && !paramsOptional) {
                      reject('Please input at least one file');
                      return;
                    }
                    resolve(true);
                  });
                },
              },
            ]}
          >
            <AdataInput />
          </Form.Item>
        );
      }
      default:
        return null;
    }
  };
  const renderRowFormItem = (item: any) => {
    return (
      <Row>
        <Col span={5} />
        {item.map((value) => {
          const dependency = paramsDict[value];
          return (
            <Col key={`${dependency.name}`} span={16 / item.length}>
              {renderFormItem(
                dependency.name,
                dependency.name,
                dependency.render_type,
                dependency.optional,
                8,
                dependency.description,
                dependency.options,
                dependency.filename,
              )}
            </Col>
          );
        })}
      </Row>
    );
  };

  const nestArgsFormItemKeys = (childrenList) => {
    const formItemList = childrenList;
    // const formItemKeys = Object.keys(paramsRenderTypeDict);
    formItemList.sort((key1: any, key2: any) => {
      const key1Optional = key1.optional;
      const key2Optional = key2.optional;

      if (key1Optional && !key2Optional) {
        return 1;
      } else if (!key1Optional && key2Optional) {
        return -1;
      } else {
        return 0;
      }
    });

    return formItemList;
  };

  useEffect(() => {
    const paramsDependenciesList = [];
    const paramsDict = {};
    paramsList.forEach((params) => {
      paramsDict[params.name] = params;
    });
    setParamsDict(paramsDict);
    paramsList.forEach((element) => {
      if (element.dependencies && element.dependencies instanceof Array) {
        element.dependencies.forEach((dependencyName: string) => {
          paramsDependenciesList.push([dependencyName, element.name]);
        });
      }
    });

    setParamsDependenciesList(paramsDependenciesList);
  }, []);

  const argsFormItemKeys = () => {
    const formItemList = paramsList;
    // const formItemKeys = Object.keys(paramsRenderTypeDict);
    formItemList.sort((key1: any, key2: any) => {
      const key1Optional = key1.optional;
      const key2Optional = key2.optional;

      if (key1Optional && !key2Optional) {
        return 1;
      } else if (!key1Optional && key2Optional) {
        return -1;
      } else {
        return 0;
      }
    });

    const filteredFormItemList = formItemList.filter((item) => {
      for (const element of paramsDependenciesList) {
        if (element.includes(item.name)) {
          return false; // Do not include this item in the new array
        }
      }
      return true; // Include this item in the new array
    });

    return filteredFormItemList;
  };

  return (
    <Form
      form={form}
      key={nodeId}
      // layout="horizontal"
      layout={layout}
      disabled={disabled}
      labelAlign="right"
      onFieldsChange={onFieldsChange}
      autoComplete="off"
    >
      {paramsDependenciesList.map((item) => {
        return <div key={item}>{renderRowFormItem(item)}</div>;
      })}
      {argsFormItemKeys().map((item) => {
        if (!item.children) {
          return (
            <div key={item.name}>
              {renderFormItem(
                item.name,
                item.name,
                item.render_type,
                // item.default_value,
                item.optional,
                8,
                item.description,
                item.options,
                item.filename,
              )}
            </div>
          );
        } else {
          return (
            <Form.Item
              key={`${item.name}`}
              labelCol={{ span: 8 }}
              label={item.name}
              name={item.name}
              rules={[{ required: !item.optional }]}
            >
              {' '}
              <div
                style={{
                  border: '1px solid rgba(169,169,169,.4)',
                  borderRadius: '5px',
                  paddingTop: '5px',
                  paddingLeft: '10px',
                  paddingRight: '10px',
                }}
              >
                {nestArgsFormItemKeys(item.children).map((value) => {
                  return renderFormItem(
                    value.name,
                    `${item.name}#.?_${value.name}`,
                    value.render_type,
                    value.optional,
                    8,
                    value.description,
                    value.options,
                    value.filename,
                  );
                })}
              </div>
            </Form.Item>
          );
        }
      })}
      <DescriptionModal description={description} setDescription={setDescription} />
    </Form>
  );
};

export default FBParameterForm;
