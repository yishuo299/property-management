<template>
  <div>
    <PageHeader title="统计报表" desc="社区报修与物业费收缴情况多维统计分析" />

    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-icon orange"><el-icon><Tools /></el-icon></div>
        <div>
          <div class="stat-value">{{ ov.totalOrders ?? 0 }}</div>
          <div class="stat-label">累计报修工单</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon red"><el-icon><AlarmClock /></el-icon></div>
        <div>
          <div class="stat-value">{{ ov.timeoutOrders ?? 0 }}</div>
          <div class="stat-label">超时未受理</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green"><el-icon><TrendCharts /></el-icon></div>
        <div>
          <div class="stat-value">{{ ov.collectRate ?? 0 }}%</div>
          <div class="stat-label">物业费收缴率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon blue"><el-icon><Money /></el-icon></div>
        <div>
          <div class="stat-value">{{ (ov.received ?? 0).toFixed(0) }}</div>
          <div class="stat-label">已收物业费（元）</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon red"><el-icon><Wallet /></el-icon></div>
        <div>
          <div class="stat-value">{{ (ov.totalLateFee ?? 0).toFixed(2) }}</div>
          <div class="stat-label">应收滞纳金（元）</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green"><el-icon><Star /></el-icon></div>
        <div>
          <div class="stat-value">{{ ov.avgScore ?? '-' }}</div>
          <div class="stat-label">平均服务评分</div>
        </div>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="12">
        <div class="chart-card"><div class="chart-title">报修类型分布</div><ChartBox :option="typeOption" /></div>
      </el-col>
      <el-col :span="12">
        <div class="chart-card"><div class="chart-title">近 14 天报修趋势</div><ChartBox :option="trendOption" /></div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <div class="chart-card"><div class="chart-title">工单处理时效（按类型，小时）</div><ChartBox :option="effOption" /></div>
      </el-col>
      <el-col :span="12">
        <div class="chart-card"><div class="chart-title">工单完成时长分布</div><ChartBox :option="durOption" /></div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <div class="chart-card"><div class="chart-title">各账期物业费收缴率</div><ChartBox :option="rateOption" /></div>
      </el-col>
      <el-col :span="12">
        <div class="chart-card"><div class="chart-title">楼栋缴费对比</div><ChartBox :option="buildOption" /></div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <div class="chart-card"><div class="chart-title">维修工工作量与完成情况</div><ChartBox :option="staffOption" /></div>
      </el-col>
      <el-col :span="12">
        <div class="chart-card"><div class="chart-title">费用构成</div><ChartBox :option="feeCompOption" /></div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import ChartBox from '../../components/ChartBox.vue'
import {
  statsOverview, statsRepairType, statsRepairTrend, statsRepairEfficiency,
  statsFeeRate, statsBuildingFee, statsStaffWorkload, statsFeeComposition
} from '../../api'

const ov = ref({})
const typeOption = ref({})
const trendOption = ref({})
const effOption = ref({})
const durOption = ref({})
const rateOption = ref({})
const buildOption = ref({})
const staffOption = ref({})
const feeCompOption = ref({})

const palette = ['#ea580c', '#65a30d', '#f59e0b', '#0ea5e9', '#a855f7', '#e11d48']
const axisStyle = { axisLine: { lineStyle: { color: '#e7d9c8' } } }
const splitStyle = { splitLine: { lineStyle: { color: '#f5ece0' } } }

