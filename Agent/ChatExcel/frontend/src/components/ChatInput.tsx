import { useState, useRef } from 'react';
import { PlusOutlined, SendOutlined, FileExcelOutlined, CloseOutlined } from '@ant-design/icons';
import { message } from 'antd';
import { uploadFile } from '../api/client';
import type { FileInfo } from '../types';

type UploadedFileInfo = FileInfo & { size?: number };

interface Props {
  onSend: (input: string, fileInfo: FileInfo | null, fileList?: UploadedFileInfo[]) => void;
  disabled?: boolean;
  disableUpload?: boolean;
  chatMode?: string;
  onFileUploaded?: (fileInfo: FileInfo) => void;
  convUid?: string;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function ProgressRing({ percent, size = 28, strokeWidth = 3 }: { percent: number; size?: number; strokeWidth?: number }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="#e5e7eb"
        strokeWidth={strokeWidth}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="#60a5fa"
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.3s ease' }}
      />
    </svg>
  );
}

export default function ChatInput({
  onSend,
  disabled,
  disableUpload,
  chatMode = 'chat_excel',
  onFileUploaded,
  convUid = '',
}: Props) {
  const [input, setInput] = useState('');
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [fileList, setFileList] = useState<UploadedFileInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadProgress(0);

    let simulated = 0;
    const progressTimer = setInterval(() => {
      simulated = Math.min(simulated + Math.random() * 15, 90);
      setUploadProgress(Math.round(simulated));
    }, 200);

    try {
      const result = await uploadFile(file, chatMode, 'default', convUid);
      clearInterval(progressTimer);
      setUploadProgress(100);
      setFileInfo(result);
      setFileList(prev => {
        const exists = prev.some(item => item.file_path === result.file_path);
        if (exists) return prev;
        return [...prev, { ...result, size: file.size }];
      });
      onFileUploaded?.(result);

      setTimeout(() => {
        setUploading(false);
        setUploadProgress(0);
      }, 500);
    } catch (err: any) {
      clearInterval(progressTimer);
      setUploadProgress(0);
      setUploading(false);
      const errMsg = err?.message || err?.toString() || '上传失败，请重试';
      message.error(`上传失败: ${errMsg}`);
    }

    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSend = () => {
    if (disabled) return;
    const hasFileToSend = fileInfo || fileList.length > 0;
    if (!input.trim() && !hasFileToSend) return;

    if (chatMode === 'react_agent') {
      onSend(input.trim(), fileInfo, fileList);
    } else {
      onSend(input.trim(), fileInfo);
    }
    setInput('');
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const autoResize = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  };

  return (
    <div className="input-container">
      {fileList.length > 0 && (
        <>
          <div className="file-preview-area">
            {fileList.map((file, idx) => (
              <div className="file-chip" key={file.file_path || idx}>
                <FileExcelOutlined className="file-icon" />
                <div className="file-info">
                  <span className="file-name">{file.file_name}</span>
                  <span className="file-size">{formatFileSize(file.size || 0)}</span>
                </div>
                <button
                  className="file-remove"
                  disabled
                  style={{ opacity: 0.3, cursor: 'not-allowed' }}
                  title="已上传文件不能删除"
                >
                  <CloseOutlined />
                </button>
              </div>
            ))}
          </div>
          <div className="file-preview-divider" />
        </>
      )}

      <div className="input-row">
        <button
          className="upload-btn"
          onClick={() => fileInputRef.current?.click()}
          title="上传 Excel 文件"
          disabled={disabled || uploading || disableUpload}
          style={(disabled || disableUpload) ? { opacity: 0.35, cursor: 'not-allowed' } : undefined}
        >
          {uploading ? (
            <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28 }}>
              <ProgressRing percent={uploadProgress} size={28} strokeWidth={3} />
            </span>
          ) : (
            <PlusOutlined />
          )}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          style={{ display: 'none' }}
          onChange={handleUpload}
        />

        <textarea
          ref={textareaRef}
          className="input-textarea"
          value={input}
          onChange={autoResize}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? '正在处理数据，请稍候...' : '输入问题，分析你的数据...'}
          disabled={disabled}
          rows={1}
        />

        <button
          className="send-btn"
          onClick={handleSend}
          disabled={disabled || (!input.trim() && !fileInfo && fileList.length === 0)}
          title="发送"
        >
          <SendOutlined />
        </button>
      </div>
    </div>
  );
}
