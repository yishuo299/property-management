import request from './request'

// ---------- 认证 ----------
export const login = (data) => request.post('/auth/login', data)
export const getInfo = () => request.get('/auth/info')
export const changePassword = (data) => request.post('/auth/password', data)
export const logout = () => request.post('/auth/logout')
export const updateProfile = (data) => request.post('/auth/profile', data)
export const getStaffList = () => request.get('/auth/staff-list')

// ---------- 楼栋 / 单元 / 房屋 ----------
export const buildingList = () => request.get('/building/list')
export const buildingPage = (params) => request.get('/building/page', { params })
export const addBuilding = (data) => request.post('/building', data)
export const updateBuilding = (id, data) => request.post(`/building/${id}`, data)
export const delBuilding = (id) => request.post(`/building/${id}/delete`)

export const unitList = (params) => request.get('/unit/list', { params })
export const unitPage = (params) => request.get('/unit/page', { params })
export const addUnit = (data) => request.post('/unit', data)
export const updateUnit = (id, data) => request.post(`/unit/${id}`, data)
export const delUnit = (id) => request.post(`/unit/${id}/delete`)

export const roomList = (params) => request.get('/room/list', { params })
export const roomPage = (params) => request.get('/room/page', { params })
export const addRoom = (data) => request.post('/room', data)
export const updateRoom = (id, data) => request.post(`/room/${id}`, data)
export const delRoom = (id) => request.post(`/room/${id}/delete`)

// ---------- 业主 ----------
export const ownerList = (params) => request.get('/owner/list', { params })
export const ownerPage = (params) => request.get('/owner/page', { params })
export const ownerDetail = (id) => request.get(`/owner/${id}/detail`)
export const addOwner = (data) => request.post('/owner', data)
export const updateOwner = (id, data) => request.post(`/owner/${id}`, data)
export const delOwner = (id) => request.post(`/owner/${id}/delete`)
export const bindOwnerRoom = (data) => request.post('/owner/bind', data)
export const unbindOwnerRoom = (id, data) => request.post(`/owner/binding/${id}/unbind`, data)
export const transferOwner = (data) => request.post('/owner/transfer', data)
export const roomBindings = (params) => request.get('/owner/room-bindings', { params })

// ---------- 报修工单 ----------
export const repairPage = (params) => request.get('/repair/page', { params })
export const repairMine = (params) => request.get('/repair/mine', { params })
export const repairDetail = (id) => request.get(`/repair/detail/${id}`)
export const addRepair = (data) => request.post('/repair', data)
export const assignRepair = (id, data) => request.post(`/repair/${id}/assign`, data)
export const processRepair = (id, data) => request.post(`/repair/${id}/process`, data)
export const finishRepair = (id, data) => request.post(`/repair/${id}/finish`, data)
export const evaluateRepair = (id, data) => request.post(`/repair/${id}/evaluate`, data)
export const rejectRepair = (id, data) => request.post(`/repair/${id}/reject`, data)
export const cancelRepair = (id, data) => request.post(`/repair/${id}/cancel`, data)

// ---------- 物业费 ----------
export const billPage = (params) => request.get('/bill/page', { params })
export const billMine = (params) => request.get('/bill/mine', { params })
export const billPreview = (params) => request.get('/bill/preview', { params })
export const billGenerate = (data) => request.post('/bill/generate', data)
export const billArrears = () => request.get('/bill/arrears')
export const billDetail = (id) => request.get(`/bill/${id}/detail`)
export const billPay = (id, data) => request.post(`/bill/${id}/pay`, data)
export const billPayments = (id) => request.get(`/bill/${id}/payments`)
export const delBill = (id) => request.post(`/bill/${id}/delete`)

// ---------- 停车位 ----------
export const parkingPage = (params) => request.get('/parking/page', { params })
export const parkingList = () => request.get('/parking/list')
export const parkingMine = () => request.get('/parking/mine')
export const addParking = (data) => request.post('/parking', data)
export const updateParking = (id, data) => request.post(`/parking/${id}`, data)
export const bindParking = (id, data) => request.post(`/parking/${id}/bind`, data)
export const releaseParking = (id) => request.post(`/parking/${id}/release`)
export const delParking = (id) => request.post(`/parking/${id}/delete`)

// ---------- 公告 ----------
export const noticePage = (params) => request.get('/notice/page', { params })
export const noticeList = () => request.get('/notice/list')
export const noticeDetail = (id) => request.get(`/notice/${id}/detail`)
export const readNotice = (id) => request.post(`/notice/${id}/read`)
export const unreadCount = () => request.get('/notice/unread-count')
export const addNotice = (data) => request.post('/notice', data)
export const updateNotice = (id, data) => request.post(`/notice/${id}`, data)
export const delNotice = (id) => request.post(`/notice/${id}/delete`)

// ---------- 访客 ----------
export const visitorPage = (params) => request.get('/visitor/page', { params })
export const addVisitor = (data) => request.post('/visitor', data)
export const updateVisitor = (id, data) => request.post(`/visitor/${id}`, data)
export const checkinVisitor = (id) => request.post(`/visitor/${id}/checkin`)
export const checkoutVisitor = (id) => request.post(`/visitor/${id}/checkout`)
export const cancelVisitor = (id) => request.post(`/visitor/${id}/cancel`)
export const delVisitor = (id) => request.post(`/visitor/${id}/delete`)

// ---------- 统计 ----------
export const statsOverview = () => request.get('/stats/overview')
export const statsMyOverview = () => request.get('/stats/my-overview')
export const statsRepairType = () => request.get('/stats/repair-type')
export const statsRepairTrend = (params) => request.get('/stats/repair-trend', { params })
export const statsRepairEfficiency = () => request.get('/stats/repair-efficiency')
export const statsFeeRate = (params) => request.get('/stats/fee-rate', { params })
export const statsBuildingFee = (params) => request.get('/stats/building-fee', { params })
export const statsStaffWorkload = () => request.get('/stats/staff-workload')
export const statsFeeComposition = () => request.get('/stats/fee-composition')

// ---------- 上传 / 导出 ----------
export const uploadFile = (formData) =>
  request.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })

export function downloadExport(url, filename) {
  return request
    .get(url, { responseType: 'blob' })
    .then((resp) => {
      const blob = new Blob([resp.data])
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(link.href)
    })
}
