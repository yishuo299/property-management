<template>
  <div>
    <PageHeader title="业主管理" desc="维护业主档案与房屋绑定关系，支持一户多业主与房屋过户" />

    <div class="page-card">
      <div class="toolbar">
        <el-input v-model="q.keyword" placeholder="姓名 / 电话 / 身份证号" clearable style="width: 240px" @keyup.enter="load" />
        <el-select v-model="q.ownerType" placeholder="业主类型" clearable style="width: 140px">
          <el-option v-for="t in ['业主', '家属', '租户']" :key="t" :label="t" :value="t" />
        </el-select>
        <el-button type="primary" @click="load"><el-icon><Search /></el-icon>查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="warning" @click="transferVisible = true"><el-icon><Switch /></el-icon>房屋过户</el-button>
        <el-button type="success" @click="openForm()"><el-icon><Plus /></el-icon>新增业主</el-button>
        <el-button plain @click="doExport"><el-icon><Download /></el-icon>导出 Excel</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="70" />
        <el-table-column prop="phone" label="联系电话" width="130" />
        <el-table-column prop="idCard" label="身份证号" width="180" />
        <el-table-column prop="ownerType" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small" effect="light" :type="row.ownerType === '业主' ? 'warning' : 'info'">{{ row.ownerType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="名下房屋" min-width="230">
          <template #default="{ row }">
            <span v-if="!row.roomCount" style="color: #a8a29e">暂无</span>
            <el-tag v-for="(rn, i) in row.roomNames" :key="i" size="small" effect="plain" style="margin: 2px 4px 2px 0">{{ rn }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="登录账号" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.userId" type="success" size="small" effect="light">已开通</el-tag>
            <span v-else style="color: #a8a29e">未开通</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
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

    <!-- 新增/编辑 -->
    <el-dialog v-model="visible" :title="form.id ? '编辑业主' : '新增业主'" width="540px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入业主姓名" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio-button label="男" />
            <el-radio-button label="女" />
          </el-radio-group>
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" maxlength="11" placeholder="11 位手机号" />
        </el-form-item>
        <el-form-item label="身份证号">
          <el-input v-model="form.idCard" maxlength="18" placeholder="18 位身份证号（选填）" />
        </el-form-item>
        <el-form-item label="业主类型">
          <el-select v-model="form.ownerType" style="width: 100%">
            <el-option v-for="t in ['业主', '家属', '租户']" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <template v-if="!form.id">
          <el-divider content-position="left">开通线上账号（可选）</el-divider>
          <el-form-item label="登录账号">
            <el-input v-model="form.username" placeholder="留空则不创建登录账号" />
          </el-form-item>
          <el-form-item label="初始密码">
            <el-input v-model="form.password" placeholder="默认 123456" />
          </el-form-item>
        </template>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情 -->
    <el-dialog v-model="detailVisible" title="业主详情" width="640px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="姓名">{{ detail.name }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ detail.gender }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ detail.phone }}</el-descriptions-item>
        <el-descriptions-item label="业主类型">{{ detail.ownerType }}</el-descriptions-item>
        <el-descriptions-item label="身份证号" :span="2">{{ detail.idCard || '-' }}</el-descriptions-item>
      </el-descriptions>
      <el-divider content-position="left">房屋绑定记录（含过户历史）</el-divider>
      <el-table :data="detail.bindings || []" size="small" border>
        <el-table-column prop="roomName" label="房屋" min-width="160" />
        <el-table-column prop="relation" label="关系" width="90" />
        <el-table-column label="主产权人" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.isPrimary" type="warning" size="small" effect="dark">是</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="startDate" label="起始" width="105" />
        <el-table-column prop="endDate" label="结束" width="105" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '有效' ? 'success' : 'info'" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 过户 -->
    <el-dialog v-model="transferVisible" title="房屋过户" width="520px">
      <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 14px"
        title="过户后原产权人的绑定关系将标记为「已过户」，新产权人成为主产权人。" />
      <el-form :model="transferForm" :rules="transferRules" ref="transferFormRef" label-width="100px">
        <el-form-item label="房屋" prop="roomId">
          <el-select v-model="transferForm.roomId" filterable placeholder="搜索房屋" style="width: 100%">
            <el-option v-for="r in roomOptions" :key="r.id" :label="r.fullName" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="新业主" prop="newOwnerId">
          <el-select v-model="transferForm.newOwnerId" filterable placeholder="选择新业主" style="width: 100%">
            <el-option v-for="o in ownerOptions" :key="o.id" :label="`${o.name}（${o.phone}）`" :value="o.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="过户日期">
          <el-date-picker v-model="transferForm.transferDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="transferVisible = false">取消</el-button>
        <el-button type="warning" @click="doTransfer">确认过户</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import {
  ownerPage, ownerList, ownerDetail, addOwner, updateOwner, delOwner,
  roomList, transferOwner, downloadExport
} from '../../api'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = reactive({ current: 1, size: 10, keyword: '', ownerType: '' })
const roomOptions = ref([])
const ownerOptions = ref([])

const visible = ref(false)
const formRef = ref()
const form = reactive({ id: null, name: '', gender: '男', phone: '', idCard: '', ownerType: '业主', username: '', password: '', remark: '' })
const rules = {
  name: [{ required: true, message: '请输入业主姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^\d{11}$/, message: '请输入 11 位手机号', trigger: 'blur' }
  ]
}

async function load() {
  loading.value = true
  try {
    const d = await ownerPage(q)
    rows.value = d.records
    total.value = d.total
  } finally {
    loading.value = false
  }
}

function reset() {
  q.keyword = ''
  q.ownerType = ''
  q.current = 1
  load()
}

function openForm(row) {
  if (row) {
    Object.assign(form, { id: row.id, name: row.name, gender: row.gender, phone: row.phone, idCard: row.idCard, ownerType: row.ownerType, username: '', password: '', remark: row.remark })
  } else {
    Object.assign(form, { id: null, name: '', gender: '男', phone: '', idCard: '', ownerType: '业主', username: '', password: '', remark: '' })
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
    await updateOwner(form.id, form)
    ElMessage.success('修改成功')
  } else {
    await addOwner(form)
    ElMessage.success('新增成功')
  }
  visible.value = false
  load()
  loadOptions()
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确定删除业主「${row.name}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await delOwner(row.id)
  ElMessage.success('删除成功')
  load()
  loadOptions()
}

const detailVisible = ref(false)
const detail = reactive({})

async function openDetail(row) {
  const d = await ownerDetail(row.id)
  Object.assign(detail, d)
  detailVisible.value = true
}

const transferVisible = ref(false)
const transferFormRef = ref()
const transferForm = reactive({ roomId: null, newOwnerId: null, transferDate: '' })
const transferRules = {
  roomId: [{ required: true, message: '请选择房屋', trigger: 'change' }],
  newOwnerId: [{ required: true, message: '请选择新业主', trigger: 'change' }]
}

async function doTransfer() {
  try {
    await transferFormRef.value.validate()
  } catch (e) {
    return
  }
  const res = await transferOwner(transferForm)
  ElMessage.success(res?.id ? '过户成功' : '过户完成')
  transferVisible.value = false
  transferForm.roomId = null
  transferForm.newOwnerId = null
  transferForm.transferDate = ''
  load()
}

async function loadOptions() {
  ownerOptions.value = await ownerList()
}

function doExport() {
  downloadExport('/export/owners', '业主信息.xlsx')
  ElMessage.success('正在导出业主信息...')
}

onMounted(async () => {
  const rooms = await roomList({})
  roomOptions.value = rooms.map((r) => ({ id: r.id, fullName: `${r.buildingName}${r.unitName}${r.roomNo}` }))
  await loadOptions()
  load()
})
</script>

<style scoped>
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
