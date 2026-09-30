<template>
  <div>
    <PageHeader title="报修工单管理" desc="工单状态流转：待受理 → 已派单 → 处理中 → 已完成 → 已评价（旁路：已驳回 / 已取消）" />

    <div class="stat-grid">
      <div class="stat-card" v-for="s in cards" :key="s.label">
        <div class="stat-icon" :class="s.color"><el-icon><component :is="s.icon" /></el-icon></div>
        <div>
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <div class="page-card">
      <div class="toolbar">
        <el-input v-model="q.keyword" placeholder="工单号 / 标题 / 描述" clearable style="width: 220px" @keyup.enter="load" />
        <el-select v-model="q.status" placeholder="工单状态" clearable style="width: 130px">
          <el-option v-for="s in statusList" :key="s" :label="s" :value="s" />
        </el-select>
        <el-select v-model="q.repairType" placeholder="报修类型" clearable style="width: 130px">
          <el-option v-for="t in types" :key="t" :label="t" :value="t" />
        </el-select>
        <el-select v-model="q.urgency" placeholder="紧急程度" clearable style="width: 130px">
          <el-option v-for="u in ['一般', '紧急', '非常紧急']" :key="u" :label="u" :value="u" />
        </el-select>
        <el-checkbox v-model="q.timeoutOnly" label="只看超时" border style="margin-left: 0" />
        <el-button type="primary" @click="load"><el-icon><Search /></el-icon>查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="success" plain @click="doExport"><el-icon><Download /></el-icon>导出 Excel</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="orderNo" label="工单号" width="150" />
        <el-table-column prop="roomName" label="房屋" min-width="150" />
        <el-table-column prop="ownerName" label="业主" width="90" />
        <el-table-column prop="title" label="报修内容" min-width="180" show-overflow-tooltip />
        <el-table-column prop="repairType" label="类型" width="95" />
        <el-table-column label="紧急程度" width="100">
          <template #default="{ row }">
            <el-tag :type="urgencyType(row.urgency)" size="small" effect="light">{{ row.urgency }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="105">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="超时" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.timeout" type="danger" size="small" effect="dark">超时</el-tag>
            <span v-else style="color: #a8a29e">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="handlerName" label="处理人" width="95">
          <template #default="{ row }">{{ row.handlerName || '-' }}</template>
        </el-table-column>
        <el-table-column prop="submitTime" label="提交时间" width="160" />
        <el-table-column label="评分" width="80">
          <template #default="{ row }">
            <span v-if="row.score">{{ row.score }} 星</span>
            <span v-else style="color: #a8a29e">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情 / 处理</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager" background layout="total, prev, pager, next, sizes"
        :total="total" v-model:current-page="q.current" v-model:page-size="q.size"
        :page-sizes="[10, 20, 50]" @change="load" />
    </div>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawer" title="工单详情" size="620px">
      <template v-if="cur.id">
        <el-steps :active="stepIndex" align-center finish-status="success" style="margin-bottom: 18px">
          <el-step title="待受理" :description="shortTime(cur.submitTime)" />
          <el-step title="已派单" :description="shortTime(cur.assignTime)" />
          <el-step title="处理中" :description="cur.handlerName || ''" />
          <el-step title="已完成" :description="shortTime(cur.finishTime)" />
          <el-step title="已评价" :description="cur.score ? cur.score + ' 星' : ''" />
        </el-steps>

        <el-alert v-if="cur.timeout" type="error" :closable="false" show-icon
          title="该工单已超过 24 小时未受理，系统已标记为超时" style="margin-bottom: 12px" />

        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="工单号">{{ cur.orderNo }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(cur.status)" size="small" effect="light">{{ cur.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="房屋">{{ cur.roomName }}</el-descriptions-item>
          <el-descriptions-item label="建筑面积">{{ cur.area }} ㎡</el-descriptions-item>
          <el-descriptions-item label="报修业主">{{ cur.ownerName }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ cur.ownerPhone }}</el-descriptions-item>
          <el-descriptions-item label="报修类型">{{ cur.repairType }}</el-descriptions-item>
          <el-descriptions-item label="紧急程度">{{ cur.urgency }}</el-descriptions-item>
          <el-descriptions-item label="处理人">{{ cur.handlerName || '未指派' }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ cur.submitTime }}</el-descriptions-item>
          <el-descriptions-item label="报修内容" :span="2">{{ cur.content }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="cur.images && cur.images.length" style="margin-top: 12px">
          <div class="chart-title">现场照片</div>
          <el-image
            v-for="img in cur.images" :key="img" :src="img" :preview-src-list="cur.images"
            fit="cover" style="width: 110px; height: 84px; margin-right: 8px; border-radius: 8px" />
        </div>

        <div v-if="cur.remark" style="margin-top: 12px">
          <el-alert type="info" :closable="false" :title="'备注：' + cur.remark" />
        </div>

        <div class="chart-title" style="margin-top: 18px">处理记录</div>
        <el-timeline>
          <el-timeline-item
            v-for="r in cur.records" :key="r.id"
            :timestamp="r.createTime" :type="recordType(r.action)" placement="top">
            <div class="rec-head">
              <el-tag size="small" effect="light">{{ r.action }}</el-tag>
              <span class="rec-op">{{ r.operatorName }}</span>
            </div>
            <div class="rec-body">{{ r.content }}</div>
          </el-timeline-item>
        </el-timeline>

        <div v-if="cur.evaluation" style="margin-top: 10px">
          <el-divider content-position="left">业主评价</el-divider>
          <el-rate :model-value="cur.evaluation.score" disabled show-score />
          <div class="rec-body">{{ cur.evaluation.content }}</div>
          <div class="rec-op">服务态度 {{ cur.evaluation.attitudeScore }} 星 · 处理速度 {{ cur.evaluation.speedScore }} 星</div>
        </div>

        <el-divider content-position="left">可执行操作</el-divider>
        <div class="action-bar">
          <el-button v-if="cur.status === '待受理'" type="primary" @click="openAction('assign')">
            <el-icon><Promotion /></el-icon>派单
          </el-button>
          <el-button v-if="cur.status === '待受理'" type="danger" plain @click="openAction('reject')">驳回</el-button>
          <el-button v-if="['待受理', '已派单'].includes(cur.status)" plain @click="openAction('cancel')">取消工单</el-button>
          <el-button v-if="cur.status === '已派单'" type="warning" @click="openAction('process')">开始处理</el-button>
          <el-button v-if="cur.status === '处理中'" type="success" @click="openAction('finish')">完成维修</el-button>
          <el-tag v-if="['已完成', '已评价', '已驳回', '已取消'].includes(cur.status)" type="info" effect="plain">
            {{ cur.status === '已完成' ? '等待业主评价' : '工单已结束' }}
          </el-tag>
        </div>
      </template>
    </el-drawer>

    <!-- 操作对话框 -->
    <el-dialog v-model="actionVisible" :title="actionTitle" width="520px">
      <el-form :model="actionForm" label-width="90px">
        <el-form-item v-if="action === 'assign'" label="指派员工" required>
          <el-select v-model="actionForm.handlerId" placeholder="选择物业维修工" style="width: 100%">
            <el-option v-for="s in staffList" :key="s.id" :label="`${s.realName}（${s.phone}）`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="action === 'reject'" label="驳回原因" required>
          <el-input v-model="actionForm.reason" type="textarea" :rows="3" placeholder="请说明驳回原因，将反馈给业主" />
        </el-form-item>
        <el-form-item v-if="action === 'cancel'" label="取消原因">
          <el-input v-model="actionForm.reason" type="textarea" :rows="3" placeholder="请填写取消原因" />
        </el-form-item>
        <el-form-item v-if="['process', 'finish'].includes(action)" label="处理说明">
          <el-input v-model="actionForm.content" type="textarea" :rows="3" :placeholder="action === 'finish' ? '维修完成情况说明' : '处理进展说明'" />
        </el-form-item>
        <el-form-item v-if="['process', 'finish'].includes(action)" label="处理照片">
          <el-upload
            :action="uploadUrl" :headers="uploadHeaders" name="file"
            :show-file-list="false" :on-success="onUploaded" :on-error="onUploadError"
            accept="image/*">
            <el-button plain><el-icon><Upload /></el-icon>上传照片</el-button>
          </el-upload>
          <el-image v-if="actionForm.images" :src="actionForm.images" fit="cover"
            style="width: 90px; height: 70px; margin-left: 10px; border-radius: 8px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="actionVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAction">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import {
  repairPage, repairDetail, assignRepair, processRepair, finishRepair,
  rejectRepair, cancelRepair, getStaffList, downloadExport
} from '../../api'

