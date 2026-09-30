<template>
  <div>
    <PageHeader title="房屋管理" desc="按楼栋、单元、房号维护房屋面积、户型与使用状态" />

    <div class="page-card">
      <div class="toolbar">
        <el-select v-model="q.buildingId" placeholder="楼栋" clearable style="width: 140px" @change="onBuildingChange">
          <el-option v-for="b in buildings" :key="b.id" :label="b.buildingName" :value="b.id" />
        </el-select>
        <el-select v-model="q.unitId" placeholder="单元" clearable style="width: 130px">
          <el-option v-for="u in unitOptions" :key="u.id" :label="u.unitName" :value="u.id" />
        </el-select>
        <el-select v-model="q.status" placeholder="使用状态" clearable style="width: 130px">
          <el-option label="自住" value="自住" />
          <el-option label="出租" value="出租" />
          <el-option label="空置" value="空置" />
        </el-select>
        <el-select v-model="q.layout" placeholder="户型" clearable style="width: 130px">
          <el-option v-for="l in ['1室1厅', '2室1厅', '2室2厅', '3室2厅', '4室2厅']" :key="l" :label="l" :value="l" />
        </el-select>
        <el-input v-model="q.keyword" placeholder="房号" clearable style="width: 120px" @keyup.enter="load" />
        <el-button type="primary" @click="load"><el-icon><Search /></el-icon>查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="success" @click="openForm()"><el-icon><Plus /></el-icon>新增房屋</el-button>
        <el-button type="warning" plain @click="showBindings">业主绑定</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="buildingName" label="楼栋" width="100" />
        <el-table-column prop="unitName" label="单元" width="90" />
        <el-table-column prop="roomNo" label="房号" width="90" />
        <el-table-column prop="floorNo" label="楼层" width="80" />
        <el-table-column prop="area" label="面积(㎡)" width="100" />
        <el-table-column prop="layout" label="户型" width="100" />
        <el-table-column prop="orientation" label="朝向" width="100" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="{ 自住: 'success', 出租: 'warning', 空置: 'info' }[row.status]" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openForm(row)">编辑</el-button>
            <el-button link type="success" @click="openBind(row)">绑定业主</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager" background layout="total, prev, pager, next, sizes"
        :total="total" v-model:current-page="q.current" v-model:page-size="q.size"
        :page-sizes="[10, 20, 50]" @change="load" />
    </div>

    <!-- 房屋表单 -->
    <el-dialog v-model="visible" :title="form.id ? '编辑房屋' : '新增房屋'" width="520px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="所属楼栋" prop="buildingId">
          <el-select v-model="form.buildingId" :disabled="!!form.id" style="width: 100%" @change="onFormBuildingChange">
            <el-option v-for="b in buildings" :key="b.id" :label="b.buildingName" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属单元" prop="unitId">
          <el-select v-model="form.unitId" :disabled="!!form.id" style="width: 100%">
            <el-option v-for="u in formUnits" :key="u.id" :label="u.unitName" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="房号" prop="roomNo">
          <el-input v-model="form.roomNo" :disabled="!!form.id" placeholder="如 601" />
        </el-form-item>
        <el-form-item label="楼层" prop="floorNo">
          <el-input-number v-model="form.floorNo" :min="1" :max="60" />
        </el-form-item>
        <el-form-item label="建筑面积" prop="area">
          <el-input-number v-model="form.area" :min="10" :max="1000" :precision="2" :step="5" />
          <span style="margin-left: 8px; color: #78716c">㎡</span>
        </el-form-item>
        <el-form-item label="户型">
          <el-select v-model="form.layout" style="width: 100%">
            <el-option v-for="l in ['1室1厅', '2室1厅', '2室2厅', '3室2厅', '4室2厅']" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="朝向">
          <el-input v-model="form.orientation" placeholder="如 南北通透" />
        </el-form-item>
        <el-form-item label="使用状态">
          <el-radio-group v-model="form.status">
            <el-radio-button label="自住" />
            <el-radio-button label="出租" />
            <el-radio-button label="空置" />
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 绑定业主 -->
    <el-dialog v-model="bindVisible" title="绑定业主" width="560px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 14px"
        :title="`房屋：${bindRoom.roomName || ''}`" description="一个房屋可以绑定多位业主（如夫妻共同持有），其中一位为主产权人。" />
      <el-table :data="bindings" size="small" border>
        <el-table-column prop="ownerName" label="业主" width="100" />
        <el-table-column prop="relation" label="关系" width="90" />
        <el-table-column label="主产权人" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.isPrimary" type="warning" size="small" effect="dark">是</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '有效' ? 'success' : 'info'" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="startDate" label="起始日期" width="110" />
        <el-table-column prop="endDate" label="结束日期" width="110" />
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button v-if="!row.isPrimary" link type="danger" @click="unbind(row)">解绑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-divider>新增绑定</el-divider>
      <el-form :model="bindForm" label-width="90px" inline>
        <el-form-item label="业主">
          <el-select v-model="bindForm.ownerId" filterable placeholder="选择业主" style="width: 170px">
            <el-option v-for="o in owners" :key="o.id" :label="`${o.name}（${o.phone}）`" :value="o.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关系">
          <el-select v-model="bindForm.relation" style="width: 120px">
            <el-option v-for="r in ['产权人', '配偶', '子女', '父母', '租客']" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="主产权人">
          <el-switch v-model="bindForm.isPrimary" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bindVisible = false">关闭</el-button>
        <el-button type="primary" @click="doBind">确认绑定</el-button>
      </template>
    </el-dialog>

    <!-- 按房屋查看绑定 -->
    <el-dialog v-model="lookupVisible" title="查询房屋的业主绑定关系" width="480px">
      <el-form label-width="90px">
        <el-form-item label="选择房屋">
          <el-select v-model="lookupRoomId" filterable placeholder="输入楼栋单元房号搜索" style="width: 100%" @change="loadBindingsById">
            <el-option v-for="r in roomOptions" :key="r.id" :label="r.fullName" :value="r.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-table :data="bindings" size="small" border>
        <el-table-column prop="ownerName" label="业主" width="100" />
        <el-table-column prop="relation" label="关系" width="90" />
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column prop="startDate" label="起始日期" />
        <el-table-column prop="endDate" label="结束日期" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import {
  buildingList, unitList, roomPage, roomList, addRoom, updateRoom, delRoom,
  ownerList, roomBindings, bindOwnerRoom, unbindOwnerRoom
} from '../../api'

