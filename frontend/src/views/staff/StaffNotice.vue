<template>
  <div>
    <PageHeader title="公告通知" desc="查看物业服务中心发布的公告与工作通知" />

    <div v-loading="loading">
      <div v-if="!list.length" class="empty-tip">暂无公告</div>
      <div v-for="n in list" :key="n.id" class="notice-item" :class="{ unread: !n.read }" @click="open(n)">
        <div class="notice-title">
          <span v-if="!n.read" class="dot-unread"></span>
          <el-tag v-if="n.isTop" type="danger" size="small" effect="dark" round>置顶</el-tag>
          <el-tag size="small" effect="light" :type="{ 通知: 'primary', 提醒: 'warning', 活动: 'success', 紧急: 'danger' }[n.noticeType]">{{ n.noticeType }}</el-tag>
          {{ n.title }}
        </div>
        <div class="notice-body">{{ n.content.slice(0, 120) }}{{ n.content.length > 120 ? '...' : '' }}</div>
        <div class="repair-card-meta">
          <span>发布：{{ n.publishTime }}</span>
          <span>{{ n.publisherName }}</span>
        </div>
      </div>
    </div>

    <el-dialog v-model="visible" :title="cur.title" width="640px">
      <div class="rec-op" style="margin-bottom: 12px">
        发布人：{{ cur.publisherName }} · 发布时间：{{ cur.publishTime }}
      </div>
      <div class="notice-body">{{ cur.content }}</div>
      <template #footer>
        <el-button type="primary" @click="visible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import { noticeList, noticeDetail } from '../../api'

const list = ref([])
const loading = ref(false)
const visible = ref(false)
const cur = ref({})

async function load() {
  loading.value = true
  try {
    list.value = (await noticeList()) || []
  } finally {
    loading.value = false
  }
}

async function open(n) {
  cur.value = await noticeDetail(n.id)
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
</style>