const statusList = ['待受理', '已派单', '处理中', '已完成', '已评价', '已驳回', '已取消']
const types = ['水电', '门窗', '家电', '公共设施', '其他']

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = reactive({ current: 1, size: 10, keyword: '', status: '', repairType: '', urgency: '', timeoutOnly: false })
const cards = ref([])
const staffList = ref([])

const uploadUrl = '/api/upload'
const uploadHeaders = computed(() => ({ Authorization: 'Bearer ' + localStorage.getItem('token') }))

function urgencyType(u) {
  return { 一般: 'info', 紧急: 'warning', 非常紧急: 'danger' }[u] || 'info'
}

function statusType(s) {
  return { 待受理: 'danger', 已派单: 'warning', 处理中: 'primary', 已完成: 'success', 已评价: 'success', 已驳回: 'info', 已取消: 'info' }[s] || 'info'
}

function recordType(a) {
  return { 提交报修: 'primary', 受理工单: 'warning', 派单: 'warning', 处理中: 'primary', 完成: 'success', 评价: 'success', 已驳回: 'danger', 已取消: 'info' }[a] || 'info'
}

function shortTime(t) {
  return t ? t.slice(5, 16) : ''
}

async function load() {
  loading.value = true
  try {
    const d = await repairPage(q)
    rows.value = d.records
    total.value = d.total
  } finally {
    loading.value = false
  }
}