onMounted(async () => {
  ov.value = await statsOverview()

  const t = await statsRepairType()
  typeOption.value = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} 件 ({d}%)' },
    legend: { bottom: 0, icon: 'circle' },
    color: palette,
    series: [{
      type: 'pie', radius: ['40%', '66%'], center: ['50%', '45%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{c}件' }, data: t
    }]
  }

  const tr = await statsRepairTrend({ days: 14 })
  trendOption.value = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['新增报修', '完成工单'], bottom: 0, icon: 'roundRect' },
    grid: { left: 45, right: 20, top: 20, bottom: 45 },
    color: ['#ea580c', '#65a30d'],
    xAxis: { type: 'category', data: tr.dates, ...axisStyle },
    yAxis: { type: 'value', ...splitStyle },
    series: [
      { name: '新增报修', type: 'line', smooth: true, areaStyle: { opacity: 0.16 }, data: tr.newOrders, symbolSize: 6 },
      { name: '完成工单', type: 'line', smooth: true, areaStyle: { opacity: 0.16 }, data: tr.finishedOrders, symbolSize: 6 }
    ]
  }

  const eff = await statsRepairEfficiency()
  effOption.value = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['平均受理时长', '平均完成时长'], bottom: 0, icon: 'roundRect' },
    grid: { left: 50, right: 20, top: 20, bottom: 45 },
    color: ['#f59e0b', '#65a30d'],
    xAxis: { type: 'category', data: eff.types, ...axisStyle },
    yAxis: { type: 'value', name: '小时', ...splitStyle },
    series: [
      { name: '平均受理时长', type: 'bar', barWidth: 16, itemStyle: { borderRadius: [5, 5, 0, 0] }, data: eff.avgAcceptHours },
      { name: '平均完成时长', type: 'bar', barWidth: 16, itemStyle: { borderRadius: [5, 5, 0, 0] }, data: eff.avgFinishHours }
    ]
  }

  const buckets = eff.durationBuckets || []
  durOption.value = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} 件 ({d}%)' },
    legend: { bottom: 0, icon: 'circle' },
    color: ['#65a30d', '#f59e0b', '#e11d48'],
    series: [{
      type: 'pie', radius: '62%', center: ['50%', '45%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{c}件' }, data: buckets
    }]
  }

  const fr = await statsFeeRate()
  rateOption.value = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['应收金额', '实收金额', '收缴率'], bottom: 0, icon: 'roundRect' },
    grid: { left: 55, right: 50, top: 20, bottom: 45 },
    color: ['#fb923c', '#65a30d', '#0ea5e9'],
    xAxis: { type: 'category', data: fr.periods, ...axisStyle },
    yAxis: [
      { type: 'value', name: '元', ...splitStyle },
      { type: 'value', name: '收缴率%', max: 100, ...splitStyle }
    ],
    series: [
      { name: '应收金额', type: 'bar', barWidth: 18, itemStyle: { borderRadius: [5, 5, 0, 0] }, data: fr.receivable },
      { name: '实收金额', type: 'bar', barWidth: 18, itemStyle: { borderRadius: [5, 5, 0, 0] }, data: fr.received },
      { name: '收缴率', type: 'line', yAxisIndex: 1, smooth: true, symbolSize: 8, data: fr.rate }
    ]
  }

  const bf = await statsBuildingFee()
  buildOption.value = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['应收金额', '实收金额'], bottom: 0, icon: 'roundRect' },
    grid: { left: 55, right: 20, top: 20, bottom: 45 },
    color: ['#fb923c', '#65a30d'],
    xAxis: { type: 'category', data: bf.buildings, ...axisStyle },
    yAxis: { type: 'value', name: '元', ...splitStyle },
    series: [
      { name: '应收金额', type: 'bar', barWidth: 18, itemStyle: { borderRadius: [5, 5, 0, 0] }, data: bf.receivable },
      { name: '实收金额', type: 'bar', barWidth: 18, itemStyle: { borderRadius: [5, 5, 0, 0] }, data: bf.received }
    ]
  }

  const sw = await statsStaffWorkload()
  staffOption.value = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['承接工单', '已完成'], bottom: 0, icon: 'roundRect' },
    grid: { left: 45, right: 20, top: 20, bottom: 45 },
    color: ['#0ea5e9', '#65a30d'],
    xAxis: { type: 'category', data: sw.names, ...axisStyle },
    yAxis: { type: 'value', ...splitStyle },
    series: [
      { name: '承接工单', type: 'bar', barWidth: 22, itemStyle: { borderRadius: [5, 5, 0, 0] }, data: sw.totals },
      { name: '已完成', type: 'bar', barWidth: 22, itemStyle: { borderRadius: [5, 5, 0, 0] }, data: sw.finished }
    ]
  }

  const fc = await statsFeeComposition()
  feeCompOption.value = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} 元 ({d}%)' },
    legend: { bottom: 0, icon: 'circle' },
    color: ['#ea580c', '#65a30d'],
    series: [{
      type: 'pie', radius: ['42%', '68%'], center: ['50%', '45%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{c} 元' },
      data: fc.map((x) => ({ name: x.name, value: x.value }))
    }]
  }
})
</script>
