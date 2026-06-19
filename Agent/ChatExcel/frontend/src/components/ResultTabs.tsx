/** ResultTabs — 数据分析结果双标签：数据表 + SQL + 复制 */

import { useState } from 'react';
import { TableOutlined, CodeOutlined, CopyOutlined, CheckOutlined } from '@ant-design/icons';
import { message } from 'antd';
import TableRenderer from './TableRenderer';
import ChartRenderer from './ChartRenderer';

interface Props {
  sql: string;
  chartType: string;
  chartData: { columns: string[]; rows: any[][] } | null;
}

/**
 * SQL 标准格式化
 * 将 SQL 格式化为标准缩进格式：
 *   SELECT
 *        COUNT(*) AS 深圳客户数量
 *   FROM
 *        data_analysis_table
 *   WHERE
 *        等级 = '白金';
 */
function formatSql(sql: string): string {
  let s = sql.trim().replace(/;\s*$/, ''); // 去掉末尾分号

  // 定义子句关键字及其内容缩进级别
  // 关键字按长度降序排列，避免 LEFT JOIN 被 JOIN 先匹配
  const topClauses = [
    'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING',
    'ORDER BY', 'LIMIT', 'OFFSET',
    'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'FULL JOIN', 'CROSS JOIN', 'JOIN',
    'UNION ALL', 'UNION', 'INTERSECT', 'EXCEPT',
    'INSERT INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE FROM',
  ].sort((a, b) => b.length - a.length);

  // 第1步：在子句关键字前插入换行符
  for (const kw of topClauses) {
    const re = new RegExp(`\\b(${kw})\\b`, 'gi');
    s = s.replace(re, `\n${kw}`);
  }
  s = s.replace(/^\n+/, '');

  // 第2步：按行处理，在关键字行后面插入缩进的子句内容
  const lines = s.split('\n');
  const result: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // 判断这一行是否以子句关键字开头
    const isClauseLine = topClauses.some(kw => {
      const re = new RegExp(`^${kw}$`, 'i');
      return re.test(trimmed);
    });

    if (isClauseLine) {
      // 关键字单独一行
      result.push(trimmed.toUpperCase());
    } else {
      // 检查是否是"关键字 + 内容"在同一行（如 "SELECT COUNT(*)"）
      const clauseMatch = topClauses.find(kw => {
        const re = new RegExp(`^${kw}\\s+`, 'i');
        return re.test(trimmed);
      });

      if (clauseMatch) {
        // 将关键字和内容拆成两行
        const re = new RegExp(`^(${clauseMatch})(\\s+)(.*)`, 'i');
        const m = trimmed.match(re);
        if (m) {
          result.push(m[1].toUpperCase());
          // 内容缩进
          const content = m[3].trim();
          result.push(`     ${content}`);
        } else {
          result.push(`     ${trimmed}`);
        }
      } else {
        // AND/OR 单独处理
        const andOrMatch = trimmed.match(/^(AND|OR)\s+(.*)/i);
        if (andOrMatch) {
          result.push(`  ${andOrMatch[1].toUpperCase()}`);
          result.push(`     ${andOrMatch[2].trim()}`);
        } else {
          result.push(`     ${trimmed}`);
        }
      }
    }
  }

  // 第3步：处理逗号换行（SELECT 字段列表中的多字段情况）
  let formatted = result.join('\n');

  // 逗号后换行+缩进（仅针对缩进后的内容行）
  formatted = formatted.replace(/,\s*/g, ',\n     ');

  // 清理连续多余空行
  formatted = formatted.replace(/\n{2,}/g, '\n');

  // 清理行尾空格
  formatted = formatted.replace(/ +\n/g, '\n');

  return formatted;
}

export default function ResultTabs({ sql, chartType, chartData }: Props) {
  const [activeTab, setActiveTab] = useState<'table' | 'sql'>('table');
  const [copied, setCopied] = useState(false);

  const formattedSql = formatSql(sql);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formattedSql);
      setCopied(true);
      message.success('已复制到剪贴板');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // 降级方案
      const textarea = document.createElement('textarea');
      textarea.value = formattedSql;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      message.success('已复制到剪贴板');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="result-tabs">
      <div className="result-tabs-header">
        <div className="result-tabs-header-left">
          <button
            className={`result-tab ${activeTab === 'table' ? 'active' : ''}`}
            onClick={() => setActiveTab('table')}
          >
            <TableOutlined style={{ marginRight: 4 }} /> 数据表
          </button>
          <button
            className={`result-tab ${activeTab === 'sql' ? 'active' : ''}`}
            onClick={() => setActiveTab('sql')}
          >
            <CodeOutlined style={{ marginRight: 4 }} /> SQL
          </button>
        </div>
        {activeTab === 'sql' && (
          <button className="sql-copy-btn" onClick={handleCopy} title="复制 SQL">
            {copied ? <CheckOutlined style={{ color: '#52c41a' }} /> : <CopyOutlined />}
          </button>
        )}
      </div>

      <div className="result-tabs-body">
        {activeTab === 'table' && chartData && (
          chartType === 'response_table' ? (
            <TableRenderer columns={chartData.columns} rows={chartData.rows} />
          ) : (
            <ChartRenderer chartType={chartType} data={chartData} />
          )
        )}
        {activeTab === 'sql' && (
          <pre className="sql-block-formatted">{formattedSql}</pre>
        )}
      </div>
    </div>
  );
}
