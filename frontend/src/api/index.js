import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '',
  timeout: 60000
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail || err.message || '请求失败'
    ElMessage.error(typeof detail === 'string' ? detail : JSON.stringify(detail))
    return Promise.reject(err)
  }
)

export default api
