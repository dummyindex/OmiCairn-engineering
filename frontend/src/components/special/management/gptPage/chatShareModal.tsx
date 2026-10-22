import { Permission, PermissionName } from '@/constants/userRelation';
import { InvitationStatus, type CollaborationInvitation } from '@/interfaces/invitation';
import {
  requestAnalysisUserRelation,
  requestCancelCollaboration,
  requestChangePermission,
  requestCollaborationList,
  requestInviteCollaboration,
  requestToggleAnalysisPublishState,
} from '@/request/analysis';
import { requestSearchUser } from '@/request/user';
import { writeToClipboard } from '@/util/operationTools';
import { UserRelationTool } from '@/util/userRelationTool';
import { CopyOutlined, DeleteOutlined, PlusOutlined, RedoOutlined } from '@ant-design/icons';
import {
  Button,
  Checkbox,
  Divider,
  Form,
  Input,
  message,
  Modal,
  Select,
  Space,
  Switch,
  Table,
} from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';

const { confirm } = Modal;

const AddCollaboratorForm = (props: any) => {
  const { dictionary } = useModel('localization');
  const { isAddModalOpen, setIsAddModalOpen, createCollaboration, excludeUserIdSet } = props;
  const [userList, setUserList] = useState([]);
  const [form] = Form.useForm();

  const onSearchUser = async (keyword: string) => {
    if (!keyword) {
      setUserList([]);
      return;
    }
    const { data: userList } = await requestSearchUser(keyword, 1);
    setUserList(userList);
  };

  const onAdd = async () => {
    await form.validateFields();
    const values = form.getFieldsValue();
    const { users, editable } = values;
    const receiverIdList = users.map((user: any) => user.value);
    const permission = editable
      ? PermissionName[Permission.write]
      : PermissionName[Permission.read];
    createCollaboration(receiverIdList, permission);
    form.resetFields();
    setIsAddModalOpen(false);
  };

  return (
    <Modal
      centered
      title={dictionary.ADD_COLLABORATOR}
      open={isAddModalOpen}
      okText={dictionary.ADD}
      cancelText={dictionary.CANCEL}
      onCancel={() => {
        form.resetFields();
        setIsAddModalOpen(false);
      }}
      onOk={onAdd}
    >
      <Form form={form}>
        <Form.Item
          label="Users"
          name="users"
          rules={[{ required: true, message: 'Please select users!' }]}
        >
          <Select
            labelInValue
            mode="multiple"
            placeholder="Select users"
            filterOption={false}
            onSearch={onSearchUser}
          >
            {userList.map((user: any) => {
              if (excludeUserIdSet.has(user.id)) return null;
              return (
                <Select.Option key={user.id} value={user.id}>
                  {user.userName}
                </Select.Option>
              );
            })}
          </Select>
        </Form.Item>
        <Form.Item label="Editable" name="editable" valuePropName="checked">
          <Checkbox>Editable</Checkbox>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default function ChatShareModal(props: any) {
  const { analysisId, chatId, setAnalysisId, isEditable = true } = props;
  const { userInfo } = useModel('user');
  const { dictionary } = useModel('localization');

  const [isShareStateLoading, setIsShareStateLoading] = useState(false);
  const [isPublic, setIsPublic] = useState(false);

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [invitationList, setInvitationList] = useState<CollaborationInvitation[]>([]);
  const [filteredInvitationList, setFilteredInvitationList] = useState<CollaborationInvitation[]>(
    [],
  );
  const [searchExcludeUserIdSet, setSearchExcludeUserIdSet] = useState(new Set());

  const getDefaultPublic = async () => {
    if (analysisId && !!userInfo) {
      setIsShareStateLoading(true);
      const { data: result } = await requestAnalysisUserRelation(analysisId);
      if (!result) {
        throw Error('Fail to fetch relation list');
      }
      const userRelationTool = new UserRelationTool(userInfo.id, result);
      setIsShareStateLoading(false);
      setIsPublic(userRelationTool.isPublished());
    }
  };

  const loadInvitationList = async () => {
    const { data: collaborationList } = await requestCollaborationList(analysisId);
    setInvitationList(collaborationList);
  };

  const filterInvitationList = () => {
    if (!searchText) {
      setFilteredInvitationList(invitationList);
      return;
    }
    const filteredData = invitationList.filter(
      (user: any) =>
        user.inviteeName && user.inviteeName.toLowerCase().includes(searchText.toLowerCase()),
    );
    setFilteredInvitationList(filteredData);
  };

  useEffect(() => {
    if (analysisId && !!userInfo) {
      getDefaultPublic();
      loadInvitationList();
    }
  }, [analysisId, userInfo]);

  useEffect(() => {
    filterInvitationList();
  }, [searchText, invitationList]);

  useEffect(() => {
    const newSet = new Set();
    if (!!userInfo) {
      newSet.add(userInfo.id);
    }
    if (!!invitationList && invitationList.length > 0) {
      invitationList.forEach((invitation) => {
        newSet.add(invitation.inviteeId);
      });
    }
    setSearchExcludeUserIdSet(newSet);
  }, [invitationList, userInfo]);

  const handleCheckboxChange = async (invitationId: number) => {
    const index = filteredInvitationList.findIndex(
      (invitation: any) => invitation.id === invitationId,
    );
    if (index === -1) return;
    const invitation = filteredInvitationList[index];
    const newPermission =
      Permission[invitation.permission] === Permission.read ? Permission.write : Permission.read;
    const newPermissionName = PermissionName[newPermission];
    await requestChangePermission(invitationId, newPermissionName);
    setInvitationList(
      invitationList.map((item) =>
        item.id === invitationId ? { ...item, permission: newPermissionName } : item,
      ),
    );
  };

  const handleDeleteUser = (invitation_id: string | number) => {
    confirm({
      title: 'Confirm deletion of user?',
      content: 'After deletion, it cannot be restored.',
      async onOk() {
        await requestCancelCollaboration(invitation_id);
        setInvitationList(invitationList.filter((item) => item.id !== invitation_id));
      },
      onCancel() {},
    });
  };

  const publicDatasetChange = async (checked: boolean) => {
    setIsShareStateLoading(true);
    await requestToggleAnalysisPublishState(analysisId, checked);
    setIsShareStateLoading(false);
    setIsPublic(checked);
  };

  const copyLink = () => {
    const host = window.location.host;
    const protocol = window.location.protocol;
    const url = chatId
      ? `${protocol}//${host}/management/gptPage?chatId=${chatId}`
      : `${protocol}//${host}/management/gptPage`;
    writeToClipboard(url)
      .then(() => {
        message.success('Chat link copied');
      })
      .catch(() => {
        console.error('Link cannot be copied');
      });
  };

  const createCollaboration = async (receiverIdList: string[], permission: string) => {
    try {
      await requestInviteCollaboration(analysisId, receiverIdList, permission);
      loadInvitationList();
      message.success('Collaborator invited successfully');
    } catch (e) {
      message.error('Failed to invite collaborator');
    }
  };

  const columns = [
    {
      title: dictionary.NAME,
      dataIndex: 'inviteeName',
      key: 'inviteeName',
    },
    {
      title: dictionary.EDITABLE,
      dataIndex: 'permission',
      key: 'permission',
      render: (permission: string, record: CollaborationInvitation) => {
        const checked = Permission[permission] === Permission.write;
        return <Checkbox checked={checked} onChange={() => handleCheckboxChange(record.id)} />;
      },
    },
    {
      title: dictionary.STATUS,
      dataIndex: 'status',
      key: 'status',
      filters: [
        { text: InvitationStatus.Accepted, value: InvitationStatus.Accepted },
        { text: InvitationStatus.Rejected, value: InvitationStatus.Rejected },
        { text: InvitationStatus.Pending, value: InvitationStatus.Pending },
      ],
      onFilter: (value: string, record) => record.status.indexOf(value) === 0,
    },
    {
      title: dictionary.ACTION,
      key: 'operate',
      render: (text, record) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteUser(record.id)}
          />
        </Space>
      ),
    },
  ];

  return (
    <Modal
      centered
      title="Share Chat"
      open={!!analysisId}
      width="40vw"
      style={{ minWidth: '600px' }}
      footer={null}
      onCancel={() => setAnalysisId(null)}
    >
      <div className="share-section" style={{ marginBottom: '24px' }}>
        <div style={{ marginBottom: '16px' }}>
          {isEditable && (
            <>
              <div style={{ marginBottom: '8px', fontSize: '14px', color: '#666' }}>
                Chat sharing inherits the same permissions as the analysis it belongs to.
              </div>
              {dictionary.PUBLIC} :{' '}
              <Switch
                checked={isPublic}
                onChange={publicDatasetChange}
                loading={isShareStateLoading}
                disabled={!isEditable}
              />
            </>
          )}
        </div>
        <Button size="small" onClick={copyLink} style={{ fontSize: '12px' }}>
          <CopyOutlined /> Copy Chat Link
        </Button>
      </div>

      {isEditable && (
        <>
          <Divider />

          <div className="collaboration-section">
            <AddCollaboratorForm
              isAddModalOpen={isAddModalOpen}
              setIsAddModalOpen={setIsAddModalOpen}
              createCollaboration={createCollaboration}
              excludeUserIdSet={searchExcludeUserIdSet}
            />
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '16px',
              }}
            >
              <div>
                <Button
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setIsAddModalOpen(true);
                  }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center' }}>
                <Input
                  placeholder={dictionary.SEARCH}
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  style={{ width: '300px' }}
                />
                <Button
                  style={{ marginLeft: 16 }}
                  icon={
                    <RedoOutlined
                      style={{
                        transform: 'rotate(-90deg)',
                      }}
                    />
                  }
                  onClick={() => {
                    loadInvitationList();
                  }}
                />
              </div>
            </div>

            <div style={{ height: '40vh', overflow: 'auto' }}>
              <Table
                dataSource={filteredInvitationList}
                columns={columns}
                rowKey="id"
                pagination={{ pageSize: 10 }}
              />
            </div>
          </div>
        </>
      )}
    </Modal>
  );
}
