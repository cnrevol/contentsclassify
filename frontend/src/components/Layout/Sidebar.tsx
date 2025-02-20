import React from 'react';
import { Layout, Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import {
  FileTextOutlined,
  MailOutlined,
  SettingOutlined,
  DashboardOutlined
} from '@ant-design/icons';
import type { MenuProps } from 'antd';

const { Sider } = Layout;

type MenuItem = Required<MenuProps>['items'][number];

const Sidebar: React.FC = () => {
  const location = useLocation();

  const menuItems: MenuItem[] = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: <Link to="/">Dashboard</Link>
    },
    {
      key: 'content-classifier',
      icon: <FileTextOutlined />,
      label: <Link to="/content-classifier">Content Classifier</Link>
    },
    {
      key: 'email-classifier',
      icon: <MailOutlined />,
      label: <Link to="/email-classifier">Email Classifier</Link>
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: <Link to="/settings">Settings</Link>
    }
  ];

  const selectedKey = location.pathname === '/' 
    ? 'dashboard' 
    : location.pathname.slice(1);

  return (
    <Sider
      width={200}
      style={{
        background: '#fff',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0
      }}
    >
      <div style={{ height: '64px', padding: '16px', textAlign: 'center' }}>
        <h2 style={{ margin: 0 }}>AI Classifier</h2>
      </div>
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        style={{ height: 'calc(100% - 64px)', borderRight: 0 }}
        items={menuItems}
      />
    </Sider>
  );
};

export default Sidebar;