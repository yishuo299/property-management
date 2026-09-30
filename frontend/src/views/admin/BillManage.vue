<template>
  <div>
    <PageHeader title="物业费管理" desc="按「建筑面积 × 单价 × 月数」计费，支持按楼栋批量生成账单与滞纳金自动计算" />

    <el-tabs v-model="tab" class="page-card">
      <!-- ===== 账单列表 ===== -->
      <el-tab-pane label="账单管理" name="list">
        <div class="toolbar">
          <el-select v-model="q.buildingId" placeholder="楼栋" clearable style="width: 130px">
            <el-option v-for="b in buildings" :key="b.id" :label="b.buildingName" :value="b.id" />
          </el-select>
          <el-select v-model="q.period" placeholder="账期" clearable style="width: 130px">
            <el-option v-for="p in periods" :key="p" :label="p" :value="p" />
          </el-select>
          <el-select v-model="q.status" placeholder="缴费状态" clearable style="width: 130px">
            <el-option v-for="s in ['未缴', '部分缴纳', '已缴']" :key="s" :label="s" :value="s" />
          </el-select>
          <el-select v-model="q.feeType" placeholder="费用类型" clearable style="width: 130px">
            <el-option label="物业费" value="物业费" />
            <el-option label="车位费" value="车位费" />
          </el-select>
          <el-input v-model="q.keyword" placeholder="账单号 / 房号" clearable style="width: 160px" @keyup.enter="load" />
          <el-button type="primary" @click="load"><el-icon><Search /></el-icon>查询</el-button>
          <el-button @click="reset">重置</el-button>
          <div class="spacer"></div>
          <el-button type="warning" @click="openGenerate"><el-icon><MagicStick /></el-icon>批量生成账单</el-button>
          <el-button type="success" plain @click="doExport"><el-icon><Download /></el-icon>导出 Excel</el-button>
        </div>

        <el-table :data="rows" v-loading="loading" border stripe>
          <el-table-column prop="billNo" label="账单号" width="160" />
          <el-table-column prop="roomName" label="房屋" min-width="150" />
          <el-table-column prop="ownerName" label="业主" width="95" />
          <el-table-column prop="feeType" label="类型" width="85" />
          <el-table-column prop="period" label="账期" width="95" />
          <el-table-column label="计算方式" min-width="160">
            <template #default="{ row }">
              <span style="font-size: 12.5px; color: #78716c">
                {{ row.area }}㎡ × {{ row.unitPrice }} × {{ row.months }}月
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="应缴" width="95" />
          <el-table-column prop="paidAmount" label="已缴" width="95" />
          <el-table-column label="滞纳金" width="100">
            <template #default="{ row }">
              <span v-if="row.lateFee > 0" style="color: #e11d48; font-weight: 600">{{ row.lateFee }}</span>
              <span v-else style="color: #a8a29e">0.00</span>
            </template>
          </el-table-column>
          <el-table-column label="逾期天数" width="95">
            <template #default="{ row }">
              <span v-if="row.overdueDays > 0" style="color: #e11d48">{{ row.overdueDays }} 天</span>
              <span v-else style="color: #a8a29e">-</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="{ 已缴: 'success', 部分缴纳: 'warning', 未缴: 'danger' }[row.status]" size="small" effect="light">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="190" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDetail(row)">详情</el-button>
              <el-button v-if="row.status !== '已缴'" link type="success" @click="openPay(row)">收费</el-button>
              <el-button v-if="row.status !== '已缴'" link type="danger" @click="remove(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          class="pager" background layout="total, prev, pager, next, sizes"
          :total="total" v-model:current-page="q.current" v-model:page-size="q.size"
          :page-sizes="[10, 20, 50]" @change="load" />
      </el-tab-pane>

      <!-- ===== 欠费统计 ===== -->
      <el-tab-pane label="欠费统计" name="arrears">
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-icon red"><el-icon><Wallet /></el-icon></div>
            <div>
              <div class="stat-value">{{ arrears.totalUnpaid ?? 0 }}</div>
              <div class="stat-label">欠费总额（元，含滞纳金）</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon orange"><el-icon><Wallet /></el-icon></div>
            <div>
              <div class="stat-value">{{ arrears.totalLateFee ?? 0 }}</div>
              <div class="stat-label">应收滞纳金（元）</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon blue"><el-icon><Tickets /></el-icon></div>
            <div>
              <div class="stat-value">{{ arrears.totalBills ?? 0 }}</div>
              <div class="stat-label">欠费账单（笔）</div>
            </div>
          </div>
        </div>
        <el-alert type="info" :closable="false" show-icon style="margin-bottom: 14px"
          :title="`滞纳金计算规则：滞纳金 = 逾期天数 × 日滞纳金率（${arrears.lateFeeRate}） × 欠费金额`" />
        <el-table :data="arrears.list || []" border stripe>
          <el-table-column prop="buildingName" label="楼栋" width="130" />
          <el-table-column prop="billCount" label="欠费账单数" width="130" />
          <el-table-column prop="overdueCount" label="其中已逾期" width="130" />
          <el-table-column prop="unpaidAmount" label="欠费金额（元）" width="150" />
          <el-table-column prop="lateFee" label="滞纳金（元）" width="150" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- ===== 批量生成面板 ===== -->
    <el-dialog v-model="genVisible" title="批量生成物业费账单" width="880px" top="6vh">
      <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 14px"
        title="生成规则：应缴金额 = 房屋建筑面积 × 单价 × 月数；对已存在同账期账单的房屋会自动跳过，不会重复生成。" />
      <el-form :model="genForm" label-width="100px" inline>
        <el-form-item label="选择楼栋" required>
          <el-select v-model="genForm.buildingId" placeholder="请选择楼栋" style="width: 160px" @change="doPreview">
            <el-option v-for="b in buildings" :key="b.id" :label="b.buildingName" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="账期" required>
          <el-date-picker v-model="genForm.period" type="month" value-format="YYYY-MM"
            placeholder="选择月份" style="width: 150px" @change="doPreview" />
        </el-form-item>
        <el-form-item label="单价(元/㎡/月)">
          <el-input-number v-model="genForm.unitPrice" :min="0.1" :max="50" :precision="2" :step="0.1" @change="doPreview" />
        </el-form-item>
        <el-form-item label="计费月数">
          <el-input-number v-model="genForm.months" :min="1" :max="24" @change="doPreview" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" plain @click="doPreview"><el-icon><View /></el-icon>预览</el-button>
        </el-form-item>
      </el-form>

      <template v-if="preview">
        <el-divider content-position="left">生成预览</el-divider>
        <div class="preview-summary">
          <el-tag type="info" effect="plain">楼栋：{{ preview.buildingName }}</el-tag>
          <el-tag type="info" effect="plain">账期：{{ preview.period }}</el-tag>
          <el-tag type="info" effect="plain">缴费截止日：{{ preview.dueDate }}</el-tag>
          <el-tag type="success" effect="light">房屋总数：{{ preview.totalRooms }}</el-tag>
          <el-tag type="warning" effect="light">将新生成：{{ preview.newCount }}</el-tag>
          <el-tag type="info" effect="light">已存在跳过：{{ preview.existCount }}</el-tag>
          <el-tag type="danger" effect="light">预计新增金额：{{ preview.newAmount }} 元</el-tag>
        </div>
        <el-table :data="preview.rows" size="small" border max-height="300" style="margin-top: 12px">
          <el-table-column prop="roomName" label="房屋" min-width="160" />
          <el-table-column prop="ownerName" label="业主" width="100" />
          <el-table-column prop="area" label="面积(㎡)" width="100" />
          <el-table-column prop="amount" label="应缴金额" width="110" />
          <el-table-column label="是否已生成" width="120">
            <template #default="{ row }">
              <el-tag :type="row.exists ? 'info' : 'success'" size="small" effect="light">
                {{ row.exists ? '已存在(跳过)' : '待生成' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </template>

      <template #footer>
        <el-button @click="genVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!preview || preview.newCount === 0" @click="doGenerate">
          确认生成{{ preview ? `（${preview.newCount} 条）` : '' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ===== 缴费 ===== -->
    <el-dialog v-model="payVisible" title="物业费收费" width="540px">
      <el-descriptions :column="2" border size="small" style="margin-bottom: 14px">
        <el-descriptions-item label="账单号">{{ payBill.billNo }}</el-descriptions-item>
        <el-descriptions-item label="房屋">{{ payBill.roomName }}</el-descriptions-item>
        <el-descriptions-item label="业主">{{ payBill.ownerName }}</el-descriptions-item>
        <el-descriptions-item label="账期">{{ payBill.period }}</el-descriptions-item>
        <el-descriptions-item label="应缴金额">{{ payBill.amount }} 元</el-descriptions-item>
        <el-descriptions-item label="已缴金额">{{ payBill.paidAmount }} 元</el-descriptions-item>
        <el-descriptions-item label="逾期天数">{{ payBill.overdueDays }} 天</el-descriptions-item>
        <el-descriptions-item label="滞纳金">
          <span style="color: #e11d48">{{ payBill.lateFee }} 元</span>
        </el-descriptions-item>
        <el-descriptions-item label="本次应缴" :span="2">
          <b style="color: #ea580c; font-size: 16px">{{ payBill.remaining }} 元</b>
          <span style="color: #78716c; font-size: 12.5px; margin-left: 8px">（应缴 + 滞纳金 - 已缴）</span>
        </el-descriptions-item>
      </el-descriptions>
      <el-form :model="payForm" :rules="payRules" ref="payFormRef" label-width="100px">
        <el-form-item label="缴费金额" prop="amount">
          <el-input-number v-model="payForm.amount" :min="0.01" :max="payBill.remaining || 999999" :precision="2" style="width: 200px" />
          <el-button link type="primary" style="margin-left: 10px" @click="payForm.amount = payBill.remaining">全额缴清</el-button>
        </el-form-item>
        <el-form-item label="缴费方式" prop="payMethod">
          <el-radio-group v-model="payForm.payMethod">
            <el-radio-button v-for="m in ['微信', '支付宝', '银行卡', '现金']" :key="m" :label="m" />
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="payForm.remark" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPay">确认收费</el-button>
      </template>
    </el-dialog>

    <!-- ===== 账单详情 ===== -->
    <el-dialog v-model="detailVisible" title="账单详情" width="620px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="账单号">{{ detail.billNo }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="{ 已缴: 'success', 部分缴纳: 'warning', 未缴: 'danger' }[detail.status]" size="small" effect="light">{{ detail.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="房屋">{{ detail.roomName }}</el-descriptions-item>
        <el-descriptions-item label="业主">{{ detail.ownerName }}</el-descriptions-item>
        <el-descriptions-item label="费用类型">{{ detail.feeType }}</el-descriptions-item>
        <el-descriptions-item label="账期">{{ detail.period }}</el-descriptions-item>
        <el-descriptions-item label="建筑面积">{{ detail.area }} ㎡</el-descriptions-item>
        <el-descriptions-item label="单价 × 月数">{{ detail.unitPrice }} × {{ detail.months }}</el-descriptions-item>
        <el-descriptions-item label="应缴金额">{{ detail.amount }} 元</el-descriptions-item>
        <el-descriptions-item label="已缴金额">{{ detail.paidAmount }} 元</el-descriptions-item>
        <el-descriptions-item label="缴费截止日">{{ detail.dueDate }}</el-descriptions-item>
        <el-descriptions-item label="逾期天数">{{ detail.overdueDays }} 天</el-descriptions-item>
        <el-descriptions-item label="滞纳金" :span="2">
          <span style="color: #e11d48">{{ detail.lateFee }} 元</span>
          <div style="font-size: 12.5px; color: #78716c; margin-top: 4px">{{ detail.lateFeeFormula }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="当前应缴合计" :span="2">
          <b style="color: #ea580c">{{ detail.remaining }} 元</b>
        </el-descriptions-item>
      </el-descriptions>
      <el-divider content-position="left">缴费记录</el-divider>
      <el-table :data="detail.payments || []" size="small" border>
        <el-table-column prop="amount" label="金额(元)" width="100" />
        <el-table-column prop="payMethod" label="方式" width="90" />
        <el-table-column prop="tradeNo" label="流水号" min-width="160" />
        <el-table-column prop="payTime" label="缴费时间" width="160" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import {
  buildingList, billPage, billPreview, billGenerate, billArrears, billDetail,
  billPay, delBill, downloadExport
} from '../../api'

const tab = ref('list')
const buildings = ref([])
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = reactive({ current: 1, size: 10, buildingId: null, period: '', status: '', feeType: '', keyword: '' })
const periods = ['2026-07', '2026-08', '2026-09', '2026-10', '2026-11', '2026-12']
const arrears = ref({})

async function load() {
  loading.value = true
  try {
    const d = await billPage(q)
    rows.value = d.records
    total.value = d.total
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(q, { current: 1, buildingId: null, period: '', status: '', feeType: '', keyword: '' })
  load()
}

async function loadArrears() {
  arrears.value = await billArrears()
}

// ---- 批量生成 ----
const genVisible = ref(false)
const preview = ref(null)
const genForm = reactive({ buildingId: null, period: '', unitPrice: 2.5, months: 1 })

function openGenerate() {
  genVisible.value = true
  preview.value = null
}

async function doPreview() {
  if (!genForm.buildingId || !genForm.period) {
    return
  }
  preview.value = await billPreview({ ...genForm })
}

async function doGenerate() {
  const res = await billGenerate({ ...genForm })
  ElMessage.success(`生成完成：新增 ${res.created} 条，跳过已存在 ${res.skipped} 条`)
  genVisible.value = false
  preview.value = null
  load()
  loadArrears()
}

// ---- 缴费 ----
const payVisible = ref(false)
const payBill = reactive({})
const payFormRef = ref()
const payForm = reactive({ amount: 0, payMethod: '微信', remark: '' })
const payRules = {
  amount: [{ required: true, message: '请输入缴费金额', trigger: 'blur' }],
  payMethod: [{ required: true, message: '请选择缴费方式', trigger: 'change' }]
}

function openPay(row) {
  Object.assign(payBill, row)
  payForm.amount = row.remaining
  payForm.payMethod = '微信'
  payForm.remark = ''
  payVisible.value = true
}

async function submitPay() {
  try {
    await payFormRef.value.validate()
  } catch (e) {
    return
  }
  if (!payForm.amount || payForm.amount <= 0) {
    ElMessage.warning('缴费金额必须大于 0')
    return
  }
  await billPay(payBill.id, payForm)
  ElMessage.success('收费成功')
  payVisible.value = false
  load()
  loadArrears()
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确定删除账单「${row.billNo}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await delBill(row.id)
  ElMessage.success('删除成功')
  load()
}

// ---- 详情 ----
const detailVisible = ref(false)
const detail = reactive({})

async function openDetail(row) {
  const d = await billDetail(row.id)
  Object.assign(detail, d)
  detailVisible.value = true
}

function doExport() {
  const params = []
  if (q.period) params.push(`period=${q.period}`)
  if (q.status) params.push(`status=${encodeURIComponent(q.status)}`)
  if (q.buildingId) params.push(`buildingId=${q.buildingId}`)
  downloadExport('/export/bills' + (params.length ? '?' + params.join('&') : ''), '物业费账单明细.xlsx')
  ElMessage.success('正在导出账单明细...')
}

onMounted(async () => {
  buildings.value = await buildingList()
  load()
  loadArrears()
})
</script>

<style scoped>
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}

.preview-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 6px;
}
</style>
