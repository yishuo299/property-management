<template>
  <div>
    <PageHeader title="访客预约" desc="提前为访客预约登记，生成访客码，访客凭码进出小区" />

    <div class="page-card">
      <div class="toolbar">
        <el-input v-model="q.keyword" placeholder="访客姓名 / 电话 / 访客码" clearable style="width: 240px" @keyup.enter="load" />
        <el-select v-model="q.status" placeholder="状态" clearable style="width: 130px">
          <el-option v-for="s in ['待到访', '已到访', '已离开', '已取消']" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="load"><el-icon><Search /></el-icon>查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="success" @click="openForm"><el-icon><Plus /></el-icon>预约访客</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="visitorName" label="访客姓名" width="110" />
        <el-table-column prop="phone" label="联系电话" width="140" />
        <el-table-column prop="roomName" label="到访房屋" min-width="160" />
        <el-table-column label="访客码" width="150">
          <template #default="{ row }">
            <el-tag type="warning" effect="plain" style="font-family: monospace">{{ row.visitCode }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="purpose" label="来访事由" width="130" />
        <el-table-column prop="carNo" label="车牌号" width="110">
          <template #default="{ row }">{{ row.carNo || '-' }}</template>
        </el-table-column>
        <el-table-column prop="visitTime" label="预约到访时间" width="165" />
        <el-table-column prop="leaveTime" label="离开时间" width="165">
          <template #default="{ row }">{{ row.leaveTime || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="95">
          <template #default="{ row }">
            <el-tag :type="{ 待到访: 'warning', 已到访: 'success', 已离开: 'info', 已取消: 'info' }[row.status]" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === '待到访'" link type="danger" @click="cancel(row)">取消预约</el-button>
            <span v-else style="color: #a8a29e; font-size: 12.5px">-</span>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager" background layout="total, prev, pager, next, sizes"
        :total="total" v-model:current-page="q.current" v-model:page-size="q.size"
        :page-sizes="[10, 20, 50]" @change="load" />
    </div>

    <el-dialog v-model="visible" title="预约访客" width="540px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="访客姓名" prop="visitorName">
          <el-input v-model="form.visitorName" placeholder="请输入访客姓名" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" maxlength="11" placeholder="11 位手机号，用于门岗核验" />
        </el-form-item>
        <el-form-item label="到访房屋" prop="roomId">
          <el-select v-model="form.roomId" placeholder="请选择到访房屋" style="width: 100%">
            <el-option v-for="r in rooms" :key="r.roomId" :label="r.roomName" :value="r.roomId" />
          </el-select>
        </el-form-item>
        <el-form-item label="到访时间" prop="visitTime">
          <el-date-picker v-model="form.visitTime" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="选择预约到访时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="来访事由">
          <el-input v-model="form.purpose" placeholder="如 探亲、朋友聚会、家政保洁" />
        </el-form-item>
        <el-form-item label="车牌号">
          <el-input v-model="form.carNo" placeholder="选填，便于门岗放行" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="save">提交预约</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import { visitorPage, addVisitor, cancelVisitor, ownerDetail, getInfo } from '../../api'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = reactive({ current: 1, size: 10, keyword: '', status: '' })
const rooms = ref([])

async function load() {
  loading.value = true
  try {
    const d = await visitorPage(q)
    rows.value = d.records
    total.value = d.total
  } finally {
    loading.value = false
  }
}

function reset() {
  q.keyword = ''
  q.status = ''
  q.current = 1
  load()
}

const visible = ref(false)
const formRef = ref()
const form = reactive({ visitorName: '', phone: '', roomId: null, visitTime: '', purpose: '', carNo: '' })
const rules = {
  visitorName: [{ required: true, message: '请输入访客姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^\d{11}$/, message: '请输入 11 位手机号', trigger: 'blur' }
  ],
  roomId: [{ required: true, message: '请选择到访房屋', trigger: 'change' }],
  visitTime: [{ required: true, message: '请选择到访时间', trigger: 'change' }]
}

function openForm() {
  if (!rooms.value.length) {
    ElMessage.warning('您名下暂无房屋，无法预约访客')
    return
  }
  Object.assign(form, { visitorName: '', phone: '', roomId: rooms.value[0]?.roomId || null, visitTime: '', purpose: '', carNo: '' })
  visible.value = true
}

async function save() {
  try {
    await formRef.value.validate()
  } catch (e) {
    return
  }
  const d = await addVisitor(form)
  ElMessage.success(`预约成功，访客码：${d.visitCode}`)
  visible.value = false
  load()
}

async function cancel(row) {
  try {
    await ElMessageBox.confirm(`确定取消访客「${row.visitorName}」的预约吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await cancelVisitor(row.id)
  ElMessage.success('预约已取消')
  load()
}

onMounted(async () => {
  const info = await getInfo()
  if (info.ownerId) {
    const d = await ownerDetail(info.ownerId)
    rooms.value = (d.bindings || []).filter((b) => b.status === '有效')
  }
  load()
})
</script>

<style scoped>
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
