<template>
  <div>
    <PageHeader title="停车位管理" desc="维护车位编号、类型（地上/地下/固定/临时）、车位费与业主绑定" />

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
        <el-input v-model="q.keyword" placeholder="车位编号 / 区域" clearable style="width: 200px" @keyup.enter="load" />
        <el-select v-model="q.spotType" placeholder="车位类型" clearable style="width: 130px">
          <el-option v-for="t in ['地上', '地下', '固定', '临时']" :key="t" :label="t" :value="t" />
        </el-select>
        <el-select v-model="q.status" placeholder="使用状态" clearable style="width: 130px">
          <el-option v-for="s in ['空闲', '已租', '停用']" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="load"><el-icon><Search /></el-icon>查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="success" @click="openForm()"><el-icon><Plus /></el-icon>新增车位</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="spotNo" label="车位编号" width="110" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="light" :type="{ 地上: 'success', 地下: 'primary', 固定: 'warning', 临时: 'info' }[row.spotType]">{{ row.spotType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="area" label="所在区域" min-width="150" />
        <el-table-column prop="ownerName" label="绑定业主" width="110">
          <template #default="{ row }">{{ row.ownerName || '-' }}</template>
        </el-table-column>
        <el-table-column prop="roomName" label="绑定房屋" min-width="150">
          <template #default="{ row }">{{ row.roomName || '-' }}</template>
        </el-table-column>
        <el-table-column prop="fee" label="车位费(元/月)" width="130" />
        <el-table-column label="状态" width="95">
          <template #default="{ row }">
            <el-tag :type="{ 已租: 'success', 空闲: 'info', 停用: 'danger' }[row.status]" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="租期" min-width="180">
          <template #default="{ row }">
            <span v-if="row.startDate">{{ row.startDate }} ~ {{ row.endDate || '长期' }}</span>
            <span v-else style="color: #a8a29e">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="130" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openForm(row)">编辑</el-button>
            <el-button v-if="row.status !== '已租'" link type="success" @click="openBind(row)">绑定业主</el-button>
            <el-button v-else link type="warning" @click="release(row)">释放</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager" background layout="total, prev, pager, next, sizes"
        :total="total" v-model:current-page="q.current" v-model:page-size="q.size"
        :page-sizes="[10, 20, 50]" @change="load" />
    </div>

    <el-dialog v-model="visible" :title="form.id ? '编辑车位' : '新增车位'" width="520px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="车位编号" prop="spotNo">
          <el-input v-model="form.spotNo" :disabled="!!form.id" placeholder="如 D-013" />
        </el-form-item>
        <el-form-item label="车位类型" prop="spotType">
          <el-radio-group v-model="form.spotType">
            <el-radio-button v-for="t in ['地上', '地下', '固定', '临时']" :key="t" :label="t" />
          </el-radio-group>
        </el-form-item>
        <el-form-item label="所在区域">
          <el-input v-model="form.area" placeholder="如 地下车库A区" />
        </el-form-item>
        <el-form-item label="车位费(元/月)" prop="fee">
          <el-input-number v-model="form.fee" :min="0" :max="5000" :precision="2" :step="10" />
        </el-form-item>
        <el-form-item label="使用状态">
          <el-select v-model="form.status" :disabled="form.status === '已租'" style="width: 100%">
            <el-option label="空闲" value="空闲" />
            <el-option label="停用" value="停用" />
            <el-option v-if="form.status === '已租'" label="已租" value="已租" />
          </el-select>
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

    <el-dialog v-model="bindVisible" title="车位绑定业主" width="500px">
      <el-form :model="bindForm" :rules="bindRules" ref="bindFormRef" label-width="110px">
        <el-form-item label="车位">{{ bindForm.spotNo }}</el-form-item>
        <el-form-item label="业主" prop="ownerId">
          <el-select v-model="bindForm.ownerId" filterable placeholder="选择业主" style="width: 100%" @change="onOwnerChange">
            <el-option v-for="o in owners" :key="o.id" :label="`${o.name}（${o.phone}）`" :value="o.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="绑定房屋">
          <el-select v-model="bindForm.roomId" clearable placeholder="选择该业主名下房屋" style="width: 100%">
            <el-option v-for="r in ownerRooms" :key="r.id" :label="r.roomName" :value="r.roomId" />
          </el-select>
        </el-form-item>
        <el-form-item label="租用开始">
          <el-date-picker v-model="bindForm.startDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="租用结束">
          <el-date-picker v-model="bindForm.endDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bindVisible = false">取消</el-button>
        <el-button type="primary" @click="doBind">确认绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import {
  parkingPage, parkingList, addParking, updateParking, delParking,
  bindParking, releaseParking, ownerList, ownerDetail
} from '../../api'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = reactive({ current: 1, size: 10, keyword: '', spotType: '', status: '' })
const owners = ref([])
const allSpots = ref([])

const cards = computed(() => {
  const s = allSpots.value
  return [
    { label: '车位总数', value: s.length, icon: 'Van', color: 'orange' },
    { label: '已租', value: s.filter((x) => x.status === '已租').length, icon: 'CircleCheck', color: 'green' },
    { label: '空闲', value: s.filter((x) => x.status === '空闲').length, icon: 'Sunny', color: 'blue' },
    { label: '停用', value: s.filter((x) => x.status === '停用').length, icon: 'Warning', color: 'red' },
    { label: '月度车位费收入', value: s.filter((x) => x.status === '已租').reduce((a, b) => a + b.fee, 0).toFixed(2), icon: 'Money', color: 'green' }
  ]
})

async function load() {
  loading.value = true
  try {
    const d = await parkingPage(q)
    rows.value = d.records
    total.value = d.total
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(q, { current: 1, keyword: '', spotType: '', status: '' })
  load()
}

const visible = ref(false)
const formRef = ref()
const form = reactive({ id: null, spotNo: '', spotType: '地上', area: '', fee: 120, status: '空闲', remark: '' })
const rules = {
  spotNo: [{ required: true, message: '请输入车位编号', trigger: 'blur' }],
  spotType: [{ required: true, message: '请选择车位类型', trigger: 'change' }],
  fee: [{ required: true, message: '请输入车位费', trigger: 'blur' }]
}

function openForm(row) {
  if (row) {
    Object.assign(form, row)
  } else {
    Object.assign(form, { id: null, spotNo: '', spotType: '地上', area: '', fee: 120, status: '空闲', remark: '' })
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
    await updateParking(form.id, form)
    ElMessage.success('修改成功')
  } else {
    await addParking(form)
    ElMessage.success('新增成功')
  }
  visible.value = false
  load()
  loadSpots()
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确定删除车位「${row.spotNo}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await delParking(row.id)
  ElMessage.success('删除成功')
  load()
  loadSpots()
}

const bindVisible = ref(false)
const bindFormRef = ref()
const bindForm = reactive({ id: null, spotNo: '', ownerId: null, roomId: null, startDate: '', endDate: '' })
const ownerRooms = ref([])
const bindRules = {
  ownerId: [{ required: true, message: '请选择业主', trigger: 'change' }]
}

function openBind(row) {
  Object.assign(bindForm, { id: row.id, spotNo: row.spotNo, ownerId: null, roomId: null, startDate: '', endDate: '' })
  ownerRooms.value = []
  bindVisible.value = true
}

async function onOwnerChange(id) {
  bindForm.roomId = null
  if (!id) {
    ownerRooms.value = []
    return
  }
  const d = await ownerDetail(id)
  ownerRooms.value = (d.bindings || []).filter((b) => b.status === '有效')
}

async function doBind() {
  try {
    await bindFormRef.value.validate()
  } catch (e) {
    return
  }
  await bindParking(bindForm.id, bindForm)
  ElMessage.success('绑定成功')
  bindVisible.value = false
  load()
  loadSpots()
}

async function release(row) {
  try {
    await ElMessageBox.confirm(`确定释放车位「${row.spotNo}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await releaseParking(row.id)
  ElMessage.success('车位已释放')
  load()
  loadSpots()
}

async function loadSpots() {
  allSpots.value = await parkingList()
}

onMounted(async () => {
  owners.value = await ownerList()
  await loadSpots()
  load()
})
</script>

<style scoped>
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
