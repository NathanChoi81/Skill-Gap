import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const isDev = user?.role === 'dev'

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex gap-6">
          <Link to="/dashboard" className="text-gray-700 hover:text-gray-900 font-medium">Dashboard</Link>
          <Link to="/roles" className="text-gray-700 hover:text-gray-900 font-medium">Roles</Link>
          <Link to="/resume-skills" className="text-gray-700 hover:text-gray-900 font-medium">Resume & Skills</Link>
          <Link to="/jobs" className="text-gray-700 hover:text-gray-900 font-medium">Jobs</Link>
          <Link to="/skills" className="text-gray-700 hover:text-gray-900 font-medium">Skills</Link>
          <Link to="/plan" className="text-gray-700 hover:text-gray-900 font-medium">Plan</Link>
          <Link to="/settings" className="text-gray-700 hover:text-gray-900 font-medium">Settings</Link>
          {isDev && (
            <>
              <Link to="/dev/jobs" className="text-amber-600 hover:text-amber-700 font-medium">Dev Jobs</Link>
              <Link to="/dev/courses" className="text-amber-600 hover:text-amber-700 font-medium">Dev Courses</Link>
              <Link to="/dev/skills" className="text-amber-600 hover:text-amber-700 font-medium">Dev Skills</Link>
            </>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">{user?.email}</span>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Logout
          </button>
        </div>
      </nav>
      <main className="max-w-5xl mx-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
