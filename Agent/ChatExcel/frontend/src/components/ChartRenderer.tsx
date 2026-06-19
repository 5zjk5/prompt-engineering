/** ChartRenderer — ECharts 图表渲染 */

import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';

interface Props {
  chartType: string;
  data: { columns: string[]; rows: any[][] };
}

function buildOption(chartType: string, data: { columns: string[]; rows: any[][] }): EChartsOption {
  const { columns, rows } = data;
  if (!columns || !rows || !Array.isArray(rows) || rows.length === 0) return {};

  const xData = rows.map(r => r[0]);
  const yCols = columns.slice(1);

  if (chartType.includes('pie')) {
    return {
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        type: 'pie',
        radius: '55%',
        data: rows.map(r => ({ name: r[0], value: r[1] })),
      }],
    };
  }

  const seriesType = chartType.includes('line') ? 'line'
    : chartType.includes('scatter') ? 'scatter'
    : 'bar';

  return {
    tooltip: { trigger: 'axis' },
    legend: {},
    grid: { left: 40, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: xData },
    yAxis: { type: 'value' },
    series: yCols.map((col, idx) => ({
      name: col,
      type: seriesType,
      data: rows.map(r => r[idx + 1]),
    })),
  };
}

export default function ChartRenderer({ chartType, data }: Props) {
  const option = buildOption(chartType, data);
  return (
    <ReactECharts
      option={option}
      style={{ height: 300, width: '100%' }}
    />
  );
}
