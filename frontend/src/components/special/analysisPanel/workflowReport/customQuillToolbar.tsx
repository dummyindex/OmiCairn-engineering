import { Button } from 'antd';
import { DownloadOutlined, SaveOutlined } from '@ant-design/icons';
import { useModel } from 'umi';
import 'react-quill/dist/quill.snow.css';
import './index.css';

const CustomQuillToolbar = ({ onDownloadAsPdf, onSaveContent }) => {
  const { dictionary } = useModel('localization');
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-start',
        backgroundColor: 'white',
        padding: '0.3em 1em',
      }}
    >
      <div
        id="toolbar"
        style={{
          border: 'none',
          backgroundColor: 'transparent',
        }}
      >
        {/* <select className="ql-header" defaultValue={''} onChange={(e) => e.persist()}>
          <option value="1" />
          <option value="2" />
          <option selected />
        </select> */}
        <select className="ql-size" defaultValue={''} onChange={(e) => e.persist()}>
          <option value="small" />
          <option value="large" />
          <option value="huge" />
          <option selected />
        </select>
        <button className="ql-bold" />
        <button className="ql-italic" />
        <button className="ql-underline" />
        <button className="ql-strike" />
        <button className="ql-list" value="ordered" />
        <button className="ql-list" value="bullet" />
        <button className="ql-indent" value="-1" />
        <button className="ql-indent" value="+1" />
        <button className="ql-link" />
        <button className="ql-image" />
        <select className="ql-color">
          <option value="red" />
          <option value="green" />
          <option value="blue" />
          <option value="orange" />
          <option value="violet" />
          <option value="#d0d1d2" />
          <option selected />
        </select>
      </div>
      <div
        style={{
          flex: 1,
        }}
      />
      <Button type="text" icon={<SaveOutlined />} onClick={onSaveContent}>
        {dictionary.SAVE}
      </Button>
      <Button type="text" icon={<DownloadOutlined />} onClick={onDownloadAsPdf}>
        {dictionary.DOWNLOAD}
      </Button>
    </div>
  );
};

export default CustomQuillToolbar;
