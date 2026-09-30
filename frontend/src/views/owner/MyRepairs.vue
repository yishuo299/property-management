<template>
  <div>
    <PageHeader title="我的报修" desc="查看报修进度，确认维修完成并评价服务" />

    <div class="toolbar">
      <el-radio-group v-model="q.status" @change="load">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button v-for="s in statusList" :key="s" :label="s" />
      </el-radio-group>
      <div class="spacer"></div>
      <el-button type="primary" @click="$router.push('/new-repair')"><el-icon><EditPen /></el-icon>我要报修</el-button>
    </div>

    <div v-loading="loading">
      <div v-if="!rows.length" class="empty-tip">暂无报修记录，点击「我要报修」提交第一条吧</div>
      <div
        v-for="r in rows" :key="r.id"
        class="repair-card"
        :class="{ done: ['已完成', '已评价'].includes(r.status), warn: r.timeout }"
        @click="openDetail(r)">
        <div class="repair-card-head">
          <div class="repair-card-title">
            <el-tag size="small" effect="light" :type="statusType(r.status)">{{ r.status }}</el-tag>
            <span style="margin-left: 8px">{{ r.title }}</span>
          </div>
          <div>
            <el-tag v-if="r.timeout" type="danger" size="small" effect="dark">已超时</el-tag>
            <el-tag v-else size="small" effect="plain">{{ r.repairType }}</el-tag>
          </div>
        </div>
        <div class="repair-card-meta">
          <span>工单号：{{ r.orderNo }}</span>
          <span>房屋：{{ r.roomName }}</span>
          <span>紧急程度：{{ r.urgency }}</span>
          <span>提交时间：{{ r.submitTime }}</span>
          <span v-if="r.handlerName">维修工：{{ r.handlerName }}</span>
          <span v-if="r.score">评分：{{ r.score }} 星</span>
        </div>
        <div v-if="r.content" class="rec-body">{{ r.content }}</div>
      </div>
      <el-pagination
        v-if="total > q.size"
        class="pager" background layout="total, prev, pager, next"
        :total="total" v-model:current-page="q.current" v-model:page-size="q.size" @change="load" />
    </div>

    <el-dialog v-model="visible" title="报修详情" width="620px">
      <template v-if="cur.id">
        <el-steps :active="stepIndex" align-center finish-status="success" style="margin-bottom: 18px">
          <el-step title="待受理" :description="shortTime(cur.submitTime)" />
          <el-step title="已派单" :description="shortTime(cur.assignTime)" />
          <el-step title="处理中" :description="cur.handlerName || ''" />
          <el-step title="已完成" :description="shortTime(cur.finishTime)" />
          <el-step title="已评价" :description="cur.score ? cur.score + ' 星' : ''" />
        </el-steps>

        <el-alert v-if="['已驳回', '已取消'].includes(cur.status)" type="info" :closable="false" show-icon
          :title="`该工单${cur.status}：${cur.remark || ''}`" style="margin-bottom: 12px" />

        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="工单号">{{ cur.orderNo }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag size="small" effect="light" :type="statusType(cur.status)">{{ cur.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="房屋">{{ cur.roomName }}</el-descriptions-item>
          <el-descriptions-item label="报修类型">{{ cur.repairType }}</el-descriptions-item>
          <el-descriptions-item label="紧急程度">{{ cur.urgency }}</el-descriptions-item>
          <el-descriptions-item label="维修工">{{ cur.handlerName || '待指派' }}</el-descriptions-item>
          <el-descriptions-item label="问题描述" :span="2">{{ cur.content }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="cur.images && cur.images.length" style="margin-top: 12px">
          <div class="chart-title">我上传的照片</div>
          <el-image v-for="img in cur.images" :key="img" :src="img" :preview-src-list="cur.images"
            fit="cover" style="width: 100px; height: 76px; margin-right: 8px; border-radius: 8px" />
        </div>

        <div class="chart-title" style="margin-top: 18px">处理进度</div>
        <el-timeline>
          <el-timeline-item v-for="r in cur.records" :key="r.id" :timestamp="r.createTime" placement="top">
            <el-tag size="small" effect="light">{{ r.action }}</el-tag>
            <span class="rec-op">{{ r.operatorName }}</span>
            <div class="rec-body">{{ r.content }}</div>
            <div v-if="r.images && r.images.length">
              <el-image v-for="img in r.images" :key="img" :src="img" :preview-src-list="r.images"
                fit="cover" style="width: 92px; height: 70px; margin: 6px 8px 0 0; border-radius: 8px" />
            </div>
          </el-timeline-item>
        </el-timeline>

        <div v-if="cur.evaluation" style="margin-top: 8px">
          <el-divider content-position="left">我的评价</el-divider>
          <el-rate :model-value="cur.evaluation.score" disabled show-score />
          <div class="rec-body">{{ cur.evaluation.content }}</div>
        </div>

        <div class="action-bar" style="margin-top: 14px">
          <el-button v-if="cur.status === '已完成'" type="success" @click="openEvaluate">
            <el-icon><Star /></el-icon>确认完成并评价
          </el-button>
          <el-button v-if="['待受理', '已派单'].includes(cur.status)" plain @click="cancelOrder">取消报修</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="evalVisible" title="服务评价" width="500px">
      <el-form :model="evalForm" :rules="evalRules" ref="evalFormRef" label-width="90px">
        <el-form-item label="综合评分" prop="score">
          <el-rate v-model="evalForm.score" show-text :texts="['很不满意', '不满意', '一般', '满意', '非常满意']" />
        </el-form-item>
        <el-form-item label="服务态度">
          <el-rate v-model="evalForm.attitudeScore" />
        </el-form-item>
        <el-form-item label="处理速度">
          <el-rate v-model="evalForm.speedScore" />
        </el-form-item>
        <el-form-item label="评价内容">
          <el-input v-model="evalForm.content" type="textarea" :rows="3" placeholder="说说本次维修服务的感受（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="evalVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEvaluate">提交评价</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import { repairMine, repairDetail, evaluateRepair, cancelRepair } from '../../api'

const statusList = ['待受理', '已派单', '处理中', '已完成', '已评价', '已驳回', '已取消']
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = reactive({ current: 1, size: 5, status: '' })

function statusType(s) {
  return { 待受理: 'danger', 已派单: 'warning', 处理中: 'primary', 已完成: 'success', 已评价: 'success', 已驳回: 'info', 已取消: 'info' }[s] || 'info'
}

function shortTime(t) {
  return t ? t.slice(5, 16) : ''
}

async function load() {
  loading.value = true
  try {
    const d = await repairMine(q)
    rows.value = d.records
    total.value = d.total
  } finally {
    loading.value = false
  }
}

const visible = ref(false)
const cur = reactive({ records: [], images: [] })

const stepIndex = computed(() => {
  const map = { 待受理: 1, 已派单: 2, 处理中: 3, 已完成: 4, 已评价: 5 }
  if (['已驳回', '已取消'].includes(cur.status)) return 1
  return map[cur.status] || 0
})

async function openDetail(row) {
  const d = await repairDetail(row.id)
  Object.assign(cur, d)
  visible.value = true
}

const evalVisible = ref(false)
const evalFormRef = ref()
const evalForm = reactive({ score: 5, attitudeScore: 5, speedScore: 5, content: '' })
const evalRules = {
  score: [{ required: true, message: '请给出综合评分', trigger: 'change' }]
}

function openEvaluate() {
  Object.assign(evalForm, { score: 5, attitudeScore: 5, speedScore: 5, content: '' })
  evalVisible.value = true
}

async function submitEvaluate() {
  try {
    await evalFormRef.value.validate()
  } catch (e) {
    return
  }
  await evaluateRepair(cur.id, evalForm)
  ElMessage.success('感谢您的评价')
  evalVisible.value = false
  visible.value = false
  load()
}

async function cancelOrder() {
  let reason
  try {
    const r = await ElMessageBox.prompt('请填写取消原因', '取消报修', {
      inputPlaceholder: '如：问题已自行解决',
      inputValue: '问题已自行解决'
    })
    reason = r.value
  } catch (e) {
    return
  }
  await cancelRepair(cur.id, { reason })
  ElMessage.success('工单已取消')
  visible.value = false
  load()
}

onMounted(load)
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
