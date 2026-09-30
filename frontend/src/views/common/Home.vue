<template>
  <div>
    <div class="welcome-banner">
      <div class="wb-left">
        <div class="wb-title">{{ greeting }}，{{ userStore.realName }}</div>
        <div class="wb-sub">{{ roleTip }}</div>
      </div>
      <div class="wb-right">
        <el-icon :size="58" color="rgba(255,255,255,0.55)"><House /></el-icon>
      </div>
    </div>

    <!-- 业主首页 -->
    <template v-if="isOwner">
      <div class="stat-grid">
        <div class="stat-card" v-for="s in ownerStats" :key="s.label">
          <div class="stat-icon" :class="s.color"><el-icon><component :is="s.icon" /></el-icon></div>
          <div>
            <div class="stat-value">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>
      </div>
      <div class="quick-grid">
        <div class="quick-card" v-for="q in ownerQuick" :key="q.path" @click="$router.push(q.path)">
          <div class="qc-icon"><el-icon :size="26"><component :is="q.icon" /></el-icon></div>
          <div class="qc-title">{{ q.title }}</div>
          <div class="qc-desc">{{ q.desc }}</div>
        </div>
      </div>
      <div class="page-card" style="margin-top: 16px">
        <div class="chart-title">最新公告</div>
        <div v-if="!notices.length" class="empty-tip">暂无公告</div>
        <div v-for="n in notices" :key="n.id" class="notice-item" :class="{ unread: !n.read }" @click="$router.push('/my-notice')">
          <div class="notice-title">
            <span v-if="!n.read" class="dot-unread"></span>
            <el-tag v-if="n.isTop" type="danger" size="small" effect="dark" round>置顶</el-tag>
            {{ n.title }}
          </div>
          <div class="notice-body">{{ n.content.slice(0, 90) }}{{ n.content.length > 90 ? '...' : '' }}</div>
          <div class="repair-card-meta"><span>发布时间：{{ n.publishTime }}</span></div>
        </div>
      </div>
    </template>

    <!-- 管理员 / 员工首页 -->
    <template v-else>
      <div class="stat-grid">
        <div class="stat-card" v-for="s in adminStats" :key="s.label">
          <div class="stat-icon" :class="s.color"><el-icon><component :is="s.icon" /></el-icon></div>
          <div>
            <div class="stat-value">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>
      </div>

      <el-row :gutter="16">
        <el-col :span="12">
          <div class="chart-card">
            <div class="chart-title">报修类型分布</div>
            <ChartBox :option="typeOption" />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="chart-card">
            <div class="chart-title">近 14 天报修趋势</div>
            <ChartBox :option="trendOption" />
          </div>
        </el-col>
      </el-row>

      <div class="page-card" style="margin-top: 16px">
        <div class="chart-title">待受理工单（含超时提醒）</div>
        <el-table :data="pendingOrders" size="small" v-loading="loading">
          <el-table-column prop="orderNo" label="工单号" width="160" />
          <el-table-column prop="roomName" label="房屋" min-width="150" />
          <el-table-column prop="title" label="报修内容" min-width="180" />
          <el-table-column prop="repairType" label="类型" width="90" />
          <el-table-column prop="urgency" label="紧急程度" width="100">
            <template #default="{ row }">
              <el-tag :type="urgencyType(row.urgency)" size="small" effect="light">{{ row.urgency }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="submitTime" label="提交时间" width="165" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.timeout" type="danger" size="small" effect="dark">已超时</el-tag>
              <el-tag v-else type="warning" size="small" effect="light">待受理</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../../store/user'
import ChartBox from '../../components/ChartBox.vue'
import { statsOverview, statsMyOverview, statsRepairType, statsRepairTrend, repairPage, noticeList } from '../../api'

const userStore = useUserStore()
const isOwner = computed(() => userStore.isOwner)
const ov = ref({})
const notices = ref([])
const pendingOrders = ref([])
const loading = ref(false)

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const roleTip = computed(() => ({
  ADMIN: '幸福家园小区 · 物业管理后台，祝您工作顺利',
  STAFF: '幸福家园小区 · 维修工作台，今日也要加油哦',
  OWNER: '幸福家园小区 · 业主服务台，有事随时找物业'
}[userStore.role] || ''))

const ownerStats = computed(() => [
  { label: '我的房屋（套）', value: ov.value.myRooms ?? 0, icon: 'House', color: 'orange' },
  { label: '进行中的报修', value: ov.value.myPending ?? 0, icon: 'Tools', color: 'blue' },
  { label: '待缴账单（笔）', value: ov.value.myUnpaidBills ?? 0, icon: 'Money', color: 'red' },
  { label: '待缴金额（元）', value: (ov.value.myUnpaidAmount ?? 0).toFixed(2), icon: 'Wallet', color: 'green' },
  { label: '我的车位（个）', value: ov.value.myParking ?? 0, icon: 'Van', color: 'blue' },
  { label: '未读公告', value: ov.value.unreadNotice ?? 0, icon: 'Bell', color: 'orange' }
])

const ownerQuick = [
  { path: '/new-repair', title: '我要报修', desc: '水电门窗家电问题一键上报', icon: 'EditPen' },
  { path: '/my-repairs', title: '报修进度', desc: '查看师傅上门与处理进度', icon: 'Tools' },
  { path: '/my-bills', title: '物业费缴纳', desc: '查看账单并在线缴费', icon: 'Money' },
  { path: '/my-visitor', title: '访客预约', desc: '预约访客获取访客码', icon: 'Postcard' }
]

const adminStats = computed(() => [
  { label: '楼栋 / 房屋', value: `${ov.value.buildingCount ?? 0} / ${ov.value.roomCount ?? 0}`, icon: 'OfficeBuilding', color: 'orange' },
  { label: '登记业主（人）', value: ov.value.ownerCount ?? 0, icon: 'User', color: 'blue' },
  { label: '待受理工单', value: ov.value.pendingOrders ?? 0, icon: 'Tools', color: 'red' },
  { label: '超时未受理', value: ov.value.timeoutOrders ?? 0, icon: 'AlarmClock', color: 'red' },
  { label: '物业费收缴率', value: (ov.value.collectRate ?? 0) + '%', icon: 'TrendCharts', color: 'green' },
  { label: '空闲车位', value: ov.value.parkingFree ?? 0, icon: 'Van', color: 'green' }
])

const typeOption = ref({})
const trendOption = ref({})

function urgencyType(u) {
  return { 一般: 'info', 紧急: 'warning', 非常紧急: 'danger' }[u] || 'info'
}

onMounted(async () => {
  loading.value = true
  try {
    // 业主走本人数据总览接口，管理员/员工走小区全局总览接口（服务端分别做角色校验）
    ov.value = isOwner.value ? await statsMyOverview() : await statsOverview()
    if (isOwner.value) {
      const res = await noticeList()
      notices.value = (res || []).slice(0, 4)
    } else {
      const t = await statsRepairType()
      typeOption.value = {
        tooltip: { trigger: 'item', formatter: '{b}: {c} 件 ({d}%)' },
        legend: { bottom: 0, icon: 'circle' },
        color: ['#ea580c', '#65a30d', '#f59e0b', '#0ea5e9', '#a855f7'],
        series: [{
          type: 'pie',
          radius: ['42%', '68%'],
          center: ['50%', '45%'],
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
          label: { formatter: '{b}\n{c}件' },
          data: t
        }]
      }
      const tr = await statsRepairTrend({ days: 14 })
      trendOption.value = {
        tooltip: { trigger: 'axis' },
        legend: { data: ['新增报修', '完成工单'], bottom: 0, icon: 'roundRect' },
        grid: { left: 45, right: 20, top: 20, bottom: 45 },
        color: ['#ea580c', '#65a30d'],
        xAxis: { type: 'category', data: tr.dates, axisLine: { lineStyle: { color: '#e7d9c8' } } },
        yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f5ece0' } } },
        series: [
          { name: '新增报修', type: 'line', smooth: true, areaStyle: { opacity: 0.16 }, data: tr.newOrders, symbolSize: 6 },
          { name: '完成工单', type: 'line', smooth: true, areaStyle: { opacity: 0.16 }, data: tr.finishedOrders, symbolSize: 6 }
        ]
      }
      const p = await repairPage({ status: '待受理', current: 1, size: 8 })
      pendingOrders.value = p.records
    }
  } catch (e) {
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.welcome-banner {
  background: linear-gradient(120deg, #ea580c 0%, #f97316 55%, #84cc16 130%);
  border-radius: 16px;
  padding: 22px 26px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  box-shadow: 0 8px 22px rgba(234, 88, 12, 0.2);
}

.wb-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 1px;
}

.wb-sub {
  font-size: 13.5px;
  opacity: 0.92;
  margin-top: 6px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 14px;
}

.quick-card {
  background: #fff;
  border: 1px solid var(--pm-border);
  border-radius: var(--pm-radius);
  padding: 18px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: var(--pm-shadow);
}

.quick-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--pm-shadow-hover);
}

.qc-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: linear-gradient(135deg, #ffedd5, #ecfccb);
  color: #ea580c;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.qc-title {
  font-size: 15.5px;
  font-weight: 600;
}

.qc-desc {
  font-size: 12.5px;
  color: var(--pm-text-sub);
  margin-top: 4px;
}
</style>
