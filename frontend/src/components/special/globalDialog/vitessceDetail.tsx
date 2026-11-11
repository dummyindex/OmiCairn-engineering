import { useModel } from 'umi';
import { Button, Modal, Form, Select, Divider } from 'antd';
import { VitessceStatus } from '@/interfaces/visualPanel';
import { useEffect, useState } from 'react';

const VitessceDetail = () => {
  const {
    vitessceDetailVisible,
    closeVitessceDetail,
    vitessceState,
    startPrehandleVitessce,
    dataStructure,
    genesetList,
    dataId,
  } = useModel('visualPanelControl');
  const [form] = Form.useForm();

  const [sortedVarList, setSortedVarList] = useState<any[]>([]);

  const { status, options } = vitessceState || {};

  // obs_cols = options.get("obs_cols", category_obs_keys)
  //   var_cols = options.get("var_cols", [])
  //   obsm_cols = options.get("obsm_cols", [])
  //   uns_spatial_key = options.get("uns_spatial_key", None)
  //   image = options.get("image", "hires") # hires or lowers
  useEffect(() => {
    form.setFieldsValue({
      obs_cols: options?.obs_cols || [],
      var_cols: options?.var_cols || [],
      obsm_cols: options?.obsm_cols || [],
      uns_spatial_key: options?.uns_spatial_key || null,
      image: options?.image || 'hires',
      geneset: options?.geneset || null,
    });
    return () => {
      form.resetFields();
    };
  }, [options]);

  useEffect(() => {
    if (dataStructure?.var) {
      const categoryVarList = dataStructure.var.filter((item: any) => {
        if (item.dtype !== 'category' && item.dtype !== 'bool') {
          return false;
        }
        const categories: string[] = item.categories || [];
        return categories.includes('True') || categories.includes('False');
      });
      const includeKey = (key: string) => {
        return key.includes('hvg') || key.includes('highly_variable');
      };
      const sortedVarList = categoryVarList.sort((a: { key: string }, b: { key: string }) => {
        const { key: keyA } = a;
        const { key: keyB } = b;
        if (includeKey(keyA) && !includeKey(keyB)) {
          return -1;
        }
        if (!includeKey(keyA) && includeKey(keyB)) {
          return 1;
        }
        return 0;
      });
      setSortedVarList(sortedVarList);
    } else {
      setSortedVarList([]);
    }
  }, [dataStructure]);

  return (
    <Modal
      title="Vitessce Detail"
      centered
      width="40vw"
      visible={vitessceDetailVisible}
      onCancel={closeVitessceDetail}
      footer={
        <>
          {!vitessceState && (
            <Button
              type="primary"
              onClick={() => {
                const values = form.getFieldsValue();
                startPrehandleVitessce(values);
              }}
            >
              Submit
            </Button>
          )}
          {status === VitessceStatus.FAILED && (
            <Button
              type="primary"
              onClick={() => {
                const values = form.getFieldsValue();
                startPrehandleVitessce(values);
              }}
            >
              Retry
            </Button>
          )}
          {status === VitessceStatus.SUCCESS && (
            <>
              <Button
                type="primary"
                onClick={() => {
                  const values = form.getFieldsValue();
                  startPrehandleVitessce(values);
                }}
              >
                Submit Again
              </Button>
              <Button
                type="primary"
                onClick={() => {
                  const host = window.location.host;
                  const protocol = window.location.protocol;
                  const url = `${protocol}//${host}/vSpatial-panel?data-id=${dataId}`;
                  window.open(url, '_blank');
                }}
              >
                Go to Vitessce
              </Button>
            </>
          )}
          <Button type="primary" onClick={closeVitessceDetail}>
            OK
          </Button>
        </>
      }
    >
      {/* <div>
        <div
          style={{
            lineHeight: '2.5em',
          }}
        >
          <span>Status:</span> <span>{status || '---'}</span>
        </div>
        <div
          style={{
            lineHeight: '2.5em',
          }}
        >
          <span>Status Reason:</span>{' '}
          <span title={statusReason}>{statusReason ? cutString(statusReason, 50) : '---'}</span>
        </div>
        <div
          style={{
            lineHeight: '2.5em',
          }}
        >
          <span>Created Time:</span> <span>{createdTime || '---'}</span>
        </div>
      </div> */}
      <Divider orientation="left" orientationMargin="0" style={{ marginTop: '0px' }}>
        Prehandle Options
      </Divider>
      <Form
        form={form}
        labelCol={{ span: 6 }}
        labelAlign="left"
        disabled={[VitessceStatus.PENDING, VitessceStatus.RUNNING].includes(status)}
      >
        <Form.Item label="Coloring Cell Column" name="obs_cols">
          <Select mode="multiple" allowClear style={{ width: '100%' }} placeholder="Please select">
            {dataStructure?.obs?.map((item: any) => {
              const { key, dtype } = item;
              if (dtype === 'category') {
                return (
                  <Select.Option key={key} value={key}>
                    {key}
                  </Select.Option>
                );
              }
              return null;
            })}
          </Select>
        </Form.Item>
        {/* <Form.Item label="Var cols" name="var_cols">
          <Select mode="multiple" allowClear style={{ width: '100%' }} placeholder="Please select">
            {dataStructure?.var?.map((item: any) => {
              const { key } = item;
              return (
                <Select.Option key={key} value={key}>
                  {key}
                </Select.Option>
              );
            })}
          </Select>
        </Form.Item> */}
        <Form.Item label="Uns Spatial Library" name="uns_spatial_key">
          <Select style={{ width: '100%' }} placeholder="Please select">
            {Object.keys(dataStructure?.uns_keys?.spatial || {}).map((item: any) => (
              <Select.Option key={item} value={item}>
                {item}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item label="Image" name="image">
          <Select style={{ width: '100%' }} placeholder="Please select" defaultValue={'hires'}>
            {['hires', 'lowres'].map((item: any) => (
              <Select.Option key={item} value={item}>
                {item}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item label="Geneset" name="geneset">
          <Select allowClear style={{ width: '100%' }} placeholder="Please select">
            {sortedVarList.map((item: any) => {
              const { key } = item;
              return (
                <Select.Option key={key} value={`var::${key}`}>
                  {`var::${key}`}
                </Select.Option>
              );
            })}
            {genesetList.map((item: any) => (
              <Select.Option key={item.name} value={`geneset::${item.name}`}>
                {`geneset::${item.name}`}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item label="Coordinates" name="obsm_cols">
          <Select mode="multiple" allowClear style={{ width: '100%' }} placeholder="Please select">
            {dataStructure?.obsm &&
              Object.keys(dataStructure.obsm).map((item: any) => {
                if (item === 'spatial') {
                  return null;
                }
                return (
                  <Select.Option key={item} value={item}>
                    {item}
                  </Select.Option>
                );
              })}
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default VitessceDetail;