const buildings = ref([])
const unitOptions = ref([])
const formUnits = ref([])
const owners = ref([])
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const roomOptions = ref([])

const q = reactive({ current: 1, size: 10, buildingId: null, unitId: null, status: '', layout: '', keyword: '' })

const visible = ref(false)
const formRef = ref()
const form = reactive({ id: null, buildingId: null, unitId: null, roomNo: '', floorNo: 1, area: 90, layout: '2室1厅', orientation: '南', status: '自住' })
const rules = {
  buildingId: [{ required: true, message: '请选择楼栋', trigger: 'change' }],
  unitId: [{ required: true, message: '请选择单元', trigger: 'change' }],
  roomNo: [{ required: true, message: '请输入房号', trigger: 'blur' }],
  area: [{ required: true, message: '请输入建筑面积', trigger: 'blur' }]
}

async function load() {
  loading.value = true
  try {
    const d = await roomPage(q)
    rows.value = d.records
    total.value = d.total
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(q, { current: 1, buildingId: null, unitId: null, status: '', layout: '', keyword: '' })
  unitOptions.value = []
  load()
}

async function onBuildingChange(id) {
  q.unitId = null
  unitOptions.value = id ? await unitList({ buildingId: id }) : []
  load()
}

async function onFormBuildingChange(id) {
  form.unitId = null
  formUnits.value = id ? await unitList({ buildingId: id }) : []
}

function openForm(row) {
  if (row) {
    Object.assign(form, row)
    onFormBuildingChange(row.buildingId).then(() => {
      form.unitId = row.unitId
    })
  } else {
    Object.assign(form, { id: null, buildingId: null, unitId: null, roomNo: '', floorNo: 1, area: 90, layout: '2室1厅', orientation: '南', status: '自住' })
    formUnits.value = []
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
    await updateRoom(form.id, form)
    ElMessage.success('修改成功')
  } else {
    await addRoom(form)
    ElMessage.success('新增成功')
  }
  visible.value = false
  load()
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确定删除房屋「${row.buildingName}${row.unitName}${row.roomNo}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await delRoom(row.id)
  ElMessage.success('删除成功')
  load()
}

// ---- 绑定 ----
const bindVisible = ref(false)
const bindRoom = reactive({ roomId: null, roomName: '' })
const bindings = ref([])
const bindForm = reactive({ ownerId: null, relation: '产权人', isPrimary: 0 })

async function loadBindings(roomId) {
  bindings.value = await roomBindings({ roomId })
}

function openBind(row) {
  bindRoom.roomId = row.id
  bindRoom.roomName = `${row.buildingName}${row.unitName}${row.roomNo}`
  bindForm.ownerId = null
  bindForm.relation = '产权人'
  bindForm.isPrimary = 0
  loadBindings(row.id)
  bindVisible.value = true
}

async function doBind() {
  if (!bindForm.ownerId) {
    ElMessage.warning('请选择要绑定的业主')
    return
  }
  await bindOwnerRoom({ roomId: bindRoom.roomId, ...bindForm })
  ElMessage.success('绑定成功')
  loadBindings(bindRoom.roomId)
}

async function unbind(row) {
  try {
    await ElMessageBox.confirm(`确定解除业主「${row.ownerName}」与该房屋的绑定吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await unbindOwnerRoom(row.id, {})
  ElMessage.success('已解除绑定')
  loadBindings(bindRoom.roomId)
}

const lookupVisible = ref(false)
const lookupRoomId = ref(null)

async function showBindings() {
  lookupVisible.value = true
  lookupRoomId.value = null
  bindings.value = []
}

async function loadBindingsById(id) {
  if (!id) return
  loadBindings(id)
}

onMounted(async () => {
  buildings.value = await buildingList()
  owners.value = await ownerList()
  const all = await roomList({})
  roomOptions.value = all.map((r) => ({ id: r.id, fullName: `${r.buildingName}${r.unitName}${r.roomNo}` }))
  load()
})
</script>

<style scoped>
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
