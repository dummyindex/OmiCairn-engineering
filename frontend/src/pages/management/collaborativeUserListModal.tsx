import { Permission, PermissionName } from '@/constants/userRelation';
import { InvitationStatus, type CollaborationInvitation } from '@/interfaces/invitation';
import {
  requestCancelCollaboration,
  requestChangePermission,
  requestCollaborationList,
  requestInviteCollaboration,
} from '@/request/analysis';
import { requestSearchUser } from '@/request/user';
import { DeleteOutlined, PlusOutlined, RedoOutlined } from '@ant-design/icons';
import { Table, Space, Button, Modal, Checkbox, Input, Form, Select, message } from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';

const { confirm } = Modal;

const AddForm = (props: any) => {
  const { dictionary } = useModel('localization');
  const { isAddModalOpen, setIsAddModalOpen, createCollaboration, excludeUserIdSet } = props;
  const [userList, setUserList] = useState([]); // Stores the user list
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
        {/* Add more form fields as needed */}
      </Form>
    </Modal>
  );
};

export default function CollaborativeUserListModal(props: any) {
  const { userInfo } = useModel('user');
  const { dictionary } = useModel('localization');
  const { cooperatorEditAnalysisId, setCooperatorEditAnalysisId } = props;
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [invitationList, setInvitationList] = useState<CollaborationInvitation[]>([]); // Stores the invitation list
  const [filteredInvitationList, setFilteredInvitationList] = useState<CollaborationInvitation[]>(
    [],
  ); // Stores the filtered invitation list
  const [searchExcludeUserIdSet, setSearchExcludeUserIdSet] = useState(new Set()); // Stores user ids excluded from search

  const loadInvitationList = async () => {
    const { data: collaborationList } = await requestCollaborationList(cooperatorEditAnalysisId);
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
    if (!cooperatorEditAnalysisId) return;
    loadInvitationList();
  }, [cooperatorEditAnalysisId]);

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
        {
          text: InvitationStatus.Accepted,
          value: InvitationStatus.Accepted,
        },
        {
          text: InvitationStatus.Rejected,
          value: InvitationStatus.Rejected,
        },
        {
          text: InvitationStatus.Pending,
          value: InvitationStatus.Pending,
        },
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

  const createCollaboration = async (receiverIdList: string[], permission: string) => {
    try {
      await requestInviteCollaboration(cooperatorEditAnalysisId, receiverIdList, permission);
      loadInvitationList();
      message.success('Collaborator invited successfully');
    } catch (e) {
      message.error('Failed to invite collaborator');
    }
  };

  return (
    <Modal
      centered
      title={dictionary.COLLABORATOR_LIST}
      open={!!cooperatorEditAnalysisId}
      width="40vw"
      style={{ minWidth: '600px' }}
      footer={null}
      onCancel={() => setCooperatorEditAnalysisId(null)}
    >
      <AddForm
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
      <div style={{ height: '61vh', overflow: 'auto' }}>
        <Table
          dataSource={filteredInvitationList}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }} // Custom number of rows per page
        />
      </div>
    </Modal>
  );
}
