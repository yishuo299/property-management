<template>
  <div>
    <PageHeader title="公告通知" desc="社区公告、缴费提醒与活动通知，点击查看详情即标记为已读" />

    <div class="toolbar">
      <el-radio-group v-model="filter" @change="applyFilter">
        <el-radio-button label="all">全部公告</el-radio-button>
        <el-radio-button label="unread">未读（{{ unread }})</el-radio-button>
      </el-radio-group>
      <div class="spacer"></div>
      <el-button plain @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
    </div>

    <div v-loading="loading">
      <div v-if="!shown.length" class="empty-tip">暂无公告</div>
      <div v-for="n in shown" :key="n.id" class="notice-item" :class="{ unread: !n.read }" @click="open(n)">
        <div class="notice-title">
          <span v-if="!n.read" class="dot-unread"></span>
          <el-tag v-if="n.isTop" type="danger" size="small" effect="dark" round>置顶</el-tag>
          <el-tag size="small" effect="light" :type="{ 通知: 'primary', 提醒: 'warning', 活动: 'success', 紧急: 'danger' }[n.noticeType]">{{ n.noticeType }}</el-tag>
          {{ n.title }}
        </div>
        <div class="notice-body">{{ n.content.slice(0, 110) }}{{ n.content.length > 110 ? '...' : '' }}</div>
        <div class="repair-card-meta">
          <span>发布：{{ n.publishTime }}</span>
          <span>有效期至：{{ n.expireTime || '长期有效' }}</span>
          <span>{{ n.read ? '已读' : '未读' }}</span>
        </div>
      </div>
    </div>

    <el-dialog v-model="visible" :title="cur.title" width="640px">
      <div class="rec-op" style="margin-bottom: 12px">
        发布人：{{ cur.publisherName }} · 发布时间：{{ cur.publishTime }} · 有效期至：{{ cur.expireTime || '长期有效' }}
      </div>
      <div class="notice-body">{{ cur.content }}</div>
      <template #footer>
        <el-button type="primary" @click="visible = false">我知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import { noticeList, noticeDetail } from '../../api'

const list = ref([])
const loading = ref(false)
const filter = ref('all')

const unread = computed(() => list.value.filter((n) => !n.read).length)
const shown = computed(() => (filter.value === 'unread' ? list.value.filter((n) => !n.read) : list.value))

async function load() {
  loading.value = true
  try {
    list.value = (await noticeList()) || []
  } finally {
    loading.value = false
  }
}

function applyFilter() {}

const visible = ref(false)
const cur = ref({})

async function open(n) {
  const d = await noticeDetail(n.id)
  cur.value = d
  visible.value = true
  const i = list.value.findIndex((x) => x.id === n.id)
  if (i >= 0) list.value[i].read = true
}

onMounted(load)
</script>

<style scoped>
.rec-op {
  font-size: 12.5px;
  color: var(--pm-text-sub);
}

.rec-body {
  font-size: 13px;
}
</style>
