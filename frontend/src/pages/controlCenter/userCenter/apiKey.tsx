import React, { useState, useEffect } from 'react';
import { Table, Input, Button, message, Popconfirm, Space, Form } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import style from '../index.less';
import { createAPIKey, getAPIKeys, updateAPIKey, deleteAPIKey } from '@/request/apiKey';

interface APIKey {
  id: string;
  createdTime: string;
  name: string;
  value: string;
}

const APIKeyManagement = () => {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  // Load data
  const loadKeys = async () => {
    setLoading(true);
    try {
      const response = await getAPIKeys();

      // Handle different response structures
      let data;
      if (response?.data) {
        data = response.data;
      } else {
        data = [];
      }

      setKeys(data);
    } catch (error) {
      console.error('Error loading API keys:', error);
      message.error('Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKeys();
  }, []);

  // Create new key
  const handleCreate = async (values: { name: string; value: string }) => {
    try {
      const response = await createAPIKey({ name: values.name, value: values.value });

      // Handle different response structures
      let newKey;
      if (response?.data) {
        newKey = response.data;
      } else {
        throw new Error('Unexpected response structure');
      }

      setKeys([newKey, ...keys]);
      setShowCreateForm(false);
      createForm.resetFields();
      message.success('API key created successfully');
    } catch (error) {
      console.error('Error creating API key:', error);
      message.error('Failed to create API key');
    }
  };

  // Edit key
  const handleEdit = (record: APIKey) => {
    setEditingId(record.id);
    editForm.setFieldsValue({
      [`name_${record.id}`]: record.name,
      [`value_${record.id}`]: record.value,
    });
  };

  // Save edit
  const handleSave = async (id: string) => {
    try {
      const name = editForm.getFieldValue(`name_${id}`);
      const value = editForm.getFieldValue(`value_${id}`);

      await updateAPIKey(id, { name, value });

      setKeys(keys.map((key) => (key.id === id ? { ...key, name, value } : key)));
      setEditingId(null);
      message.success('API key updated successfully');
    } catch (error) {
      console.error('Error updating API key:', error);
      message.error('Failed to update API key');
    }
  };

  // Cancel edit
  const handleCancel = () => {
    setEditingId(null);
    editForm.resetFields();
  };

  // Delete key
  const handleDelete = async (id: string) => {
    try {
      await deleteAPIKey(id);
      setKeys(keys.filter((key) => key.id !== id));
      message.success('API key deleted successfully');
    } catch (error) {
      console.error('Error deleting API key:', error);
      message.error('Failed to delete API key');
    }
  };

  // Format API key display
  const formatApiKeyDisplay = (value: string) => {
    if (!value || value.length <= 8) {
      return value; // If too short, return as is
    }
    const prefix = value.substring(0, 4);
    const suffix = value.substring(value.length - 4);
    const stars = '****************'; // Fixed 16 stars
    return `${prefix}${stars}${suffix}`;
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: APIKey) => {
        if (editingId === record.id) {
          return (
            <Form.Item
              name={`name_${record.id}`}
              style={{ margin: 0 }}
              rules={[{ required: true, message: 'Please enter name' }]}
            >
              <Input placeholder="Enter name" />
            </Form.Item>
          );
        }
        return text;
      },
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      render: (text: string, record: APIKey) => {
        if (editingId === record.id) {
          return (
            <Form.Item
              name={`value_${record.id}`}
              style={{ margin: 0 }}
              rules={[{ required: true, message: 'Please enter value' }]}
            >
              <Input.Password placeholder="Enter API key" />
            </Form.Item>
          );
        }
        return formatApiKeyDisplay(text);
      },
    },
    {
      title: 'Created Time',
      dataIndex: 'createdTime',
      key: 'createdTime',
      width: 180,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_, record: APIKey) => {
        if (editingId === record.id) {
          return (
            <Space>
              <Button
                icon={<SaveOutlined />}
                size="small"
                type="primary"
                onClick={() => handleSave(record.id)}
              >
                Save
              </Button>
              <Button icon={<CloseOutlined />} size="small" onClick={handleCancel}>
                Cancel
              </Button>
            </Space>
          );
        }

        return (
          <Space>
            <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)}>
              Edit
            </Button>
            <Popconfirm
              title="Are you sure to delete this key?"
              onConfirm={() => handleDelete(record.id)}
              okText="Yes"
              cancelText="No"
            >
              <Button icon={<DeleteOutlined />} size="small" danger>
                Delete
              </Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  const CreateForm = () => (
    <Form form={createForm} onFinish={handleCreate} style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        <Form.Item
          name="name"
          style={{ flex: 1, margin: 0 }}
          rules={[{ required: true, message: 'Please enter name' }]}
        >
          <Input placeholder="Enter key name" />
        </Form.Item>
        <Form.Item
          name="value"
          style={{ flex: 2, margin: 0 }}
          rules={[{ required: true, message: 'Please enter API key' }]}
        >
          <Input.Password placeholder="Enter API key value" />
        </Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
            Save
          </Button>
          <Button
            onClick={() => {
              setShowCreateForm(false);
              createForm.resetFields();
            }}
            icon={<CloseOutlined />}
          >
            Cancel
          </Button>
        </Space>
      </div>
    </Form>
  );

  return (
    <div className={style.box}>
      <div className={style.card}>
        <div className={style.title}>API Keys Management</div>
        <div className={style.content}>
          <div style={{ marginBottom: 16 }}>
            {!showCreateForm ? (
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setShowCreateForm(true)}
              >
                Add New Key
              </Button>
            ) : (
              <CreateForm />
            )}
          </div>

          <Form form={editForm}>
            <Table
              columns={columns}
              dataSource={keys}
              loading={loading}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `Total ${total} items`,
              }}
            />
          </Form>
        </div>
      </div>
    </div>
  );
};

export default APIKeyManagement;
