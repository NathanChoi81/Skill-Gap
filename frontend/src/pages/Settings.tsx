import { useAuth } from '../lib/auth'

export default function Settings() {
  const { user } = useAuth()
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Settings</h1>
      <div className="bg-white border rounded-lg p-6 max-w-md">
        <p className="text-sm text-gray-500">Email</p>
        <p className="font-medium">{user?.email}</p>
        <p className="mt-4 text-sm text-gray-500">Password change and preferences can be added here.</p>
      </div>
    </div>
  )
}
