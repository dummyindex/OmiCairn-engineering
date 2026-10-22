import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import CustomTabSwitch from '@/components/common/customTabSwitch';
import CollaborativeListAndShareModal from '@/pages/management/combinedCollaborativeListAndShareModal';
import AutoGenieProgressDropdown from '@/components/special/globalDialog/autoGenieProgressDropdown';
import { LoginOutlined, LogoutOutlined, UserOutlined } from '@ant-design/icons';
import { Avatar, Button, Col, Divider, Dropdown, Menu, Row } from 'antd';
import { useEffect, useState } from 'react';
import { history, useLocation, useModel } from 'umi';
// import { requestLatestComputation } from '@/request/computation';
// import { requestGetTagList, requestGetFigureInfo } from '@/request/attachedData';
// import { requestGetFBInformation } from '@/request/functionBlock';
// import { requestNodeParams } from '@/request/node';
// import { FlowTool } from '@/util/flowTool';
// import JSZip from 'jszip';
// import { saveAs } from 'file-saver';

export default function PanelHead() {
  const location = useLocation();
  const [currentPath, setCurrentPath] = useState<string>('');

  // const { analysisDetail, instance, nodes } = useModel('analysis');
  const { analysisDetail } = useModel('analysis');
  const { userInfo, immediateRefresh, isGuest } = useModel('user');
  const { dictionary } = useModel('localization');
  const [analysisId, setAnalysisId] = useState<string | null>(null);

  const isGuestUser = isGuest();

  useEffect(() => {
    const path = location.pathname;
    setCurrentPath(path);
  }, [location]);

  useEffect(() => {
    if (isGuestUser) {
      immediateRefresh();
    }
  }, [isGuestUser]);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('isGuest');
    history.push('/login/byPassword');
  };

  // const toggleChatbot = () => {
  //   setChatbotState((prevState) => ({
  //     ...prevState,
  //     isVisible: !prevState.isVisible,
  //   }));
  // };

  // const downloadAllPlots = async () => {
  //   const abortController = new AbortController();
  //   const signal = abortController.signal;
  //   let downloadCancelled = false;

  //   try {
  //     let progress = 0;
  //     let totalSteps = 0;
  //     let currentStep = 0;

  //     notification.open({
  //       key: 'download-notification',
  //       message: 'Preparing download...',
  //       description: (
  //         <div>
  //           <div>Gathering plots and node information. This may take a moment.</div>
  //           <Progress percent={0} status="active" style={{ marginTop: 8 }} />
  //           <div style={{ marginTop: 8, textAlign: 'right' }}>
  //             <Button
  //               size="small"
  //               onClick={() => {
  //                 downloadCancelled = true;
  //                 abortController.abort();
  //                 notification.close('download-notification');
  //                 notification.info({
  //                   message: 'Download cancelled',
  //                   description: 'The download process has been cancelled.',
  //                 });
  //               }}
  //             >
  //               Cancel
  //             </Button>
  //           </div>
  //         </div>
  //       ),
  //       duration: 0,
  //       icon: <Spin />,
  //     });

  //     const updateProgress = (stepCompleted = 1, message) => {
  //       if (downloadCancelled) return;

  //       currentStep += stepCompleted;
  //       progress = Math.floor((currentStep / totalSteps) * 100);

  //       notification.open({
  //         key: 'download-notification',
  //         message: message || 'Preparing download...',
  //         description: (
  //           <div>
  //             <Progress percent={progress} status="active" style={{ marginTop: 8 }} />
  //             <div style={{ marginTop: 8, textAlign: 'right' }}>
  //               <Button
  //                 size="small"
  //                 onClick={() => {
  //                   downloadCancelled = true;
  //                   abortController.abort();
  //                   notification.close('download-notification');
  //                   notification.info({
  //                     message: 'Download cancelled',
  //                     description: 'The download process has been cancelled.',
  //                   });
  //                 }}
  //               >
  //                 Cancel
  //               </Button>
  //             </div>
  //           </div>
  //         ),
  //         duration: 0,
  //         icon: <Spin />,
  //       });

  //       if (downloadCancelled) {
  //         throw new Error('Download cancelled');
  //       }
  //     };

  //     if (!instance || !nodes || nodes.length === 0) {
  //       notification.close('download-notification');
  //       notification.error({
  //         message: 'Download failed',
  //         description: 'No nodes found in current analysis.',
  //       });
  //       return;
  //     }

  //     const flowTool = new FlowTool(instance);
  //     const zip = new JSZip();
  //     type NodeWithPlots = {
  //       id: string;
  //       name: any;
  //       resultDataId: any;
  //       figures: any;
  //       computationResourceConfigure?: any;
  //       systemEnv?: any;
  //     };
  //     const nodesWithPlots: NodeWithPlots[] = [];

  //     for (const node of nodes) {
  //       if (downloadCancelled) break;

  //       if (node.type === 'data node' || node.data.state !== 'finished') {
  //         continue;
  //       }

  //       try {
  //         // Check if run complete node has plots
  //         const { data: latestComputation } = await requestLatestComputation(node.id);
  //         if (!latestComputation || !latestComputation.resultDataId) {
  //           continue;
  //         }

  //         const tagList = await requestGetTagList(latestComputation.resultDataId);
  //         const currentTag = tagList.find((tag) => +tag.node_id === +node.id);
  //         if (!currentTag) {
  //           continue;
  //         }

  //         const { charts } = currentTag;
  //         const staticFigureList = charts.filter((chart) => chart.exist_type === 'static-image');
  //         if (staticFigureList.length > 0) {
  //           nodesWithPlots.push({
  //             id: node.id,
  //             name: node.data.label,
  //             resultDataId: latestComputation.resultDataId,
  //             figures: staticFigureList,
  //             computationResourceConfigure: node.data.computationResourceConfigure,
  //             systemEnv: node.data.systemEnv,
  //           });
  //         }
  //       } catch (error) {
  //         if (error.name === 'AbortError' || downloadCancelled) {
  //           return;
  //         }
  //         console.error(`Error processing node ${node.id}:`, error);
  //       }
  //     }

  //     if (downloadCancelled) return;

  //     if (nodesWithPlots.length === 0) {
  //       notification.close('download-notification');
  //       notification.info({
  //         message: 'No plots to download',
  //         description: 'No nodes with plots were found in the current analysis.',
  //       });
  //       return;
  //     }

  //     totalSteps = nodesWithPlots.reduce((total, node) => total + 1 + node.figures.length, 0);

  //     for (const nodeWithPlots of nodesWithPlots) {
  //       if (downloadCancelled) break;

  //       const folderName = `${nodeWithPlots.id}-${nodeWithPlots.name}`;
  //       const folder = zip.folder(folderName);
  //       if (!folder) {
  //         console.error(`Failed to create folder for node ${nodeWithPlots.id}`);
  //         continue;
  //       }

  //       // 1. Get all predecessor nodes information
  //       try {
  //         updateProgress(0, `Processing node ${nodeWithPlots.id} metadata...`);

  //         const predecessorNodes = flowTool.findPredecessorNodes(nodeWithPlots.id);
  //         let csvContent =
  //           'Node ID,Node Name,Node Type,Computation Resource Configure,System Env,Node Parameters,Description,Document URL,Error Message,Preset Env,Program Language,Source\n';

  //         for (const node of predecessorNodes) {
  //           if (downloadCancelled) {
  //             throw new Error('Download cancelled');
  //           }

  //           let description = 'N/A';
  //           let documentUrl = 'N/A';
  //           let errorMessage = 'N/A';
  //           let presetEnv = 'N/A';
  //           let programLanguage = 'N/A';
  //           let source = 'N/A';
  //           let computationResourceConfigure = 'N/A';
  //           let systemEnv = 'N/A';
  //           let nodeParameters = 'N/A';

  //           if (node.type === 'computation node' && node.id) {
  //             try {
  //               const paramsResponse = await requestNodeParams(node.id);
  //               if (paramsResponse && paramsResponse.data) {
  //                 nodeParameters = `"${JSON.stringify(paramsResponse.data).replace(/"/g, '""')}"`;
  //               }
  //             } catch (e) {
  //               if (downloadCancelled) {
  //                 throw new Error('Download cancelled');
  //               }
  //               console.error(`Error fetching parameters for node ${node.id}:`, e);
  //               nodeParameters = '"Error fetching parameters"';
  //             }
  //           }

  //           if (node.data && node.data.fbId) {
  //             try {
  //               const fbInfo = await requestGetFBInformation(node.data.fbId);

  //               if (fbInfo && fbInfo.data && fbInfo.data.currentVersionInformation) {
  //                 const info = fbInfo.data.currentVersionInformation;
  //                 description = info.description
  //                   ? info.description.replace(/[\r\n]+/g, ' ').trim()
  //                   : 'N/A';
  //                 documentUrl = info.documentUrl || 'N/A';
  //                 errorMessage = info.errorMessage || 'N/A';
  //                 presetEnv = info.presetEnv || 'N/A';
  //                 programLanguage = info.programLanguage || 'N/A';
  //                 source = info.source || 'N/A';
  //               }
  //             } catch (e) {
  //               if (downloadCancelled) {
  //                 throw new Error('Download cancelled');
  //               }
  //               console.error(`Error fetching FB information for node ${node.id}:`, e);
  //               description = 'Error fetching FB information';
  //             }
  //           }

  //           const escapedNodeName = node.data?.label
  //             ? `"${node.data.label.replace(/"/g, '""')}"`
  //             : '""';
  //           const escapedDescription = `"${description.replace(/"/g, '""')}"`;
  //           const escapedDocumentUrl = `"${documentUrl.replace(/"/g, '""')}"`;
  //           const escapedErrorMessage = `"${errorMessage.replace(/"/g, '""')}"`;
  //           const escapedPresetEnv = `"${presetEnv.replace(/"/g, '""')}"`;
  //           const escapedProgramLanguage = `"${programLanguage.replace(/"/g, '""')}"`;
  //           const escapedSource = `"${source.replace(/"/g, '""')}"`;
  //           if (node.data && node.data.computationResourceConfigure) {
  //             computationResourceConfigure = `"${node.data.computationResourceConfigure
  //               .toString()
  //               .replace(/"/g, '""')}"`;
  //           } else {
  //             computationResourceConfigure = 'N/A';
  //           }
  //           if (node.data && node.data.systemEnv) {
  //             systemEnv = `"${node.data.systemEnv.toString().replace(/"/g, '""')}"`;
  //           } else {
  //             systemEnv = 'N/A';
  //           }

  //           csvContent += `${node.id},${escapedNodeName},${node.type},${computationResourceConfigure},${systemEnv},${nodeParameters},${escapedDescription},${escapedDocumentUrl},${escapedErrorMessage},${escapedPresetEnv},${escapedProgramLanguage},${escapedSource}\n`;
  //         }

  //         if (downloadCancelled) {
  //           throw new Error('Download cancelled');
  //         }

  //         // Add current node
  //         const currentNode = flowTool.getNode(nodeWithPlots.id);
  //         let currentDescription = 'N/A';
  //         let currentDocumentUrl = 'N/A';
  //         let currentErrorMessage = 'N/A';
  //         let currentPresetEnv = 'N/A';
  //         let currentProgramLanguage = 'N/A';
  //         let currentSource = 'N/A';
  //         let currentComputationResourceConfigure = 'N/A';
  //         let currentSystemEnv = 'N/A';
  //         let currentNodeParameters = 'N/A';

  //         if (currentNode && currentNode.id) {
  //           try {
  //             const paramsResponse = await requestNodeParams(currentNode.id);
  //             if (paramsResponse && paramsResponse.data) {
  //               currentNodeParameters = `"${JSON.stringify(paramsResponse.data).replace(
  //                 /"/g,
  //                 '""',
  //               )}"`;
  //             }
  //           } catch (e) {
  //             if (downloadCancelled) {
  //               throw new Error('Download cancelled');
  //             }
  //             console.error(`Error fetching parameters for current node ${nodeWithPlots.id}:`, e);
  //             currentNodeParameters = '"Error fetching parameters"';
  //           }
  //         }

  //         if (currentNode && currentNode.data && currentNode.data.fbId) {
  //           try {
  //             const fbInfo = await requestGetFBInformation(currentNode.data.fbId);

  //             if (fbInfo && fbInfo.data && fbInfo.data.currentVersionInformation) {
  //               const info = fbInfo.data.currentVersionInformation;
  //               currentDescription = info.description
  //                 ? info.description.replace(/[\r\n]+/g, ' ').trim()
  //                 : 'N/A';
  //               currentDocumentUrl = info.documentUrl || 'N/A';
  //               currentErrorMessage = info.errorMessage || 'N/A';
  //               currentPresetEnv = info.presetEnv || 'N/A';
  //               currentProgramLanguage = info.programLanguage || 'N/A';
  //               currentSource = info.source || 'N/A';
  //             }
  //           } catch (e) {
  //             if (downloadCancelled) {
  //               throw new Error('Download cancelled');
  //             }
  //             console.error(
  //               `Error fetching FB information for current node ${nodeWithPlots.id}:`,
  //               e,
  //             );
  //             currentDescription = 'Error fetching FB information';
  //           }
  //         }

  //         const escapedNodeName = nodeWithPlots.name
  //           ? `"${nodeWithPlots.name.replace(/"/g, '""')}"`
  //           : '""';
  //         const escapedDescription = `"${currentDescription.replace(/"/g, '""')}"`;
  //         const escapedDocumentUrl = `"${currentDocumentUrl.replace(/"/g, '""')}"`;
  //         const escapedErrorMessage = `"${currentErrorMessage.replace(/"/g, '""')}"`;
  //         const escapedPresetEnv = `"${currentPresetEnv.replace(/"/g, '""')}"`;
  //         const escapedProgramLanguage = `"${currentProgramLanguage.replace(/"/g, '""')}"`;
  //         const escapedSource = `"${currentSource.replace(/"/g, '""')}"`;
  //         if (currentNode.data && currentNode.data.computationResourceConfigure) {
  //           currentComputationResourceConfigure = `"${currentNode.data.computationResourceConfigure
  //             .toString()
  //             .replace(/"/g, '""')}"`;
  //         } else {
  //           currentComputationResourceConfigure = 'N/A';
  //         }
  //         if (currentNode.data && currentNode.data.systemEnv) {
  //           currentSystemEnv = `"${currentNode.data.systemEnv.toString().replace(/"/g, '""')}"`;
  //         } else {
  //           currentSystemEnv = 'N/A';
  //         }

  //         csvContent += `${nodeWithPlots.id},${escapedNodeName},computation node,${currentComputationResourceConfigure},${currentSystemEnv},${currentNodeParameters},${escapedDescription},${escapedDocumentUrl},${escapedErrorMessage},${escapedPresetEnv},${escapedProgramLanguage},${escapedSource}\n`;
  //         folder.file('predecessor_node_information.csv', csvContent);
  //         updateProgress(1, `CSV created for node ${nodeWithPlots.id}`);
  //       } catch (error) {
  //         if (error.message === 'Download cancelled' || downloadCancelled) {
  //           return;
  //         }
  //         console.error(`Error creating CSV for node ${nodeWithPlots.id}:`, error);
  //         folder.file('error_log.txt', `Error creating CSV: ${error.message}`);
  //         updateProgress(1, `Error creating CSV for node ${nodeWithPlots.id}`);
  //       }

  //       // 2. Add plots
  //       try {
  //         for (let i = 0; i < nodeWithPlots.figures.length; i++) {
  //           if (downloadCancelled) break;

  //           const figure = nodeWithPlots.figures[i];
  //           try {
  //             updateProgress(
  //               0,
  //               `Downloading figure ${i + 1}/${nodeWithPlots.figures.length} for node ${
  //                 nodeWithPlots.id
  //               }...`,
  //             );

  //             const figureUrl = await requestGetFigureInfo(figure.chart_uuid);
  //             if (figureUrl) {
  //               const secureUrl = figureUrl.replace(/^http:\/\//i, 'https://');
  //               const response = await fetch(secureUrl, {
  //                 headers: {
  //                   'Cache-Control': 'no-cache, no-store, must-revalidate',
  //                   Pragma: 'no-cache',
  //                   Expires: '0',
  //                 },
  //                 mode: 'cors',
  //                 signal: signal,
  //               });

  //               if (!response.ok) {
  //                 throw new Error(
  //                   `Failed to fetch image: ${response.status} ${response.statusText}`,
  //                 );
  //               }

  //               const blob = await response.blob();
  //               let fileName = figure.chart_name || `plot_${i + 1}`;
  //               fileName = fileName.replace(/[<>:"/\\|?*]/g, '_');
  //               if (!fileName.endsWith('.png')) {
  //                 fileName += '.png';
  //               }
  //               folder.file(fileName, blob);
  //             }
  //             updateProgress(1, `Figure ${i + 1} downloaded for node ${nodeWithPlots.id}`);
  //           } catch (figError) {
  //             if (figError.name === 'AbortError' || downloadCancelled) {
  //               return;
  //             }
  //             console.error(`Error fetching figure ${figure.chart_uuid}:`, figError);
  //             folder.file(
  //               `error_figure_${i + 1}.txt`,
  //               `Error fetching figure: ${figError.message}`,
  //             );
  //             updateProgress(1, `Error fetching figure ${i + 1} for node ${nodeWithPlots.id}`);
  //           }
  //         }
  //       } catch (error) {
  //         if (error.name === 'AbortError' || downloadCancelled) {
  //           return;
  //         }
  //         console.error(`Error adding plots for node ${nodeWithPlots.id}:`, error);
  //         folder.file('error_log.txt', `Error adding plots: ${error.message}`);
  //       }
  //     }

  //     if (downloadCancelled) return;

  //     updateProgress(0, 'Creating ZIP file...');
  //     notification.open({
  //       key: 'download-notification',
  //       message: 'Creating ZIP file...',
  //       description: (
  //         <div>
  //           <div>Finalizing your download. This may take a moment.</div>
  //           <Progress percent={99} status="active" style={{ marginTop: 8 }} />
  //           <div style={{ marginTop: 8, textAlign: 'right' }}>
  //             <Button
  //               size="small"
  //               onClick={() => {
  //                 downloadCancelled = true;
  //                 abortController.abort();
  //                 notification.close('download-notification');
  //                 notification.info({
  //                   message: 'Download cancelled',
  //                   description: 'The download process has been cancelled.',
  //                 });
  //               }}
  //             >
  //               Cancel
  //             </Button>
  //           </div>
  //         </div>
  //       ),
  //       duration: 0,
  //       icon: <Spin />,
  //     });

  //     zip
  //       .generateAsync({ type: 'blob' })
  //       .then((content) => {
  //         if (downloadCancelled) return;

  //         saveAs(content, `${analysisDetail?.name || 'analysis'}_plots.zip`);
  //         notification.close('download-notification');
  //         notification.success({
  //           message: 'Download complete',
  //           description: 'Successfully downloaded plots for {0} nodes.'.replace(
  //             '{0}',
  //             nodesWithPlots.length.toString(),
  //           ),
  //         });
  //       })
  //       .catch((error) => {
  //         if (downloadCancelled) return;

  //         console.error('Error generating zip file:', error);
  //         notification.close('download-notification');
  //         notification.error({
  //           message: 'Download failed',
  //           description: `Error generating zip file: ${error.message}`,
  //         });
  //       });
  //   } catch (error) {
  //     if (
  //       error.name === 'AbortError' ||
  //       error.message === 'Download cancelled' ||
  //       downloadCancelled
  //     ) {
  //       return;
  //     }

  //     console.error('Fatal error in downloadAllPlots:', error);
  //     notification.close('download-notification');
  //     notification.error({
  //       message: 'Download failed',
  //       description: `Error: ${error.message}`,
  //     });
  //   }
  // };

  const userInfoMenu = (
    <Menu>
      <Menu.ItemGroup style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Avatar
            style={{
              backgroundColor: 'rgba(250, 173, 20, 1)',
              marginBottom: '0.5vh',
              display: 'block',
              height: '3vh',
              width: '3vh',
              lineHeight: '3vh',
              fontSize: '1.5vh',
            }}
          >
            {userInfo?.userName ? userInfo.userName.charAt(0).toUpperCase() : ''}
          </Avatar>
        </div>

        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ marginRight: '0.5vh', fontSize: '1.5vh' }}>
            {userInfo?.userName || ''}
          </span>
        </div>
      </Menu.ItemGroup>

      <Menu.ItemGroup>
        <Menu.Item
          key="1"
          icon={<UserOutlined style={{ fontSize: '1.5vh' }} />}
          onClick={() => {
            history.push('/controlCenter/userCenter/nameSetting');
          }}
          style={{ height: '3vh', lineHeight: '3vh', fontSize: '1.5vh' }}
        >
          {dictionary.ACCOUNT_SETTING}
        </Menu.Item>
        <Menu.Item
          key="2"
          icon={<LogoutOutlined style={{ fontSize: '1.5vh' }} />}
          onClick={logout}
          style={{ height: '3vh', lineHeight: '3vh', fontSize: '1.5vh' }}
        >
          {dictionary.LOG_OUT}
        </Menu.Item>
      </Menu.ItemGroup>
    </Menu>
  );

  const guestInfoMenu = (
    <Menu>
      <Menu.ItemGroup style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Avatar
            style={{
              marginBottom: '0.5vh',
              height: '3vh',
              width: '3vh',
              lineHeight: '3vh',
              fontSize: '1.5vh',
            }}
            icon={<UserOutlined style={{ fontSize: '1.5vh' }} />}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ marginRight: '0.5vh', fontSize: '1.5vh' }}>{dictionary.GUEST}</span>
        </div>
      </Menu.ItemGroup>

      <Menu.ItemGroup>
        <Menu.Item
          key="1"
          icon={<LoginOutlined style={{ fontSize: '1.5vh' }} />}
          onClick={() => {
            history.push('/login/byPassword');
          }}
          style={{ height: '3vh', lineHeight: '3vh', fontSize: '1.5vh' }}
        >
          {dictionary.LOG_IN}
        </Menu.Item>
      </Menu.ItemGroup>
    </Menu>
  );

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'flex-start',
        alignItems: 'center',
        height: '5vh',
      }}
    >
      <div>
        <CustomImage
          name={customIconNames.LOGO}
          style={{
            height: '5vh',
            cursor: 'pointer',
            marginTop: '1vh',
            marginLeft: '1vh',
          }}
          onClick={() => {
            history.push('/management/homeMain');
          }}
        />
      </div>
      <div style={{ width: '0.5vh' }} />
      <span style={{ fontSize: '1.5vh' }}>|</span>
      <div style={{ width: '0.5vh' }} />
      <span style={{ fontSize: '1.5vh' }}>{analysisDetail?.name}</span>
      <div style={{ flex: 1.5 }} />
      <CustomTabSwitch
        tabs={[
          { key: '/analysisPanel/flowPanel', label: dictionary.ANALYSIS_PANEL },
          // {
          //   key: '/analysisPanel/workflowReportPanel',
          //   label: (
          //     <div style={{ display: 'flex', alignItems: 'center' }}>
          //       {dictionary.WORKFLOW_REPORT}
          //       {generatedRepoCNT > 0 && (
          //         <button
          //           style={{
          //             alignItems: 'center',
          //             marginLeft: '8px',
          //             padding: '0 10px',
          //             height: '23px',
          //             backgroundColor: '#2A5EE1',
          //             color: 'white',
          //             border: 'none',
          //             fontSize: '12px',
          //             borderRadius: '30px',
          //             lineHeight: '1',
          //           }}
          //         >
          //           {generatedRepoCNT} {dictionary.REPORTS_GENERATED}
          //         </button>
          //       )}
          //     </div>
          //   ),
          // },
        ]}
        activeKey={currentPath}
        onChange={(key: number) => {
          const urlSearch = location.search;
          history.push(`${key}${urlSearch}`);
        }}
      />
      <div style={{ flex: 1 }} />
      <Row gutter={10} align="middle">
        {/* <Col>
          <Button
            style={{
              width: '135px',
              height: '3vh',
              fontSize: '1.5vh',
              padding: '0 1vh',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            type="default"
            onClick={downloadAllPlots}
          >
            {'Download Plots'}
          </Button>
        </Col> */}
        {/* <Col>
          <Divider
            type="vertical"
            style={{
              backgroundColor: 'white',
              height: '3vh',
            }}
          />
        </Col> */}
        <Col>
          <AutoGenieProgressDropdown />
        </Col>
        <Col>
          <Divider
            type="vertical"
            style={{
              backgroundColor: 'white',
              height: '3vh',
            }}
          />
        </Col>
        <Col>
          <Button
            style={{
              width: '68px',
              height: '3vh',
              fontSize: '1.5vh',
              padding: '0 1vh',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            type="primary"
            onClick={() => setAnalysisId(analysisDetail?.id)}
            disabled={isGuestUser}
          >
            {dictionary.SHARE}
          </Button>
        </Col>
        <CollaborativeListAndShareModal
          analysisId={!isGuestUser ? analysisId : null}
          setAnalysisId={setAnalysisId}
        />
        <Col>
          <Divider
            type="vertical"
            style={{
              backgroundColor: 'white',
              height: '3vh',
            }}
          />
        </Col>
        {/* <Col>
          <div
            style={{
              padding: '1px',
              borderRadius: '50%',
              background: 'linear-gradient(to right, rgba(136, 194, 255, 1), rgba(33, 73, 255, 1))',
              transition: 'all 0.3s ease',
            }}
          >
            <Button
              type="text"
              shape="circle"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '3vh',
                height: '3vh',
                minWidth: '3vh',
                minHeight: '3vh',
                padding: 0,
                background: chatbotState.isVisible
                  ? 'linear-gradient(to right, rgba(136, 194, 255, 1), rgba(33, 73, 255, 1)) padding-box, white border-box'
                  : 'white',
                border: chatbotState.isVisible ? 'none' : '1px solid transparent',
                transition: 'all 0.3s ease',
              }}
              onClick={toggleChatbot}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  transform: chatbotState.isVisible ? 'rotate(360deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s ease',
                }}
              >
                {chatbotState.isVisible ? (
                  <CustomImage
                    name={customIconNames.AIICONSTARWHITE}
                    style={{
                      height: '2vh',
                      cursor: 'pointer',
                    }}
                  />
                ) : (
                  <CustomImage
                    name={customIconNames.AIICONSTAR}
                    style={{
                      height: '2vh',
                      cursor: 'pointer',
                    }}
                  />
                )}
              </div>
            </Button>
          </div>
        </Col>
        <Col>
          <Divider
            type="vertical"
            style={{
              backgroundColor: 'white',
              height: '3vh',
            }}
          />
        </Col> */}
        <Col>
          {isGuestUser ? (
            <Dropdown overlay={guestInfoMenu} trigger={['click']} placement="bottomLeft">
              <span>
                <Avatar
                  style={{
                    marginBottom: '4px',
                    cursor: 'pointer',
                    height: '3vh',
                    width: '3vh',
                    lineHeight: '3vh',
                    fontSize: '1.5vh',
                  }}
                  icon={<UserOutlined style={{ fontSize: '1.5vh' }} />}
                />
              </span>
            </Dropdown>
          ) : (
            <Dropdown overlay={userInfoMenu} trigger={['click']} placement="bottomLeft">
              <span>
                <Avatar
                  style={{
                    backgroundColor: 'rgba(250, 173, 20, 1)',
                    marginBottom: '4px',
                    cursor: 'pointer',
                    height: '3vh',
                    width: '3vh',
                    lineHeight: '3vh',
                    fontSize: '1.5vh',
                  }}
                >
                  {userInfo?.userName?.charAt(0).toUpperCase()}
                </Avatar>
              </span>
            </Dropdown>
          )}
        </Col>
        <Col>
          <Divider
            type="vertical"
            style={{
              backgroundColor: 'white',
              height: '3vh',
            }}
          />
        </Col>
      </Row>
    </div>
  );
}
