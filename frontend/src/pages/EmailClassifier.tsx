import React, { useState } from 'react';
import { 
  Upload, 
  Card, 
  Typography, 
  List, 
  Tag, 
  Space, 
  Spin,
  message 
} from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { RcFile } from 'antd/lib/upload';
import { uploadEmailFile } from '../services/api';

const { Dragger } = Upload;
const { Title, Text } = Typography;

interface ClassificationResult {
  classification: string;
  confidence: number;
  method: string;
  explanation: string;
}

interface EmailContent {
  subject?: string;
  from?: string;
  body: string;
}

interface EmailFile {
  id: number;
  file_name: string;
  file_type: string;
  email_content: EmailContent;
  classification_result: ClassificationResult;
  processed: boolean;
  processing_time: number;
}

const EmailClassifier: React.FC = () => {
  const [files, setFiles] = useState<EmailFile[]>([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (file: RcFile) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await uploadEmailFile(formData);
      setFiles(prevFiles => [...prevFiles, response.data]);
      message.success(`${file.name} file uploaded successfully`);
    } catch (error: any) {
      message.error(`${file.name} upload failed: ${error?.message || 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
    return false;
  };

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.eml,.msg,.txt,.html,.oft',
    beforeUpload: handleUpload,
    showUploadList: false,
  };

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>邮件分类</Title>
      
      <Dragger {...uploadProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持 .eml, .msg, .txt, .html, .oft 格式文件
        </p>
      </Dragger>

      {loading && (
        <div style={{ textAlign: 'center', margin: '24px' }}>
          <Spin tip="处理中..." />
        </div>
      )}

      <List
        style={{ marginTop: '24px' }}
        dataSource={files}
        renderItem={(file) => (
          <List.Item>
            <Card style={{ width: '100%' }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <Text strong>文件名:</Text>
                  <Text>{file.file_name}</Text>
                  <Tag color="blue">{file.file_type}</Tag>
                </Space>

                {/* 只有 eml/msg 等邮件格式才显示发件人和主题 */}
                {file.email_content && (file.file_type === 'eml' || file.file_type === 'msg') && (
                  <>
                    {file.email_content.from && (
                      <Space>
                        <Text strong>发件人:</Text>
                        <Text>{file.email_content.from}</Text>
                      </Space>
                    )}
                    {file.email_content.subject && (
                      <Space>
                        <Text strong>主题:</Text>
                        <Text>{file.email_content.subject}</Text>
                      </Space>
                    )}
                  </>
                )}

                {file.classification_result && (
                  <>
                    <Space>
                      <Text strong>分类:</Text>
                      <Tag color="green">{file.classification_result.classification}</Tag>
                      <Text strong>置信度:</Text>
                      <Text>{(file.classification_result.confidence * 100).toFixed(2)}%</Text>
                      <Text strong>方法:</Text>
                      <Tag>{file.classification_result.method}</Tag>
                    </Space>
                    <Space>
                      <Text strong>说明:</Text>
                      <Text>{file.classification_result.explanation}</Text>
                    </Space>
                  </>
                )}

                <Space>
                  <Text strong>处理时间:</Text>
                  <Text>{file.processing_time.toFixed(3)}秒</Text>
                </Space>
              </Space>
            </Card>
          </List.Item>
        )}
      />
    </div>
  );
};

export default EmailClassifier; 