import FBParameterForm from '@/components/highReuse/fBParameterForm';
import { LoadingOutlined, RightOutlined } from '@ant-design/icons';
import { Divider } from 'antd';
import { NodeState } from '@/constants/node';
import { useModel } from 'umi';

const stateColorMap: any = {
  [NodeState.ORIGINAL]: '#fff',
  [NodeState.RUNNING]: '#939393',
  [NodeState.FINISHED]: '#4D9A17',
  [NodeState.FAILED]: '#C74242',
  [NodeState.PENDING]: '#939393',
  [NodeState.DEBUGGING]: '#939393',
  [NodeState.CANCELLED]: '#fff',
  [NodeState.GENERATING]: '#939393',
  [NodeState.BEAUTIFYING]: '#939393',
};

const MiniToolApplication = ({ form, loading, paramList, startTask, truckNode }) => {
  const { dictionary } = useModel('localization');
  return (
    <div
      style={{
        height: '70vh',
        overflowY: 'auto',
        fontFamily: 'inherit',
        fontSize: 13,
        padding: '1em 1em 1em 1em',
        backgroundColor: '#f2f4fc',
        borderRadius: '0.5rem',
        marginLeft: '0.75rem',
        marginRight: '1.25rem',
        // marginBottom: '0.75rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
        alignItems: 'stretch',
        // gap: '1rem',
      }}
    >
      {/* <div className="application-container"> */}
      {/* <div className="upload-section">
                                <div className="upload-title-container">
                                  <h3>Upload Single Cell RNA-Seq Reference Data File</h3>
                                </div>
                                <div className="upload-info">
                                  <UploadOutlined className="upload-icon" />
                                  <span className="upload-info-text">
                                    <span className="bold-black-text">UPLOAD FROM</span>{' '}
                                    <span className="bold-grey-text">
                                      Size limits - Local: 100Mb / Remote: no limit
                                    </span>
                                  </span>
                                </div>
                                <div className="upload-file-button-controls">
                                  <button className="btn-local">Local</button>
                                  <button className="btn-remote">Remote</button>
                                </div>
                                <div className="file-info-container">
                                  <p>No Files Selected!</p>
                                  <p>
                                    Allowed file formats: <span className="file-format">h5ad</span>
                                  </p>
                                  <button className="btn-demo">Use Demo Data</button>
                                </div>
                                <div className="extra-info">
                                  <p>
                                    Your file can be in the following formats:{' '}
                                    <span className="file-format">h5ad</span>
                                  </p>
                                  <a href="/example-data" className="example-data-link">
                                    View example data <EyeOutlined className="eye-icon" />
                                  </a>
                                  <button className="btn-show-more">
                                    <DownOutlined className="downward-icon" /> Show more
                                  </button>
                                </div>
                              </div>

                              <div className="section-space"></div>

                              <div className="upload-section">
                                <div className="upload-title-container">
                                  <h3>Upload Single Cell RNA-Seq Test Data File</h3>
                                </div>
                                <div className="upload-info">
                                  <UploadOutlined className="upload-icon" />
                                  <span className="upload-info-text">
                                    <span className="bold-black-text">UPLOAD FROM</span>{' '}
                                    <span className="bold-grey-text">
                                      Size limits - Local: 100Mb / Remote: no limit
                                    </span>
                                  </span>
                                </div>
                                <div className="upload-file-button-controls">
                                  <button className="btn-local">Local</button>
                                  <button className="btn-remote">Remote</button>
                                </div>
                                <div className="file-info-container">
                                  <p>No Files Selected!</p>
                                  <p>
                                    Allowed file formats: <span className="file-format">h5ad</span>
                                  </p>
                                  <button className="btn-demo">Use Demo Data</button>
                                </div>
                                <div className="extra-info">
                                  <p>
                                    Your file can be in the following formats:{' '}
                                    <span className="file-format">h5ad</span>
                                  </p>
                                  <a href="/example-data" className="example-data-link">
                                    View example data <EyeOutlined className="eye-icon" />
                                  </a>
                                  <button className="btn-show-more">
                                    <DownOutlined className="downward-icon" /> Show more
                                  </button>
                                </div>
                              </div> */}
      <div className="update-params-page-title">
        <span>{dictionary.PARAMETER_PANEL}</span>
        <span
          style={{
            color: stateColorMap[truckNode?.state],
            textTransform: 'capitalize',
          }}
        >
          {truckNode?.state}
        </span>
      </div>
      <Divider />
      <div className="update-params-page">
        {/* <div className="input-group">
                                  <label>
                                    BATCH COLUMN NAME{' '}
                                    <QuestionCircleOutlined className="info-icon" />
                                  </label>{' '}
                                  <select className="input-field">
                                    <option>Select...</option>
                                  </select>
                                </div>
                                <div className="input-group">
                                  <label>
                                    CELL TYPE COLUMN NAME{' '}
                                    <QuestionCircleOutlined className="info-icon" />
                                  </label>{' '}
                                  <select className="input-field">
                                    <option>Select...</option>
                                  </select>
                                </div>
                                <div className="input-group">
                                  <label>
                                    LABEL COLUMN NAME{' '}
                                    <QuestionCircleOutlined className="info-icon" />
                                  </label>{' '}
                                  <select className="input-field">
                                    <option>Select...</option>
                                  </select>
                                </div>
                                <div className="input-group">
                                  <label>
                                    GENE NAMES COLUMN{' '}
                                    <QuestionCircleOutlined className="info-icon" />
                                  </label>
                                  <input type="text" className="input-field" placeholder="None" />
                                </div>
                                <div className="input-group">
                                  <label>
                                    IS DATA RAW? <QuestionCircleOutlined className="info-icon" />
                                  </label>{' '}
                                  <input type="checkbox" className="input-checkbox" />
                                </div> */}
        <FBParameterForm
          onKeyDown={(e) => {
            e.stopPropagation();
          }}
          onKeyUp={(e: any) => {
            e.stopPropagation();
          }}
          form={form}
          paramsList={paramList}
          layout={'vertical'}
          disabled={loading}
        />
      </div>
      <div className="update-params-buttons-controls">
        <button className="btn-help">Need help?</button>
        <button
          className="btn-submit"
          style={{
            filter: loading ? 'grayscale(1)' : 'none',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
          disabled={loading}
          onClick={startTask}
        >
          {dictionary.SUBMIT}
          {loading ? (
            <LoadingOutlined className="downward-icon" />
          ) : (
            <RightOutlined className="downward-icon" />
          )}
        </button>
      </div>
      {/* </div> */}
    </div>
  );
};

export default MiniToolApplication;