async function loadCards() {
  const [all, pending, assigned, processing, finished] = await Promise.all([
    repairPage({ current: 1, size: 1 }),
    repairPage({ current: 1, size: 1, status: '待受理' }),
    repairPage({ current: 1, size: 1, status: '已派单' }),
    repairPage({ current: 1, size: 1, status: '处理中' }),
    repairPage({ current: 1, size: 1, status: '已完成' })
  ])
  const to = await repairPage({ current: 1, size: 1, status: '待受理', timeoutOnly: true })
  cards.value = [
    { label: '工单总数', value: all.total, icon: 'Tickets', color: 'orange' },
    { label: '待受理', value: pending.total, icon: 'AlarmClock', color: 'red' },
    { label: '超时未受理', value: to.total, icon: 'Warning', color: 'red' },
    { label: '已派单', value: assigned.total, icon: 'Promotion', color: 'blue' },
    { label: '处理中', value: processing.total, icon: 'Tools', color: 'blue' },
    { label: '待评价 / 已完成', value: finished.total, icon: 'CircleCheck', color: 'green' }
  ]
}

function reset() {
  Object.assign(q, { current: 1, keyword: '', status: '', repairType: '', urgency: '', timeoutOnly: false })
  load()
}

const drawer = ref(false)
const cur = reactive({ records: [], images: [] })

const stepIndex = computed(() => {
  const map = { 待受理: 1, 已派单: 2, 处理中: 3, 已完成: 4, 已评价: 5 }
  if (['已驳回', '已取消'].includes(cur.status)) return 1
  return map[cur.status] || 0
})

async function openDetail(row) {
  const d = await repairDetail(row.id)
  Object.assign(cur, d)
  drawer.value = true
}

const actionVisible = ref(false)
const action = ref('')
const actionForm = reactive({ handlerId: null, reason: '', content: '', images: '' })
const actionTitle = computed(() => ({
  assign: '工单派单', reject: '驳回工单', cancel: '取消工单', process: '开始处理', finish: '完成维修'
}[action.value] || ''))

function openAction(type) {
  action.value = type
  Object.assign(actionForm, { handlerId: null, reason: '', content: '', images: '' })
  actionVisible.value = true
}

function onUploaded(res) {
  if (res.code === 200) {
    actionForm.images = res.data.url
    ElMessage.success('照片上传成功')
  } else {
    ElMessage.error(res.msg || '上传失败')
  }
}

function onUploadError() {
  ElMessage.error('照片上传失败')
}

async function submitAction() {
  const id = cur.id
  let res
  if (action.value === 'assign') {
    if (!actionForm.handlerId) {
      ElMessage.warning('请选择要指派的物业员工')
      return
    }
    res = await assignRepair(id, { handlerId: actionForm.handlerId })
  } else if (action.value === 'reject') {
    if (!actionForm.reason) {
      ElMessage.warning('请填写驳回原因')
      return
    }
    res = await rejectRepair(id, { reason: actionForm.reason })
  } else if (action.value === 'cancel') {
    res = await cancelRepair(id, { reason: actionForm.reason })
  } else if (action.value === 'process') {
    res = await processRepair(id, { content: actionForm.content, images: actionForm.images })
  } else if (action.value === 'finish') {
    res = await finishRepair(id, { content: actionForm.content, images: actionForm.images })
  }
  ElMessage.success('操作成功')
  actionVisible.value = false
  await openDetail({ id })
  load()
  loadCards()
}

function doExport() {
  downloadExport('/export/repairs', '报修工单明细.xlsx')
  ElMessage.success('正在导出报修工单...')
}

onMounted(async () => {
  staffList.value = await getStaffList()
  load()
  loadCards()
})
</script>

<style scoped>
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}

.action-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.rec-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rec-op {
  font-size: 12.5px;
  color: var(--pm-text-sub);
}

.rec-body {
  font-size: 13px;
  color: #57534e;
  margin-top: 5px;
  line-height: 1.6;
}
</style>
