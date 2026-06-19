/** ExcelPreview — 右侧收缩栏，预览 Excel 原始数据，像浏览 Excel 一样 */

import { useState, useEffect } from 'react';
import { FileExcelOutlined, LeftOutlined, RightOutlined, WarningOutlined } from '@ant-design/icons';
import { getExcelPreview } from '../api/client';

interface SheetData {
  name: string;
  total_rows: number;
  total_cols: number;
  too_large: boolean;
  message?: string;
  columns?: string[];
  rows?: any[][];
}

interface PreviewData {
  file_name: string;
  sheets: SheetData[];
}

interface PreviewSheet extends SheetData {
  file_name: string;
  display_name: string;
}

interface Props {
  filePaths: string[];
  collapsed: boolean;
  onToggle: () => void;
}

export default function ExcelPreview({ filePaths, collapsed, onToggle }: Props) {
  const [sheets, setSheets] = useState<PreviewSheet[]>([]);
  const [activeSheet, setActiveSheet] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const paths = filePaths.filter(Boolean);
    if (paths.length === 0 || collapsed) return;
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const results: PreviewData[] = await Promise.all(paths.map(path => getExcelPreview(path)));
        if (!cancelled) {
          const mergedSheets = results.flatMap(result =>
            result.sheets.map(sheet => ({
              ...sheet,
              file_name: result.file_name,
              display_name: results.length > 1 ? `${result.file_name} / ${sheet.name}` : sheet.name,
            }))
          );
          setSheets(mergedSheets);
          setActiveSheet(0);
        }
      } catch (err: any) {
        if (!cancelled) setError(err?.message || '加载预览失败');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [filePaths.join('|'), collapsed]);

  const currentSheet = sheets[activeSheet];

  return (
    <div className={`excel-preview ${collapsed ? 'collapsed' : ''}`}>
      {/* 收缩状态：显眼的提示条 */}
      {collapsed && (
        <div className="preview-collapsed-strip" onClick={onToggle}>
          <div className="collapsed-strip-icon">
            <FileExcelOutlined />
          </div>
          <span className="collapsed-strip-text">数据预览</span>
          <LeftOutlined className="collapsed-strip-arrow" />
        </div>
      )}

      {/* 展开状态 */}
      {!collapsed && (
        <div className="preview-content">
          {/* 顶部工具栏 */}
          <div className="preview-toolbar">
            <div className="preview-header">
              <FileExcelOutlined style={{ color: '#22c55e', marginRight: 6 }} />
              <span className="preview-filename">{currentSheet?.file_name || '加载中...'}</span>
            </div>
            <button className="preview-collapse-btn" onClick={onToggle} title="收起预览">
              <RightOutlined />
            </button>
          </div>

          {/* Sheet 标签栏 */}
          {sheets.length > 1 && (
            <div className="preview-sheet-tabs">
              {sheets.map((sheet, idx) => (
                <button
                  key={`${sheet.file_name}-${sheet.name}-${idx}`}
                  className={`preview-sheet-tab ${idx === activeSheet ? 'active' : ''}`}
                  onClick={() => setActiveSheet(idx)}
                >
                  {sheet.display_name}
                  <span className="sheet-row-count">{sheet.total_rows}行</span>
                </button>
              ))}
            </div>
          )}

          {/* 数据区域 */}
          <div className="preview-table-area">
            {loading && (
              <div className="preview-loading">
                <div className="preview-spinner" />
                <span>加载数据中...</span>
              </div>
            )}
            {error && (
              <div className="preview-error">
                <WarningOutlined style={{ color: '#f59e0b', marginRight: 6 }} />
                {error}
              </div>
            )}
            {currentSheet?.too_large && (
              <div className="preview-too-large">
                <WarningOutlined style={{ color: '#f59e0b', marginRight: 6 }} />
                {currentSheet.message}
              </div>
            )}
            {currentSheet && !currentSheet.too_large && currentSheet.columns && (
              <div className="preview-table-wrapper">
                <table className="preview-table">
                  <thead>
                    <tr>
                      <th className="preview-row-num">#</th>
                      {currentSheet.columns.map((col, i) => (
                        <th key={i}>{String(col)}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {currentSheet.rows?.map((row, ri) => (
                      <tr key={ri}>
                        <td className="preview-row-num">{ri + 1}</td>
                        {row.map((cell: any, ci: number) => (
                          <td key={ci}>{cell === null || cell === undefined ? '' : String(cell)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* 底部统计 */}
          {currentSheet && (
            <div className="preview-footer">
              {currentSheet.total_rows} 行 × {currentSheet.total_cols} 列
            </div>
          )}
        </div>
      )}
    </div>
  );
}
