<template>
  <div>
    <PageHeader title="我的车位" desc="查看本人名下绑定的停车位信息与车位费" />

    <div v-if="!spots.length" class="empty-tip">您当前没有绑定任何车位，如需租用车位请联系物业服务中心</div>
    <el-row :gutter="16">
      <el-col v-for="s in spots" :key="s.id" :span="8">
        <div class="spot-card">
          <div class="spot-head">
            <div class="spot-no">{{ s.spotNo }}</div>
            <el-tag size="small" effect="light" :type="{ 地上: 'success', 地下: 'primary', 固定: 'warning', 临时: 'info' }[s.spotType]">{{ s.spotType }}车位</el-tag>
          </div>
          <div class="spot-row"><span class="k">所在区域</span><span>{{ s.area || '-' }}</span></div>
          <div class="spot-row"><span class="k">绑定房屋</span><span>{{ s.roomName || '-' }}</span></div>
          <div class="spot-row"><span class="k">车位费</span><span class="fee">{{ s.fee }} 元 / 月</span></div>
          <div class="spot-row"><span class="k">租用期限</span><span>{{ s.startDate || '-' }} ~ {{ s.endDate || '长期' }}</span></div>
          <div class="spot-row"><span class="k">状态</span>
            <el-tag size="small" :type="s.status === '已租' ? 'success' : 'info'" effect="light">{{ s.status }}</el-tag>
          </div>
          <div v-if="s.remark" class="spot-remark">{{ s.remark }}</div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import { parkingMine } from '../../api'

const spots = ref([])

onMounted(async () => {
  spots.value = await parkingMine()
})
</script>

<style scoped>
.spot-card {
  background: #fff;
  border: 1px solid var(--pm-border);
  border-radius: var(--pm-radius);
  padding: 18px;
  box-shadow: var(--pm-shadow);
  margin-bottom: 16px;
  transition: all 0.2s;
}

.spot-card:hover {
  box-shadow: var(--pm-shadow-hover);
  transform: translateY(-2px);
}

.spot-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.spot-no {
  font-size: 22px;
  font-weight: 700;
  color: #ea580c;
  letter-spacing: 1px;
}

.spot-row {
  display: flex;
  justify-content: space-between;
  font-size: 13.5px;
  padding: 6px 0;
  border-bottom: 1px dashed #f5ece0;
}

.spot-row .k {
  color: var(--pm-text-sub);
}

.spot-row .fee {
  color: #65a30d;
  font-weight: 600;
}

.spot-remark {
  margin-top: 10px;
  font-size: 12.5px;
  color: var(--pm-text-sub);
}
</style>
