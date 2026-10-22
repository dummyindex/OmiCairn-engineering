import { RobotOutlined } from '@ant-design/icons';
import { Card } from 'antd';
import { useModel } from 'umi';

const WelcomeCard = () => {
  const { dictionary } = useModel('localization');
  return (
    <div style={{ padding: '20px' }}>
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px', color: '#5974CE' }} />
        <div style={{ marginBottom: '8px', fontSize: '20px', fontWeight: 'bold' }}>
          {dictionary.WELCOME_TITLE}
        </div>
        <div style={{ color: '#666', fontSize: '14px', whiteSpace: 'pre-line' }}>
          {dictionary.WELCOME_SUBTITLE}
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <div
          style={{
            fontWeight: 'bold',
            marginBottom: '16px',
            fontSize: '16px',
            color: '#333',
          }}
        >
          {dictionary.CORE_ANALYSIS_FUNCTIONS}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
          <Card size="small" hoverable style={{ cursor: 'default', border: '1px solid #e8f4f8' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#52c41a',
                  marginRight: '8px',
                }}
              />
              <span style={{ fontWeight: 'bold', fontSize: '14px' }}>
                {dictionary.SINGLE_CELL_RNA_SEQ}
              </span>
            </div>
            <div
              style={{ fontSize: '12px', color: '#666', lineHeight: '1.5', wordSpacing: '0.5px' }}
            >
              {dictionary.SINGLE_CELL_DESCRIPTION}
            </div>
          </Card>

          <Card size="small" hoverable style={{ cursor: 'default', border: '1px solid #f0f8ff' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#1890ff',
                  marginRight: '8px',
                }}
              />
              <span style={{ fontWeight: 'bold', fontSize: '14px' }}>
                {dictionary.AUTO_GENIE_PLANNING}
              </span>
            </div>
            <div
              style={{
                fontSize: '12px',
                color: '#666',
                lineHeight: '1.5',
                wordSpacing: '0.5px',
                letterSpacing: '0.3px',
              }}
            >
              {dictionary.AUTO_GENIE_DESCRIPTION}
            </div>
          </Card>

          <Card size="small" hoverable style={{ cursor: 'default', border: '1px solid #fff7e6' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#fa8c16',
                  marginRight: '8px',
                }}
              />
              <span style={{ fontWeight: 'bold', fontSize: '14px' }}>
                {dictionary.BUG_FIXER_REPAIR}
              </span>
            </div>
            <div
              style={{
                fontSize: '12px',
                color: '#666',
                lineHeight: '1.5',
                wordSpacing: '0.5px',
                letterSpacing: '0.3px',
              }}
            >
              {dictionary.BUG_FIXER_DESCRIPTION}
            </div>
          </Card>

          <Card size="small" hoverable style={{ cursor: 'default', border: '1px solid #f6ffed' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#722ed1',
                  marginRight: '8px',
                }}
              />
              <span style={{ fontWeight: 'bold', fontSize: '14px' }}>
                {dictionary.REPORT_AI_GENERATION}
              </span>
            </div>
            <div
              style={{
                fontSize: '12px',
                color: '#666',
                lineHeight: '1.5',
                wordSpacing: '0.5px',
                letterSpacing: '0.3px',
              }}
            >
              {dictionary.REPORT_AI_DESCRIPTION}
            </div>
          </Card>
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <div
          style={{
            fontWeight: 'bold',
            marginBottom: '16px',
            fontSize: '16px',
            color: '#333',
          }}
        >
          {dictionary.AI_ANALYSIS_MODULES}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
          <Card size="small" hoverable style={{ cursor: 'default', border: '1px solid #e8f4f8' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#52c41a',
                  marginRight: '8px',
                }}
              />
              <span style={{ fontWeight: 'bold', fontSize: '14px' }}>{dictionary.PARAMS_AI}</span>
            </div>
            <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.4' }}>
              {dictionary.PARAMS_AI_DESCRIPTION}
            </div>
          </Card>

          <Card size="small" hoverable style={{ cursor: 'default', border: '1px solid #f0f8ff' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#1890ff',
                  marginRight: '8px',
                }}
              />
              <span style={{ fontWeight: 'bold', fontSize: '14px' }}>
                {dictionary.DATA_INTERPRETATION}
              </span>
            </div>
            <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.4' }}>
              {dictionary.DATA_INTERPRETATION_DESCRIPTION}
            </div>
          </Card>

          <Card size="small" hoverable style={{ cursor: 'default', border: '1px solid #fff7e6' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#fa8c16',
                  marginRight: '8px',
                }}
              />
              <span style={{ fontWeight: 'bold', fontSize: '14px' }}>{dictionary.WORKFLOW_AI}</span>
            </div>
            <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.4' }}>
              {dictionary.WORKFLOW_AI_DESCRIPTION}
            </div>
          </Card>

          <Card size="small" hoverable style={{ cursor: 'default', border: '1px solid #f6ffed' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#722ed1',
                  marginRight: '8px',
                }}
              />
              <span style={{ fontWeight: 'bold', fontSize: '14px' }}>
                {dictionary.PIPELINE_TEMPLATE}
              </span>
            </div>
            <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.4' }}>
              {dictionary.PIPELINE_TEMPLATE_DESCRIPTION}
            </div>
          </Card>
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <div
          style={{
            fontWeight: 'bold',
            marginBottom: '16px',
            fontSize: '16px',
            color: '#333',
          }}
        >
          {dictionary.DATA_MANAGEMENT_TOOLS}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {[
            { text: dictionary.DATA_STORAGE_MANAGEMENT, type: 'data-management' },
            { text: dictionary.VITESSCE_VISUALIZATION, type: 'visualization' },
            { text: dictionary.GSEAPY_PATHWAY_ANALYSIS, type: 'pathway' },
            { text: dictionary.S3_CLOUD_STORAGE, type: 'storage' },
            { text: dictionary.COMPUTATION_RESOURCE_MANAGEMENT, type: 'computation' },
            { text: dictionary.USER_SPACE_MANAGEMENT, type: 'user-space' },
          ].map((item, index) => (
            <div
              key={index}
              style={{
                padding: '6px 12px',
                background: '#f0f8ff',
                border: '1px solid #d6e4ff',
                borderRadius: '16px',
                cursor: 'default',
                fontSize: '12px',
                transition: 'all 0.2s',
              }}
            >
              {item.text}
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          textAlign: 'center',
          padding: '20px',
          background: '#fafafa',
          borderRadius: '8px',
        }}
      >
        <div style={{ fontSize: '14px', color: '#666', marginBottom: '12px' }}>
          {dictionary.INPUT_ANALYSIS_NEEDS}
        </div>
        <div style={{ fontSize: '12px', color: '#999' }}>{dictionary.SUPPORT_FEATURES}</div>
      </div>
    </div>
  );
};

export default WelcomeCard;
