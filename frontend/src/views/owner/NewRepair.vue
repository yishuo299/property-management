<template>
  <div>
    <PageHeader title="在线报修" desc="选择报修房屋与问题类型，上传现场照片，一键提交给物业" />

    <div class="form-wrap page-card">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="报修房屋" prop="roomId">
          <el-select v-model="form.roomId" placeholder="请选择要报修的房屋" style="width: 100%">
            <el-option v-for="r in rooms" :key="r.roomId" :label="`${r.roomName}（${r.isPrimary ? '主产权' : r.relation}）`" :value="r.roomId" />
          </el-select>
          <div v-if="!rooms.length" class="tip-warn">当前账号名下暂无房屋，请联系物业服务中心登记产权信息。</div>
        </el-form-item>

        <el-form-item label="报修类型" prop="repairType">
          <el-radio-group v-model="form.repairType">
            <el-radio-button v-for="t in types" :key="t.value" :label="t.value">
              <el-icon><component :is="t.icon" /></el-icon>
              <span style="margin-left: 4px">{{ t.value }}</span>
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="紧急程度" prop="urgency">
          <el-radio-group v-model="form.urgency">
            <el-radio-button label="一般" />
            <el-radio-button label="紧急" />
            <el-radio-button label="非常紧急" />
          </el-radio-group>
        </el-form-item>

        <el-form-item label="报修标题" prop="title">
          <el-input v-model="form.title" placeholder="一句话描述问题，如：厨房水管漏水" maxlength="100" show-word-limit />
        </el-form-item>

        <el-form-item label="问题描述" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="5"
            placeholder="请尽量详细描述问题出现的位置、现象和持续时间，方便维修师傅提前准备工具和材料" maxlength="500" show-word-limit />
        </el-form-item>

        <el-form-item label="现场照片">
          <el-upload
            :action="uploadUrl" :headers="uploadHeaders" name="file" list-type="picture-card"
            :on-success="onUploaded" :on-error="onError" :before-upload="beforeUpload" accept="image/*">
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="tip-sub">支持 jpg / png / gif / webp 格式，单张不超过 5MB，最多上传 3 张</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" :loading="submitting" @click="submit">
            <el-icon><Promotion /></el-icon>提交报修
          </el-button>
          <el-button size="large" @click="$router.push('/my-repairs')">查看我的报修</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="page-card" style="margin-top: 16px">
      <div class="chart-title">报修小提示</div>
      <ul class="tips">
        <li>提交后物业服务中心会在 <b>24 小时内</b>受理并指派维修师傅，超时将自动标记为「超时」。</li>
        <li>属于业主户内自用设施的损坏（如自购家电、私装管道）可能不在物业免费维修范围内，物业会说明原因。</li>
        <li>维修完成后请在本系统「我的报修」中确认完成并给出评价，您的评价将帮助物业改进服务。</li>
        <li>如遇燃气泄漏、水管爆裂等紧急情况，请先关闭总阀并拨打物业热线 010-8888 6666。</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import PageHeader from '../../components/PageHeader.vue'
import { getInfo, ownerDetail, addRepair } from '../../api'
import { useUserStore } from '../../store/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const submitting = ref(false)
const rooms = ref([])

const types = [
  { value: '水电', icon: 'Lightning' },
  { value: '门窗', icon: 'House' },
  { value: '家电', icon: 'Refrigerator' },
  { value: '公共设施', icon: 'OfficeBuilding' },
  { value: '其他', icon: 'MoreFilled' }
]

const form = reactive({ roomId: null, repairType: '水电', urgency: '一般', title: '', content: '', images: [] })

const rules = {
  roomId: [{ required: true, message: '请选择报修房屋', trigger: 'change' }],
  repairType: [{ required: true, message: '请选择报修类型', trigger: 'change' }],
  urgency: [{ required: true, message: '请选择紧急程度', trigger: 'change' }],
  title: [{ required: true, message: '请填写报修标题', trigger: 'blur' }],
  content: [
    { required: true, message: '请描述具体问题', trigger: 'blur' },
    { min: 5, message: '问题描述至少 5 个字', trigger: 'blur' }
  ]
}

const uploadUrl = '/api/upload'
const uploadHeaders = computed(() => ({ Authorization: 'Bearer ' + localStorage.getItem('token') }))

function beforeUpload(file) {
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

function onUploaded(res) {
  if (res.code === 200) {
    if (form.images.length >= 3) {
      ElMessage.warning('最多上传 3 张照片')
      return
    }
    form.images.push(res.data.url)
    ElMessage.success('照片上传成功')
  } else {
    ElMessage.error(res.msg || '上传失败')
  }
}

function onError() {
  ElMessage.error('照片上传失败')
}

async function submit() {
  try {
    await formRef.value.validate()
  } catch (e) {
    return
  }
  submitting.value = true
  try {
    const d = await addRepair({ ...form, images: form.images })
    ElMessage.success(`报修提交成功，工单号 ${d.orderNo}`)
    router.push('/my-repairs')
  } catch (e) {
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  const info = await getInfo()
  if (info.ownerId) {
    const d = await ownerDetail(info.ownerId)
    rooms.value = (d.bindings || []).filter((b) => b.status === '有效')
    const primary = rooms.value.find((r) => r.isPrimary)
    if (primary) form.roomId = primary.roomId
    else if (rooms.value.length) form.roomId = rooms.value[0].roomId
  }
})
</script>

<style scoped>
.form-wrap {
  max-width: 760px;
}

.tip-warn {
  color: #e11d48;
  font-size: 12.5px;
  margin-top: 6px;
}

.tip-sub {
  color: var(--pm-text-sub);
  font-size: 12.5px;
  margin-top: 6px;
  width: 100%;
}

.tips {
  margin: 0;
  padding-left: 20px;
  line-height: 2;
  color: #57534e;
  font-size: 13.5px;
}

.tips b {
  color: #ea580c;
}
</style>
