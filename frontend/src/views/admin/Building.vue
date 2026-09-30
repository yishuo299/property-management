<template>
  <div>
    <PageHeader title="楼栋单元管理" desc="维护小区「楼栋 → 单元 → 房号」三级结构" />

    <el-tabs v-model="tab" class="page-card">
      <!-- 楼栋 -->
      <el-tab-pane label="楼栋管理" name="building">
        <div class="toolbar">
          <el-input v-model="bq.keyword" placeholder="搜索楼栋名称/编号" clearable style="width: 220px" @keyup.enter="loadBuilding" />
          <el-select v-model="bq.buildingType" placeholder="楼栋类型" clearable style="width: 140px">
            <el-option label="住宅" value="住宅" />
            <el-option label="公寓" value="公寓" />
          </el-select>
          <el-button type="primary" @click="loadBuilding"><el-icon><Search /></el-icon>查询</el-button>
          <el-button @click="resetBuilding">重置</el-button>
          <div class="spacer"></div>
          <el-button type="success" @click="openBuilding()"><el-icon><Plus /></el-icon>新增楼栋</el-button>
          <el-button type="warning" plain @click="doExport"><el-icon><Download /></el-icon>导出业主</el-button>
        </div>
        <el-table :data="buildings" v-loading="bloading" border stripe>
          <el-table-column prop="buildingCode" label="楼栋编号" width="110" />
          <el-table-column prop="buildingName" label="楼栋名称" width="120" />
          <el-table-column prop="buildingType" label="类型" width="90" />
          <el-table-column prop="unitCount" label="单元数" width="90" />
          <el-table-column prop="floorCount" label="层数" width="80" />
          <el-table-column prop="buildYear" label="建成年份" width="100" />
          <el-table-column prop="address" label="坐落位置" min-width="180" />
          <el-table-column prop="remark" label="备注" min-width="140" />
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openBuilding(row)">编辑</el-button>
              <el-button link type="danger" @click="removeBuilding(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          class="pager" background layout="total, prev, pager, next, sizes"
          :total="bTotal" v-model:current-page="bq.current" v-model:page-size="bq.size"
          :page-sizes="[10, 20, 50]" @change="loadBuilding" />
      </el-tab-pane>

      <!-- 单元 -->
      <el-tab-pane label="单元管理" name="unit">
        <div class="toolbar">
          <el-select v-model="uq.buildingId" placeholder="选择楼栋" clearable style="width: 180px" @change="loadUnit">
            <el-option v-for="b in allBuildings" :key="b.id" :label="b.buildingName" :value="b.id" />
          </el-select>
          <el-input v-model="uq.keyword" placeholder="搜索单元" clearable style="width: 180px" @keyup.enter="loadUnit" />
          <el-button type="primary" @click="loadUnit"><el-icon><Search /></el-icon>查询</el-button>
          <div class="spacer"></div>
          <el-button type="success" @click="openUnit()"><el-icon><Plus /></el-icon>新增单元</el-button>
        </div>
        <el-table :data="units" v-loading="uloading" border stripe>
          <el-table-column prop="unitNo" label="单元编号" width="150" />
          <el-table-column prop="buildingName" label="所属楼栋" width="130" />
          <el-table-column prop="unitName" label="单元名称" width="120" />
          <el-table-column prop="floorCount" label="层数" width="90" />
          <el-table-column label="电梯" width="100">
            <template #default="{ row }">
              <el-tag :type="row.hasElevator ? 'success' : 'info'" size="small" effect="light">
                {{ row.hasElevator ? '有电梯' : '无电梯' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="160" />
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openUnit(row)">编辑</el-button>
              <el-button link type="danger" @click="removeUnit(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          class="pager" background layout="total, prev, pager, next, sizes"
          :total="uTotal" v-model:current-page="uq.current" v-model:page-size="uq.size"
          :page-sizes="[10, 20, 50]" @change="loadUnit" />
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="bVisible" :title="bForm.id ? '编辑楼栋' : '新增楼栋'" width="520px">
      <el-form :model="bForm" :rules="bRules" ref="bFormRef" label-width="90px">
        <el-form-item label="楼栋编号" prop="buildingCode">
          <el-input v-model="bForm.buildingCode" :disabled="!!bForm.id" placeholder="如 B16" />
        </el-form-item>
        <el-form-item label="楼栋名称" prop="buildingName">
          <el-input v-model="bForm.buildingName" placeholder="如 16号楼" />
        </el-form-item>
        <el-form-item label="楼栋类型">
          <el-select v-model="bForm.buildingType" style="width: 100%">
            <el-option label="住宅" value="住宅" />
            <el-option label="公寓" value="公寓" />
          </el-select>
        </el-form-item>
        <el-form-item label="单元数">
          <el-input-number v-model="bForm.unitCount" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="总层数">
          <el-input-number v-model="bForm.floorCount" :min="1" :max="60" />
        </el-form-item>
        <el-form-item label="建成年份">
          <el-input-number v-model="bForm.buildYear" :min="1980" :max="2030" />
        </el-form-item>
        <el-form-item label="坐落位置">
          <el-input v-model="bForm.address" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="bForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bVisible = false">取消</el-button>
        <el-button type="primary" @click="saveBuilding">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="uVisible" :title="uForm.id ? '编辑单元' : '新增单元'" width="480px">
      <el-form :model="uForm" :rules="uRules" ref="uFormRef" label-width="90px">
        <el-form-item label="所属楼栋" prop="buildingId">
          <el-select v-model="uForm.buildingId" :disabled="!!uForm.id" style="width: 100%">
            <el-option v-for="b in allBuildings" :key="b.id" :label="b.buildingName" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="单元名称" prop="unitName">
          <el-input v-model="uForm.unitName" placeholder="如 3单元" />
        </el-form-item>
        <el-form-item label="层数">
          <el-input-number v-model="uForm.floorCount" :min="1" :max="60" />
        </el-form-item>
        <el-form-item label="是否有电梯">
          <el-switch v-model="uForm.hasElevator" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="uForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUnit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import {
  buildingList, buildingPage, addBuilding, updateBuilding, delBuilding,
  unitPage, addUnit, updateUnit, delUnit, downloadExport
} from '../../api'

const tab = ref('building')
const allBuildings = ref([])

// ---- 楼栋 ----
const buildings = ref([])
const bTotal = ref(0)
const bloading = ref(false)
const bq = reactive({ current: 1, size: 10, keyword: '', buildingType: '' })
const bVisible = ref(false)
const bFormRef = ref()
const bForm = reactive({ id: null, buildingCode: '', buildingName: '', buildingType: '住宅', unitCount: 2, floorCount: 6, buildYear: 2015, address: '', remark: '' })
const bRules = {
  buildingCode: [{ required: true, message: '请输入楼栋编号', trigger: 'blur' }],
  buildingName: [{ required: true, message: '请输入楼栋名称', trigger: 'blur' }]
}

async function loadBuilding() {
  bloading.value = true
  try {
    const d = await buildingPage(bq)
    buildings.value = d.records
    bTotal.value = d.total
  } finally {
    bloading.value = false
  }
}

function resetBuilding() {
  bq.keyword = ''
  bq.buildingType = ''
  bq.current = 1
  loadBuilding()
}

function openBuilding(row) {
  if (row) {
    Object.assign(bForm, row)
  } else {
    Object.assign(bForm, { id: null, buildingCode: '', buildingName: '', buildingType: '住宅', unitCount: 2, floorCount: 6, buildYear: 2015, address: '', remark: '' })
  }
  bVisible.value = true
}

async function saveBuilding() {
  try {
    await bFormRef.value.validate()
  } catch (e) {
    return
  }
  if (bForm.id) {
    await updateBuilding(bForm.id, bForm)
    ElMessage.success('修改成功')
  } else {
    await addBuilding(bForm)
    ElMessage.success('新增成功')
  }
  bVisible.value = false
  loadBuilding()
  loadAllBuildings()
}

async function removeBuilding(row) {
  try {
    await ElMessageBox.confirm(`确定删除楼栋「${row.buildingName}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await delBuilding(row.id)
  ElMessage.success('删除成功')
  loadBuilding()
  loadAllBuildings()
}

// ---- 单元 ----
const units = ref([])
const uTotal = ref(0)
const uloading = ref(false)
const uq = reactive({ current: 1, size: 10, keyword: '', buildingId: null })
const uVisible = ref(false)
const uFormRef = ref()
const uForm = reactive({ id: null, buildingId: null, unitName: '', floorCount: 6, hasElevator: 1, remark: '' })
const uRules = {
  buildingId: [{ required: true, message: '请选择所属楼栋', trigger: 'change' }],
  unitName: [{ required: true, message: '请输入单元名称', trigger: 'blur' }]
}

async function loadUnit() {
  uloading.value = true
  try {
    const d = await unitPage(uq)
    units.value = d.records
    uTotal.value = d.total
  } finally {
    uloading.value = false
  }
}

function openUnit(row) {
  if (row) {
    Object.assign(uForm, { id: row.id, buildingId: row.buildingId, unitName: row.unitName, floorCount: row.floorCount, hasElevator: row.hasElevator, remark: row.remark })
  } else {
    Object.assign(uForm, { id: null, buildingId: uq.buildingId || null, unitName: '', floorCount: 6, hasElevator: 1, remark: '' })
  }
  uVisible.value = true
}

async function saveUnit() {
  try {
    await uFormRef.value.validate()
  } catch (e) {
    return
  }
  if (uForm.id) {
    await updateUnit(uForm.id, uForm)
    ElMessage.success('修改成功')
  } else {
    await addUnit(uForm)
    ElMessage.success('新增成功')
  }
  uVisible.value = false
  loadUnit()
}

async function removeUnit(row) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.buildingName}${row.unitName}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await delUnit(row.id)
  ElMessage.success('删除成功')
  loadUnit()
}

async function loadAllBuildings() {
  allBuildings.value = await buildingList()
}

function doExport() {
  downloadExport('/export/owners', '业主信息.xlsx')
  ElMessage.success('正在导出业主信息...')
}

onMounted(() => {
  loadBuilding()
  loadUnit()
  loadAllBuildings()
})
</script>

<style scoped>
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
