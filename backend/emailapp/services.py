import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime
from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import models
from .models import EmailMessage, EmailAttachment, EmailFile, EmailClassificationRule, EmailAccount
from classifier.services import ContentClassificationService
from typing import Dict, Any, List, Optional
from email import policy
from email.parser import BytesParser
import time
import logging

logger = logging.getLogger(__name__)

class EmailFetchService:
    def __init__(self):
        pass
        
    def fetch_emails(self, account: EmailAccount) -> Dict[str, Any]:
        """Fetch emails from the specified email account"""
        try:
            # Connect to email server
            if account.server_type == 'imap':
                mail = imaplib.IMAP4_SSL(account.server_host, account.server_port)
                mail.login(account.username, account.password)
                
                # Select inbox
                mail.select('INBOX')
                
                # Search for all emails
                _, messages = mail.search(None, 'ALL')
                
                results = {
                    'fetched': 0,
                    'errors': []
                }
                
                for num in messages[0].split():
                    try:
                        # Fetch email message
                        _, msg = mail.fetch(num, '(RFC822)')
                        email_body = msg[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Get email details
                        subject = self._decode_email_header(email_message['subject'])
                        from_addr = self._decode_email_header(email_message['from'])
                        date_str = email_message['date']
                        received_date = email.utils.parsedate_to_datetime(date_str)
                        
                        # Create EmailMessage instance
                        message = EmailMessage.objects.create(
                            account=account,
                            message_id=email_message['message-id'],
                            subject=subject,
                            sender=from_addr,
                            recipients=self._get_recipients(email_message),
                            content=self._get_email_content(email_message),
                            received_date=received_date
                        )
                        
                        # Process attachments
                        self._process_attachments(message, email_message)
                        
                        results['fetched'] += 1
                        
                    except Exception as e:
                        results['errors'].append(str(e))
                
                # Update last checked timestamp
                account.last_checked = timezone.now()
                account.save()
                
                return results
                
            else:
                raise ValueError(f"Unsupported server type: {account.server_type}")
                
        except Exception as e:
            raise Exception(f"Failed to fetch emails: {str(e)}")
            
    def _decode_email_header(self, header):
        """Decode email header"""
        if header is None:
            return ''
            
        decoded_header = decode_header(header)
        header_parts = []
        
        for part, encoding in decoded_header:
            if isinstance(part, bytes):
                try:
                    if encoding:
                        header_parts.append(part.decode(encoding))
                    else:
                        header_parts.append(part.decode())
                except:
                    header_parts.append(part.decode('utf-8', 'ignore'))
            else:
                header_parts.append(part)
                
        return ' '.join(header_parts)
        
    def _get_recipients(self, email_message):
        """Get all recipients from email message"""
        recipients = {
            'to': self._decode_email_header(email_message['to']),
            'cc': self._decode_email_header(email_message['cc']),
            'bcc': self._decode_email_header(email_message['bcc'])
        }
        return recipients
        
    def _get_email_content(self, email_message):
        """Extract email content"""
        content = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        content.append(part.get_payload(decode=True).decode())
                    except:
                        content.append(part.get_payload(decode=True).decode('utf-8', 'ignore'))
        else:
            try:
                content.append(email_message.get_payload(decode=True).decode())
            except:
                content.append(email_message.get_payload(decode=True).decode('utf-8', 'ignore'))
                
        return '\n'.join(content)
        
    def _process_attachments(self, message, email_message):
        """Process email attachments"""
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
                
            if part.get('Content-Disposition') is None:
                continue
                
            filename = part.get_filename()
            if filename:
                # Decode filename if needed
                filename = self._decode_email_header(filename)
                
                # Create attachment
                attachment = EmailAttachment(
                    email=message,
                    file_name=filename,
                    content_type=part.get_content_type(),
                    size=len(part.get_payload(decode=True))
                )
                
                # Save attachment file
                content = part.get_payload(decode=True)
                attachment.file.save(filename, ContentFile(content), save=True)

class EmailProcessingService:
    def __init__(self):
        self.classification_service = ContentClassificationService()

    def process_email_content(self, email_content: str) -> Dict[str, Any]:
        """Process email content string through classification pipeline"""
        start_time = time.time()
        
        try:
            # Run classification pipeline
            classification_result = self._classify_email_content(email_content)
            
            return classification_result
            
        except Exception as e:
            logger.error(f"Error processing email content: {str(e)}")
            return {
                'classification': 'Error',
                'confidence': 0.0,
                'method': 'error',
                'error': str(e)
            }
    
    def _classify_email_content(self, content: str) -> Dict[str, Any]:
        """Classify email content using classification service"""
        classifier = ContentClassificationService()
        return classifier.classify_content(content, content_type='text')
        
    def process_email_file(self, email_file: EmailFile) -> Dict[str, Any]:
        """Process uploaded email file through classification pipeline"""
        start_time = time.time()
        
        try:
            # Extract email content
            email_content = self._extract_email_content(email_file.file)
            logger.info(f"Extracted email content: {email_content}")
            
            # 存储邮件内容
            email_file.email_content = email_content
            email_file.save()
            
            # Run classification pipeline
            classification_result = self._classify_email(email_file)
            
            # Update processing metadata
            email_file.processing_time = time.time() - start_time
            email_file.classification_result = classification_result
            email_file.processed = True
            email_file.save()
            
            return classification_result
            
        except Exception as e:
            logger.error(f"Error processing email file {email_file.id}: {str(e)}")
            return {
                'classification': 'Error',
                'confidence': 0.0,
                'method': 'error',
                'error': str(e)
            }
    
    def _get_email_body(self, msg) -> str:
        """Extract email body text with encoding handling"""
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        # 尝试使用消息指定的编码
                        charset = part.get_content_charset() or 'utf-8'
                        payload = part.get_payload(decode=True)
                        body += payload.decode(charset, errors='replace')
                    except (UnicodeDecodeError, AttributeError):
                        try:
                            # 如果失败，尝试其他常见编码
                            for encoding in ['utf-8', 'gbk', 'gb2312', 'iso-8859-1']:
                                try:
                                    body += payload.decode(encoding)
                                    break
                                except UnicodeDecodeError:
                                    continue
                        except:
                            # 如果所有尝试都失败，使用 replace 模式
                            body += payload.decode('utf-8', errors='replace')
        else:
            try:
                # 尝试使用消息指定的编码
                charset = msg.get_content_charset() or 'utf-8'
                payload = msg.get_payload(decode=True)
                body = payload.decode(charset, errors='replace')
            except (UnicodeDecodeError, AttributeError):
                try:
                    # 如果失败，尝试其他常见编码
                    for encoding in ['utf-8', 'gbk', 'gb2312', 'iso-8859-1']:
                        try:
                            body = payload.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                except:
                    # 如果所有尝试都失败，使用 replace 模式
                    body = payload.decode('utf-8', errors='replace')
        return body

    def _extract_email_content(self, file) -> Dict[str, Any]:
        """Extract content from email file based on type"""
        file_path = file.path
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        try:
            if ext in ['.eml', '.msg']:
                with open(file_path, 'rb') as fp:
                    msg = BytesParser(policy=policy.default).parse(fp)
                    
                # 提取邮件内容
                content = {
                    'subject': msg.get('subject', ''),
                    'from': msg.get('from', ''),
                    'to': msg.get('to', ''),
                    'date': msg.get('date', ''),
                    'body': self._get_email_body(msg),
                    'attachments': self._get_attachments_info(msg)
                }
            else:
                # 处理文本/HTML文件
                encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1']
                content = None
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = {
                                'body': f.read(),
                                'attachments': []
                            }
                        break
                    except UnicodeDecodeError:
                        continue
                        
                if content is None:
                    with open(file_path, 'rb') as f:
                        content = {
                            'body': f.read().decode('utf-8', errors='replace'),
                            'attachments': []
                        }
                    
            logger.info(f"Extracted email content: {content}")
            return content
        except Exception as e:
            logger.error(f"Error extracting content from file {file_path}: {str(e)}")
            return {
                'subject': '',
                'from': '',
                'to': '',
                'date': '',
                'body': f'Error extracting content: {str(e)}',
                'attachments': []
            }

    def _get_attachments_info(self, msg) -> List[Dict[str, Any]]:
        """Get information about email attachments"""
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                    
                filename = part.get_filename()
                if filename:
                    size = len(part.get_payload(decode=True))
                    attachments.append({
                        'filename': filename,
                        'size': size,
                        'type': part.get_content_type()
                    })
        return attachments

    def _update_email_metadata(self, email_file: EmailFile, content: Dict[str, Any]):
        """Update email file with extracted content"""
        email_file.subject = content.get('subject', '')
        email_file.sender = content.get('from', '')
        email_file.recipient = content.get('to', '')
        email_file.body_text = content.get('body', '')
        
        attachments = content.get('attachments', [])
        email_file.attachment_count = len(attachments)
        email_file.total_attachment_size = sum(a['size'] for a in attachments)
        
        # email_file.metadata.update({
        #     'extracted_content': content
        # })
        
        email_file.save()

    def _classify_email(self, email_file: EmailFile) -> Dict[str, Any]:
        """Run email through classification pipeline"""
        # 1. Rule Engine
        rule_result = self._apply_rules(email_file)
        if rule_result:
            email_file.classification_level = 'rule'
            email_file.confidence_score = 1.0
            return rule_result

        # 2. FastText Model
        fasttext_result = self._apply_fasttext(email_file)
        if fasttext_result and fasttext_result['confidence'] >= settings.FASTTEXT_THRESHOLD:
            email_file.classification_level = 'fasttext'
            email_file.confidence_score = fasttext_result['confidence']
            return fasttext_result

        # 3. BERT Model
        bert_result = self._apply_bert(email_file)
        if bert_result and bert_result['confidence'] >= settings.BERT_THRESHOLD:
            email_file.classification_level = 'bert'
            email_file.confidence_score = bert_result['confidence']
            return bert_result

        # 4. LLM Model
        llm_result = self._apply_llm(email_file)
        email_file.classification_level = 'llm'
        email_file.confidence_score = llm_result['confidence']
        return llm_result

    def _apply_rules(self, email_file: EmailFile) -> Optional[Dict[str, Any]]:
        """Apply rule-based classification"""
        try:
            rules = EmailClassificationRule.objects.filter(is_active=True).order_by('-priority')
            logger.info(f"Found {rules.count()} active rules")
            
            # 使用 email_content 而不是 classification_result
            email_content = email_file.email_content
            logger.info(f"Applying rules to content: {email_content}")
            
            for rule in rules:
                matched_reasons = []
                
                # 检查发件人域名
                if rule.sender_domains:
                    sender = email_content.get('from', '')
                    if '@' in sender:
                        sender_domain = sender.split('@')[1].lower()
                        if sender_domain in rule.sender_domains:
                            logger.debug(f"Rule {rule.name}: Sender domain {sender_domain} matched")
                            matched_reasons.append(f'Sender domain {sender_domain} matched')
                
                # 检查主题关键词
                if rule.subject_keywords:
                    subject = email_content.get('subject', '').lower()
                    matched_keywords = [kw for kw in rule.subject_keywords if kw.lower() in subject]
                    if matched_keywords:
                        logger.debug(f"Rule {rule.name}: Subject keywords matched: {matched_keywords}")
                        matched_reasons.append(f'Subject contains keywords: {matched_keywords}')
                
                # 检查正文关键词
                if rule.body_keywords:
                    body = email_content.get('body', '').lower()
                    matched_keywords = [kw for kw in rule.body_keywords if kw.lower() in body]
                    if matched_keywords:
                        logger.debug(f"Rule {rule.name}: Body keywords matched: {matched_keywords}")
                        matched_reasons.append(f'Body contains keywords: {matched_keywords}')
                
                # 检查附件数量
                attachments = email_content.get('attachments', [])
                attachment_count = len(attachments)
                if (rule.min_attachments > 0 and attachment_count >= rule.min_attachments):
                    matched_reasons.append(f'Attachment count ({attachment_count}) >= {rule.min_attachments}')
                if (rule.max_attachments and attachment_count <= rule.max_attachments):
                    matched_reasons.append(f'Attachment count ({attachment_count}) <= {rule.max_attachments}')
                
                # 检查附件大小
                total_size = sum(a.get('size', 0) for a in attachments)
                if (rule.min_attachment_size > 0 and total_size >= rule.min_attachment_size):
                    matched_reasons.append(f'Total attachment size ({total_size}) >= {rule.min_attachment_size}')
                if (rule.max_attachment_size and total_size <= rule.max_attachment_size):
                    matched_reasons.append(f'Total attachment size ({total_size}) <= {rule.max_attachment_size}')
                
                # 如果有任何条件匹配
                if matched_reasons:
                    logger.info(f"Rule {rule.name} matched: {matched_reasons}")
                    return {
                        'classification': rule.classification,
                        'confidence': 1.0,
                        'method': 'Decision Tree',
                        'rule_name': rule.name,
                        'explanation': ', '.join(matched_reasons)
                    }
                else:
                    logger.debug(f"Rule {rule.name} did not match any conditions")
            
            logger.info("No rules matched")
            return None
            
        except Exception as e:
            logger.error(f"Error applying rules: {str(e)}")
            return None

    def _apply_fasttext(self, email_file: EmailFile) -> Optional[Dict[str, Any]]:
        """Apply FastText classification"""
        try:
            # 从 email_content 获取内容
            email_content = email_file.email_content or {}
            subject = email_content.get('subject', '')
            body = email_content.get('body', '')
            content = f"Subject: {subject}\n\nBody: {body}"
            
            # 使用通用的分类方法
            result = self._classify_with_provider(content, 'fasttext')
            
            # 检查置信度是否达到阈值
            if result and result['confidence'] >= settings.FASTTEXT_THRESHOLD:
                return result
            
            logger.info(f"FastText confidence {result['confidence']} below threshold {settings.FASTTEXT_THRESHOLD}")
            return None
            
        except Exception as e:
            logger.error(f"Error in FastText classification: {str(e)}")
            return None

    def _classify_with_provider(self, content: str, provider: str) -> Dict[str, Any]:
        """
        使用指定的 provider 对内容进行分类
        
        Args:
            content (str): 要分类的内容
            provider (str): 使用的提供商 ('bert', 'deepseek', etc.)
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        try:
            # 临时切换到指定的 provider
            original_provider = self.classification_service.provider_name
            self.classification_service.update_provider(provider)
            
            logger.info(f"Classifying content with provider {provider}")
            results = self.classification_service.classify_content(content, 'email')
            
            # 恢复原来的 provider
            self.classification_service.update_provider(original_provider)
            
            if results:
                result = results[0]  # Get first classification result
                return {
                    'classification': result['classification'],
                    'confidence': result['confidence'],
                    'method': provider,
                    'explanation': result.get('explanation', '')
                }
            
            logger.warning(f"{provider} classification returned no results")
            return {
                'classification': 'Uncategorized',
                'confidence': 0.0,
                'method': provider,
                'explanation': f'{provider} classification failed'
            }
            
        except Exception as e:
            logger.error(f"Error in {provider} classification: {str(e)}")
            return {
                'classification': 'Error',
                'confidence': 0.0,
                'method': provider,
                'explanation': f'Error during classification: {str(e)}'
            }

    def _apply_bert(self, email_file: EmailFile) -> Optional[Dict[str, Any]]:
        """Apply BERT classification"""
        email_content = email_file.email_content or {}
        subject = email_content.get('subject', '')
        body = email_content.get('body', '')
        content = f"Subject: {subject}\n\nBody: {body}"
        
        return self._classify_with_provider(content, 'bert')

    def _apply_llm(self, email_file: EmailFile) -> Dict[str, Any]:
        """Apply LLM classification using deepseek"""
        email_content = email_file.email_content or {}
        subject = email_content.get('subject', '')
        body = email_content.get('body', '')
        content = f"Subject: {subject}\n\nBody: {body}"
        
        return self._classify_with_provider(content, 'deepseek')