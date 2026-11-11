import ManagementHead from '@/components/special/functionBlock/head';
import FunctionBlockList from '@/components/special/functionBlock/side';
import { requestPublicFBGroupList, requestGetFBInformation } from '@/request/functionBlock';
import { Card, Layout } from 'antd';
import { useEffect, useState } from 'react';

const { Header, Sider, Content } = Layout;

const headerStyle: React.CSSProperties = {
  color: '#fff',
  height: '5vh',
  paddingInline: 50,
  lineHeight: '5vh',
  backgroundColor: '#364578',
};

const contentStyle: React.CSSProperties = {
  // textAlign: 'center',
  minHeight: '120',
  color: '#000',
  height: 'calc(91vh - 0.5px)',
  width: '84vw',
  backgroundColor: '#F3F3F2',
  padding: 30,
};

const leftSiderStyle: React.CSSProperties = {
  height: '95vh',
  width: '16vw',
  color: '#000',
  backgroundColor: '#FFFFFF',
  boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.04)',
};

const Home = () => {
  const [functionBlockId, setFunctionBlockId] = useState<string>('');
  const [defaultSelectedFB, setDefaultSelectedFB] = useState<string>('');
  const [functionBlockGroup, setFunctionBlockGroup] = useState<string>('');
  const [description, setDescription] = useState('');
  const [FBList, setFBList] = useState<any[]>([]);
  const getFunctionBlockMenuList = async () => {
    const { data: result } = await requestPublicFBGroupList();
    if (result && result.length > 0) {
      const FBlist: any[] = [];
      for (let i = 1; i < result.length + 1; i++) {
        result.forEach((item: any) => {
          if (item.serialNumber === i) {
            FBlist.push(item);
          }
        });
      }
      setFBList(FBlist);
      // console.log(FBlist);
      let firstFunctionBlockGroup: any = null;
      let firstFunctionBlockId: any = null;

      for (const item of FBlist) {
        if (Array.isArray(item.functionBlockList) && item.functionBlockList.length > 0) {
          const firstFunctionBlock = item.functionBlockList[0];
          firstFunctionBlockId = firstFunctionBlock.id;
          firstFunctionBlockGroup = item.serialNumber;
          break; // Exit the loop once the first non-empty functionBlockList is found
        }
      }

      if (firstFunctionBlockId !== null) {
        setFunctionBlockId(firstFunctionBlockId);
        setDefaultSelectedFB(firstFunctionBlockId);
        setFunctionBlockGroup(firstFunctionBlockGroup);
        // getDescription(firstFunctionBlockId);
      }
    }
  };

  useEffect(() => {
    getFunctionBlockMenuList();
  }, []);

  const getDescription = async (id) => {
    const { data: information } = await requestGetFBInformation(id);
    setDescription(information.currentVersionInformation.description);
  };
  useEffect(() => {
    if (functionBlockId) {
      getDescription(functionBlockId);
    }
  }, [functionBlockId]);

  return (
    <div>
      <Layout>
        <Header style={headerStyle}>
          <ManagementHead />
        </Header>
        <Layout>
          <Sider width="14vw" style={leftSiderStyle}>
            <FunctionBlockList
              setFunctionBlockId={setFunctionBlockId}
              defaultSelectedFB={defaultSelectedFB}
              functionBlockGroup={functionBlockGroup}
              functionBlockList={FBList}
            />
          </Sider>
          <Content style={contentStyle}>
            {/* <Outlet /> */}
            <Card style={{ height: 'calc(91vh - 1px)', overflow: 'auto' }} bordered={false}>
              {description}
            </Card>
          </Content>
        </Layout>
      </Layout>
    </div>
  );
};

export default Home;
