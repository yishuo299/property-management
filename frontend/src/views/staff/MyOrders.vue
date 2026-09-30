<template>
  <div>
    <PageHeader title="我的工单" desc="查看指派给我的维修工单，更新处理进度并上传处理照片" />

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
        <el-input v-model="q.keyword" placeholder="工单号 / 报修内容" clearable style="width: 220px" @keyup.enter="load" />
        <el-select v-model="q.status" placeholder="工单状态" clearable style="width: 140px">
          <el-option v-for="s in ['已派单', '处理中', '已完成', '已评价']" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="load"><el-icon><Search /></el-icon>查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="orderNo" label="工单号" width="150" />
        <el-table-column prop="roomName" label="房屋" min-width="150" />
        <el-table-column prop="ownerName" label="业主" width="95" />
        <el-table-column prop="ownerPhone" label="联系电话" width="130" />
        <el-table-column prop="title" label="报修内容" min-width="190" show-overflow-tooltip />
        <el-table-column prop="repairType" label="类型" width="95" />
        <el-table-column label="紧急程度" width="100">
          <template #default="{ row }">
            <el-tag :type="{ 一般: 'info', 紧急: 'warning', 非常紧急: 'danger' }[row.urgency]" size="small" effect="light">{{ row.urgency }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="{ 已派单: 'warning', 处理中: 'primary', 已完成: 'success', 已评价: 'success' }[row.status]" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submitTime" label="提交时间" width="160" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button v-if="row.status === '已派单'" link type="warning" @click="openAction(row, 'process')">开始处理</el-button>
            <el-button v-if="row.status === '处理中'" link type="success" @click="openAction(row, 'finish')">完成维修</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager" background layout="total, prev, pager, next, sizes"
        :total="total" v-model:current-page="q.current" v-model:page-size="q.size"
        :page-sizes="[10, 20, 50]" @change="load" />
    </div>

    <el-drawer v-model="drawer" title="工单详情" size="580px">
      <template v-if="cur.id">
        <el-steps :active="stepIndex" align-center finish-status="success" style="margin-bottom: 18px">
          <el-step title="待受理" />
          <el-step title="已派单" :description="shortTime(cur.assignTime)" />
          <el-step title="处理中" />
          <el-step title="已完成" :description="shortTime(cur.finishTime)" />
          <el-step title="已评价" :description="cur.score ? cur.score + ' 星' : ''" />
        </el-steps>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="工单号">{{ cur.orderNo }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ cur.status }}</el-descriptions-item>
          <el-descriptions-item label="房屋">{{ cur.roomName }}</el-descriptions-item>
          <el-descriptions-item label="业主">{{ cur.ownerName }}（{{ cur.ownerPhone }}）</el-descriptions-item>
          <el-descriptions-item label="报修类型">{{ cur.repairType }}</el-descriptions-item>
          <el-descriptions-item label="紧急程度">{{ cur.urgency }}</el-descriptions-item>
          <el-descriptions-item label="报修内容" :span="2">{{ cur.content }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="cur.images && cur.images.length" style="margin-top: 12px">
          <div class="chart-title">业主上传的现场照片</div>
          <el-image v-for="img in cur.images" :key="img" :src="img" :preview-src-list="cur.images"
            fit="cover" style="width: 110px; height: 84px; margin-right: 8px; border-radius: 8px" />
        </div>
        <div class="chart-title" style="margin-top: 18px">处理记录</div>
        <el-timeline>
          <el-timeline-item v-for="r in cur.records" :key="r.id" :timestamp="r.createTime" placement="top">
            <el-tag size="small" effect="light">{{ r.action }}</el-tag>
            <span class="rec-op">{{ r.operatorName }}</span>
            <div class="rec-body">{{ r.content }}</div>
          </el-timeline-item>
        </el-timeline>
        <div class="action-bar" style="margin-top: 14px">
          <el-button v-if="cur.status === '已派单'" type="warning" @click="openAction(cur, 'process')">开始处理</el-button>
          <el-button v-if="cur.status === '处理中'" type="success" @click="openAction(cur, 'finish')">完成维修</el-button>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="actionVisible" :title="action === 'finish' ? '完成维修' : '开始处理'" width="520px">
      <el-form label-width="90px">
        <el-form-item label="处理说明">
          <el-input v-model="actionForm.content" type="textarea" :rows="3"
            :placeholder="action === 'finish' ? '请说明维修完成情况' : '请说明处理进展'" />
        </el-form-item>
        <el-form-item label="处理照片">
          <el-upload :action="uploadUrl" :headers="uploadHeaders" name="file"
            :show-file-list="false" :on-success="onUploaded" accept="image/*">
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
import { repairPage, repairDetail, processRepair, finishRepair } from '../../api'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = reactive({ current: 1, size: 10, keyword: '', status: '', mine: 1 })
const cards = ref([])

const uploadUrl = '/api/upload'
const uploadHeaders = computed(() => ({ Authorization: 'Bearer ' + localStorage.getItem('token') }))

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
  const [all, assigned, processing, done] = await Promise.all([
    repairPage({ current: 1, size: 1, mine: 1 }),
    repairPage({ current: 1, size: 1, mine: 1, status: '已派单' }),
    repairPage({ current: 1, size: 1, mine: 1, status: '处理中' }),
    repairPage({ current: 1, size: 1, mine: 1, status: '已完成' })
  ])
  const ev = await repairPage({ current: 1, size: 1, mine: 1, status: '已评价' })
  cards.value = [
    { label: '我的工单', value: all.total, icon: 'Tickets', color: 'orange' },
    { label: '待处理', value: assigned.total, icon: 'AlarmClock', color: 'red' },
    { label: '处理中', value: processing.total, icon: 'Tools', color: 'blue' },
    { label: '待业主评价', value: done.total, icon: 'CircleCheck', color: 'green' },
    { label: '已完成评价', value: ev.total, icon: 'Star', color: 'green' }
  ]
}

function reset() {
  q.keyword = ''
  q.status = ''
  q.current = 1
  load()
}

const drawer = ref(false)
const cur = reactive({ records: [], images: [] })

const stepIndex = computed(() => {
  const map = { 已派单: 2, 处理中: 3, 已完成: 4, 已评价: 5 }
  return map[cur.status] || 1
})

async function openDetail(row) {
  const d = await repairDetail(row.id)
  Object.assign(cur, d)
  drawer.value = true
}

const actionVisible = ref(false)
const action = ref('')
const actionForm = reactive({ content: '', images: '' })

function openAction(row, type) {
  action.value = type
  cur.id = row.id
  Object.assign(actionForm, { content: '', images: '' })
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

async function submitAction() {
  if (action.value === 'process') {
    await processRepair(cur.id, actionForm)
  } else {
    await finishRepair(cur.id, actionForm)
  }
  ElMessage.success('操作成功')
  actionVisible.value = false
  await openDetail({ id: cur.id })
  load()
  loadCards()
}

onMounted(() => {
  load()
  loadCards()
})
</script>

<style scoped>
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}

.rec-op {
  font-size: 12.5px;
  color: var(--pm-text-sub);
  margin-left: 8px;
}

.rec-body {
  font-size: 13px;
  color: #57534e;
  margin-top: 5px;
}

.action-bar {
  display: flex;
  gap: 10px;
}
</style>
