<template>
  <div>
    <PageHeader title="访客登记" desc="管理业主访客预约、访客码与进出登记记录" />

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
        <el-input v-model="q.keyword" placeholder="访客姓名 / 电话 / 访客码 / 车牌" clearable style="width: 250px" @keyup.enter="load" />
        <el-select v-model="q.status" placeholder="状态" clearable style="width: 130px">
          <el-option v-for="s in ['待到访', '已到访', '已离开', '已取消']" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="load"><el-icon><Search /></el-icon>查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="success" @click="openForm()"><el-icon><Plus /></el-icon>代客登记</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="visitorName" label="访客姓名" width="100" />
        <el-table-column prop="phone" label="联系电话" width="130" />
        <el-table-column prop="ownerName" label="被访业主" width="100" />
        <el-table-column prop="roomName" label="到访房屋" min-width="150" />
        <el-table-column prop="visitCode" label="访客码" width="140" />
        <el-table-column prop="purpose" label="来访事由" width="130" />
        <el-table-column prop="carNo" label="车牌号" width="110">
          <template #default="{ row }">{{ row.carNo || '-' }}</template>
        </el-table-column>
        <el-table-column prop="visitTime" label="预约到访" width="160" />
        <el-table-column prop="leaveTime" label="离开时间" width="160">
          <template #default="{ row }">{{ row.leaveTime || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="95">
          <template #default="{ row }">
            <el-tag :type="{ 待到访: 'warning', 已到访: 'success', 已离开: 'info', 已取消: 'info' }[row.status]" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === '待到访'" link type="success" @click="checkin(row)">登记进入</el-button>
            <el-button v-if="row.status === '已到访'" link type="warning" @click="checkout(row)">登记离开</el-button>
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

    <el-dialog v-model="visible" :title="form.id ? '编辑访客登记' : '代客登记'" width="540px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="访客姓名" prop="visitorName">
          <el-input v-model="form.visitorName" placeholder="请输入访客姓名" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" maxlength="11" placeholder="11 位手机号" />
        </el-form-item>
        <el-form-item v-if="!form.id" label="被访业主" prop="ownerId">
          <el-select v-model="form.ownerId" filterable placeholder="选择业主" style="width: 100%" @change="onOwnerChange">
            <el-option v-for="o in owners" :key="o.id" :label="`${o.name}（${o.phone}）`" :value="o.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!form.id" label="到访房屋">
          <el-select v-model="form.roomId" clearable placeholder="默认业主主房屋" style="width: 100%">
            <el-option v-for="r in ownerRooms" :key="r.id" :label="r.roomName" :value="r.roomId" />
          </el-select>
        </el-form-item>
        <el-form-item label="到访时间" prop="visitTime">
          <el-date-picker v-model="form.visitTime" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="来访事由">
          <el-input v-model="form.purpose" placeholder="如 探亲、家政保洁" />
        </el-form-item>
        <el-form-item label="车牌号">
          <el-input v-model="form.carNo" placeholder="选填" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import {
  visitorPage, addVisitor, updateVisitor, checkinVisitor, checkoutVisitor, delVisitor,
  ownerList, ownerDetail
} from '../../api'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = reactive({ current: 1, size: 10, keyword: '', status: '' })
const owners = ref([])
const cards = ref([])

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

async function loadCards() {
  const [all, wait, in_, left] = await Promise.all([
    visitorPage({ current: 1, size: 1 }),
    visitorPage({ current: 1, size: 1, status: '待到访' }),
    visitorPage({ current: 1, size: 1, status: '已到访' }),
    visitorPage({ current: 1, size: 1, status: '已离开' })
  ])
  cards.value = [
    { label: '登记总数', value: all.total, icon: 'Postcard', color: 'orange' },
    { label: '待到访', value: wait.total, icon: 'Clock', color: 'blue' },
    { label: '在园中', value: in_.total, icon: 'CircleCheck', color: 'green' },
    { label: '已离开', value: left.total, icon: 'SwitchButton', color: 'red' }
  ]
}

function reset() {
  q.keyword = ''
  q.status = ''
  q.current = 1
  load()
}

const visible = ref(false)
const formRef = ref()
const form = reactive({ id: null, visitorName: '', phone: '', ownerId: null, roomId: null, visitTime: '', purpose: '', carNo: '', remark: '' })
const ownerRooms = ref([])
const rules = {
  visitorName: [{ required: true, message: '请输入访客姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^\d{11}$/, message: '请输入 11 位手机号', trigger: 'blur' }
  ],
  ownerId: [{ required: true, message: '请选择被访业主', trigger: 'change' }],
  visitTime: [{ required: true, message: '请选择到访时间', trigger: 'change' }]
}

function openForm(row) {
  if (row) {
    Object.assign(form, { id: row.id, visitorName: row.visitorName, phone: row.phone, ownerId: row.ownerId, roomId: row.roomId, visitTime: row.visitTime, purpose: row.purpose, carNo: row.carNo, remark: row.remark })
  } else {
    Object.assign(form, { id: null, visitorName: '', phone: '', ownerId: null, roomId: null, visitTime: '', purpose: '', carNo: '', remark: '' })
    ownerRooms.value = []
  }
  visible.value = true
}

async function onOwnerChange(id) {
  form.roomId = null
  if (!id) {
    ownerRooms.value = []
    return
  }
  const d = await ownerDetail(id)
  ownerRooms.value = (d.bindings || []).filter((b) => b.status === '有效')
}

async function save() {
  try {
    await formRef.value.validate()
  } catch (e) {
    return
  }
  if (form.id) {
    await updateVisitor(form.id, form)
    ElMessage.success('修改成功')
  } else {
    const d = await addVisitor(form)
    ElMessage.success(`登记成功，访客码 ${d.visitCode}`)
  }
  visible.value = false
  load()
  loadCards()
}

async function checkin(row) {
  await checkinVisitor(row.id)
  ElMessage.success('已登记进入小区')
  load()
  loadCards()
}

async function checkout(row) {
  await checkoutVisitor(row.id)
  ElMessage.success('已登记离开小区')
  load()
  loadCards()
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确定删除访客「${row.visitorName}」的登记记录吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await delVisitor(row.id)
  ElMessage.success('删除成功')
  load()
  loadCards()
}

onMounted(async () => {
  owners.value = await ownerList()
  load()
  loadCards()
})
</script>

<style scoped>
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
