import { DownloadOutlined } from '@ant-design/icons';
import { Button, Dropdown, Menu } from 'antd';
import domToImage from 'dom-to-image';
import jsPDF from 'jspdf';

const handleDownloadByPng = (div: any, name: string) => {
  // Get the div element to capture
  if (div) {
    domToImage
      .toPng(div)
      .then(function (dataURL) {
        // Create a hidden <a> element
        const link = document.createElement('a');
        link.href = dataURL;

        // Set the file name (modify as needed)
        link.download = name + '.png'; // Save as .png

        // Simulate a click on the download link
        link.click();
      })
      .catch(function (error) {
        console.error('Failed to capture div:', error);
      });
  }
};

const handleDownloadBySvg = (div: any, name: string) => {
  // Get the div element to capture
  if (div) {
    // Use dom-to-image to capture the div and generate an image data URL
    domToImage
      .toSvg(div)
      .then(function (dataURL) {
        // Create a hidden <a> element
        const link = document.createElement('a');
        link.href = dataURL;

        // Set the file name (modify as needed)
        link.download = name + '.svg'; // Save as .svg

        // Simulate a click on the download link
        link.click();
      })
      .catch(function (error) {
        console.error('Failed to capture div:', error);
      });
  }
};

const handleDownloadByPdf = async (div: any, name: string) => {
  // Get the div element to capture
  if (div) {
    try {
      // Convert the DOM element to an image
      const imageDataURL = await domToImage.toPng(div);

      // Create a new jsPDF instance
      const pdf = new jsPDF();
      const image = new Image();
      image.src = imageDataURL;

      image.onload = () => {
        const dpi = 96; // Assume the image DPI is 96

        // Convert the image pixel dimensions to PDF point dimensions
        const imageWidthInPoints = (image.width * 72) / dpi / 4;
        const imageHeightInPoints = (image.height * 72) / dpi / 4;

        // Add the image to the PDF
        pdf.addImage(imageDataURL, 'PNG', 0, 0, imageWidthInPoints, imageHeightInPoints);

        // Save the PDF file
        pdf.save(name + '.pdf');
      };
    } catch (error) {
      console.error('Error generating PDF:', error);
    }
  }
};

const SaveGraph = (props: any) => {
  const { onclick } = props;

  const downloadGraph = async (downloadMode) => {
    // const value = await form.validateFields();
    const value = 'figure';
    const div = onclick();
    setTimeout(function () {
      // Code to run after the delay
      if (downloadMode === 'png') {
        handleDownloadByPng(div, value);
      } else if (downloadMode === 'svg') {
        handleDownloadBySvg(div, value);
      } else if (downloadMode === 'pdf') {
        handleDownloadByPdf(div, value);
      }
    }, 2000);
  };

  const menu = (
    <Menu
      onClick={(e: any) => {
        const { domEvent, key } = e;
        domEvent.stopPropagation();
        if (key === '1') {
          // openSaveModal();
          downloadGraph('svg');
        } else if (key === '2') {
          // openSaveAutoModal();
          downloadGraph('png');
        } else if (key === '3') {
          // openSaveAutoModal();
          downloadGraph('pdf');
        }
      }}
    >
      <Menu.Item key="1">Download as SVG</Menu.Item>
      <Menu.Item key="2">Download as PNG</Menu.Item>
      <Menu.Item key="3">Download as PDF</Menu.Item>
    </Menu>
  );

  return (
    <div
      style={{
        marginLeft: '0.2vw',
        marginRight: '0.2vw',
      }}
    >
      {/* <Button onClick={openDialog} icon={<DownloadOutlined style={{ color: '#888' }} />} />  */}
      <Dropdown overlay={menu} trigger={['click']}>
        <Button icon={<DownloadOutlined style={{ color: '#888' }} />} />
      </Dropdown>
      {/* <Modal
        title="download name"
        centered
        open={dialogOpen}
        onCancel={closeDialog}
        onOk={() => {
          downloadGraph();
          closeDialog();
        }}
      >
        <Form form={form} initialValues={{ remember: true }} autoComplete="off">
          <Form.Item
            label="name"
            name="name"
            rules={[{ required: true, message: 'Please input name!' }]}
          >
            <Input />
          </Form.Item>
        </Form>
      </Modal> */}
    </div>
  );
};

export default SaveGraph;
