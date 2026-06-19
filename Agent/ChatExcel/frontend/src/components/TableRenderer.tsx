/** TableRenderer — SQL 查询结果表格 */

import { Table } from 'antd';

interface Props {
  columns: string[];
  rows: any[][];
}

export default function TableRenderer({ columns, rows }: Props) {
  if (!columns || !rows || !Array.isArray(columns) || !Array.isArray(rows)) {
    return <div style={{ color: '#999', fontSize: 13 }}>数据格式异常</div>;
  }
  const antColumns = columns.map((col) => ({
    title: col,
    dataIndex: col,
    key: col,
    ellipsis: true,
  }));

  const dataSource = rows.map((row, idx) => ({
    key: idx,
    ...Object.fromEntries(row.map((val, colIdx) => [columns[colIdx], val ?? ''])),
  }));

  return (
    <Table
      columns={antColumns}
      dataSource={dataSource}
      size="small"
      scroll={{ x: 'max-content' }}
      pagination={{ pageSize: 5, size: 'small' }}
      bordered
    />
  );
}
