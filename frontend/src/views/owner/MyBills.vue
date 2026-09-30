<template>
  <div>
    <PageHeader title="我的账单" desc="查看物业费 / 车位费账单明细，逾期账单将按日计收滞纳金" />

    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-icon orange"><el-icon><Tickets /></el-icon></div>
        <div>
          <div class="stat-value">{{ summary.count }}</div>
          <div class="stat-label">账单总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon red"><el-icon><Wallet /></el-icon></div>
        <div>
          <div class="stat-value">{{ summary.unpaid.toFixed(2) }}</div>
          <div class="stat-label">待缴金额（元）</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green"><el-icon><CircleCheck /></el-icon></div>
        <div>
          <div class="stat-value">{{ summary.paid.toFixed(2) }}</div>
          <div class="stat-label">已缴金额（元）</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon red"><el-icon><AlarmClock /></el-icon></div>
        <div>
          <div class="stat-value">{{ summary.late.toFixed(2) }}</div>
          <div class="stat-label">滞纳金（元）</div>
        </div>
      </div>
    </div>

    <div class="page-card">
      <div class="toolbar">
        <el-radio-group v-model="q.status" @change="load">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="未缴" />
          <el-radio-button label="部分缴纳" />
          <el-radio-button label="已缴" />
        </el-radio-group>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="billNo" label="账单号" width="160" />
        <el-table-column prop="roomName" label="房屋" min-width="160" />
        <el-table-column prop="feeType" label="费用类型" width="100" />
        <el-table-column prop="period" label="账期" width="95" />
        <el-table-column label="计费明细" min-width="170">
          <template #default="{ row }">{{ row.area }}㎡ × {{ row.unitPrice }} × {{ row.months }}月 = {{ row.amount }} 元</template>
        </el-table-column>
        <el-table-column prop="paidAmount" label="已缴" width="95" />
        <el-table-column label="滞纳金" width="100">
          <template #default="{ row }">
            <span v-if="row.lateFee > 0" style="color: #e11d48; font-weight: 600">{{ row.lateFee }}</span>
            <span v-else style="color: #a8a29e">0.00</span>
          </template>
        </el-table-column>
        <el-table-column label="本次应缴" width="110">
          <template #default="{ row }">
            <b v-if="row.remaining > 0" style="color: #ea580c">{{ row.remaining }}</b>
            <span v-else style="color: #a8a29e">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="dueDate" label="缴费截止日" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="{ 已缴: 'success', 部分缴纳: 'warning', 未缴: 'danger' }[row.status]" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager" background layout="total, prev, pager, next, sizes"
        :total="total" v-model:current-page="q.current" v-model:page-size="q.size"
        :page-sizes="[10, 20, 50]" @change="load" />
    </div>

    <el-dialog v-model="visible" title="账单详情" width="580px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="账单号">{{ detail.billNo }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="{ 已缴: 'success', 部分缴纳: 'warning', 未缴: 'danger' }[detail.status]" size="small" effect="light">{{ detail.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="房屋">{{ detail.roomName }}</el-descriptions-item>
        <el-descriptions-item label="费用类型">{{ detail.feeType }}</el-descriptions-item>
        <el-descriptions-item label="账期">{{ detail.period }}</el-descriptions-item>
        <el-descriptions-item label="缴费截止日">{{ detail.dueDate }}</el-descriptions-item>
        <el-descriptions-item label="建筑面积">{{ detail.area }} ㎡</el-descriptions-item>
        <el-descriptions-item label="单价 × 月数">{{ detail.unitPrice }} × {{ detail.months }}</el-descriptions-item>
        <el-descriptions-item label="应缴金额">{{ detail.amount }} 元</el-descriptions-item>
        <el-descriptions-item label="已缴金额">{{ detail.paidAmount }} 元</el-descriptions-item>
        <el-descriptions-item label="逾期天数">{{ detail.overdueDays }} 天</el-descriptions-item>
        <el-descriptions-item label="滞纳金">
          <span style="color: #e11d48">{{ detail.lateFee }} 元</span>
        </el-descriptions-item>
        <el-descriptions-item label="滞纳金公式" :span="2">
          <span style="font-size: 12.5px; color: #78716c">{{ detail.lateFeeFormula }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="应缴合计" :span="2">
          <b style="color: #ea580c; font-size: 16px">{{ detail.remaining }} 元</b>
        </el-descriptions-item>
      </el-descriptions>
      <el-divider content-position="left">缴费记录</el-divider>
      <el-table :data="detail.payments || []" size="small" border>
        <el-table-column prop="amount" label="金额(元)" width="100" />
        <el-table-column prop="payMethod" label="方式" width="90" />
        <el-table-column prop="tradeNo" label="流水号" min-width="150" />
        <el-table-column prop="payTime" label="缴费时间" width="160" />
      </el-table>
      <template #footer>
        <el-button @click="visible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import { billMine, billDetail } from '../../api'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = reactive({ current: 1, size: 10, status: '' })
const summary = reactive({ count: 0, unpaid: 0, paid: 0, late: 0 })

async function load() {
  loading.value = true
  try {
    const d = await billMine(q)
    rows.value = d.records
    total.value = d.total
  } finally {
    loading.value = false
  }
  const all = await billMine({ current: 1, size: 500 })
  summary.count = all.total
  summary.unpaid = all.records.reduce((a, b) => a + b.remaining, 0)
  summary.paid = all.records.reduce((a, b) => a + b.paidAmount, 0)
  summary.late = all.records.reduce((a, b) => a + b.lateFee, 0)
}

const visible = ref(false)
const detail = reactive({})

async function openDetail(row) {
  const d = await billDetail(row.id)
  Object.assign(detail, d)
  visible.value = true
}

onMounted(load)
</script>

<style scoped>
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
