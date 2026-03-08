import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './lib/auth'
import AuthLayout from './layouts/AuthLayout'
import AppLayout from './layouts/AppLayout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Roles from './pages/Roles'
import ResumeSkills from './pages/ResumeSkills'
import Jobs from './pages/Jobs'
import Skills from './pages/Skills'
import Plan from './pages/Plan'
import Settings from './pages/Settings'
import DevJobs from './pages/dev/DevJobs'
import DevCourses from './pages/dev/DevCourses'
import DevSkills from './pages/dev/DevSkills'
import SkillDetail from './pages/SkillDetail'
import JobDetail from './pages/JobDetail'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-8">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/roles" element={<Roles />} />
        <Route path="/resume-skills" element={<ResumeSkills />} />
        <Route path="/jobs" element={<Jobs />} />
        <Route path="/jobs/:jobId" element={<JobDetail />} />
        <Route path="/skills" element={<Skills />} />
        <Route path="/skills/:skillId" element={<SkillDetail />} />
        <Route path="/plan" element={<Plan />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/dev/jobs" element={<DevJobs />} />
        <Route path="/dev/courses" element={<DevCourses />} />
        <Route path="/dev/skills" element={<DevSkills />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
