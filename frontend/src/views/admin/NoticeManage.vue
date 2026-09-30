<template>
  <div>
    <PageHeader title="公告管理" desc="发布社区公告通知，支持置顶、有效期设置与业主已读统计" />

    <div class="page-card">
      <div class="toolbar">
        <el-input v-model="q.keyword" placeholder="标题 / 内容" clearable style="width: 220px" @keyup.enter="load" />
        <el-select v-model="q.noticeType" placeholder="公告类型" clearable style="width: 130px">
          <el-option v-for="t in ['通知', '提醒', '活动', '紧急']" :key="t" :label="t" :value="t" />
        </el-select>
        <el-select v-model="q.status" placeholder="发布状态" clearable style="width: 130px">
          <el-option label="已发布" value="已发布" />
          <el-option label="已下线" value="已下线" />
        </el-select>
        <el-button type="primary" @click="load"><el-icon><Search /></el-icon>查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="success" @click="openForm()"><el-icon><Plus /></el-icon>发布公告</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column label="标题" min-width="260">
          <template #default="{ row }">
            <el-tag v-if="row.isTop" type="danger" size="small" effect="dark" style="margin-right: 6px">置顶</el-tag>
            <span style="font-weight: 500">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="95">
          <template #default="{ row }">
            <el-tag size="small" effect="light" :type="{ 通知: 'primary', 提醒: 'warning', 活动: 'success', 紧急: 'danger' }[row.noticeType]">{{ row.noticeType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="publisherName" label="发布人" width="110" />
        <el-table-column prop="publishTime" label="发布时间" width="160" />
        <el-table-column prop="expireTime" label="有效期至" width="160">
          <template #default="{ row }">{{ row.expireTime || '长期有效' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="95">
          <template #default="{ row }">
            <el-tag :type="row.status === '已发布' ? 'success' : 'info'" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openView(row)">查看</el-button>
            <el-button link type="primary" @click="openForm(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager" background layout="total, prev, pager, next, sizes"
        :total="total" v-model:current-page="q.current" v-model:page-size="q.size"
        :page-sizes="[10, 20, 50]" @change="load" />
    </div>

    <el-dialog v-model="visible" :title="form.id ? '编辑公告' : '发布公告'" width="640px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="公告标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入公告标题" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="公告类型" prop="noticeType">
          <el-radio-group v-model="form.noticeType">
            <el-radio-button v-for="t in ['通知', '提醒', '活动', '紧急']" :key="t" :label="t" />
          </el-radio-group>
        </el-form-item>
        <el-form-item label="公告内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="7" placeholder="请输入公告正文内容" maxlength="2000" show-word-limit />
        </el-form-item>
        <el-form-item label="是否置顶">
          <el-switch v-model="form.isTop" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="发布状态">
          <el-radio-group v-model="form.status">
            <el-radio-button label="已发布" />
            <el-radio-button label="已下线" />
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="viewVisible" :title="view.title" width="620px">
      <div class="rec-op" style="margin-bottom: 10px">
        发布人：{{ view.publisherName }} · 发布时间：{{ view.publishTime }} · 有效期至：{{ view.expireTime || '长期有效' }}
      </div>
      <div class="notice-body">{{ view.content }}</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import { noticePage, noticeDetail, addNotice, updateNotice, delNotice } from '../../api'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = reactive({ current: 1, size: 10, keyword: '', noticeType: '', status: '' })

const visible = ref(false)
const formRef = ref()
const form = reactive({ id: null, title: '', content: '', noticeType: '通知', isTop: 0, status: '已发布', remark: '' })
const rules = {
  title: [{ required: true, message: '请输入公告标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入公告内容', trigger: 'blur' }]
}

async function load() {
  loading.value = true
  try {
    const d = await noticePage(q)
    rows.value = d.records
    total.value = d.total
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(q, { current: 1, keyword: '', noticeType: '', status: '' })
  load()
}

function openForm(row) {
  if (row) {
    Object.assign(form, { id: row.id, title: row.title, content: row.content, noticeType: row.noticeType, isTop: row.isTop, status: row.status, remark: '' })
  } else {
    Object.assign(form, { id: null, title: '', content: '', noticeType: '通知', isTop: 0, status: '已发布', remark: '' })
  }
  visible.value = true
}

async function save() {
  try {
    await formRef.value.validate()
  } catch (e) {
    return
  }
  if (form.id) {
    await updateNotice(form.id, form)
    ElMessage.success('修改成功')
  } else {
    await addNotice(form)
    ElMessage.success('发布成功')
  }
  visible.value = false
  load()
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确定删除公告「${row.title}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await delNotice(row.id)
  ElMessage.success('删除成功')
  load()
}

const viewVisible = ref(false)
const view = reactive({})

async function openView(row) {
  const d = await noticeDetail(row.id)
  Object.assign(view, d)
  viewVisible.value = true
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
}
</style>
