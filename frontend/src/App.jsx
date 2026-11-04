import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import { Layout, RequireRole } from './components/common'
import { homeFor } from './labels'
import { AdminAudit, AdminUsers } from './pages/Admin'
import { LoginPage, RegisterPage } from './pages/AuthPages'
import MyDocuments from './pages/MyDocuments'
import { ReviewDashboard, ReviewDetail } from './pages/Review'

function Home() {
  const { user, loading } = useAuth()
  if (loading) return null
  return <Navigate to={user ? homeFor(user.role) : '/login'} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<RequireRole />}>
        <Route element={<Layout />}>
          <Route element={<RequireRole roles={['applicant']} />}>
            <Route path="/documents" element={<MyDocuments />} />
          </Route>
          <Route element={<RequireRole roles={['reviewer', 'admin']} />}>
            <Route path="/review" element={<ReviewDashboard />} />
            <Route path="/review/:id" element={<ReviewDetail />} />
          </Route>
          <Route element={<RequireRole roles={['admin']} />}>
            <Route path="/admin/users" element={<AdminUsers />} />
            <Route path="/admin/audit" element={<AdminAudit />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Home />} />
    </Routes>
  )
}
