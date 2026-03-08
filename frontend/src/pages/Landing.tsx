import { Link } from 'react-router-dom'

const FEATURES = [
  { title: 'Resume Upload', description: 'Upload your resume and extract skills with optional AI.' },
  { title: 'Skill Gap Analysis', description: 'See how you compare to your target role.' },
  { title: 'Job Matches', description: 'Get ranked job postings and missing-skills previews.' },
  { title: 'Learning Resources', description: 'Courses and resources per skill with progress.' },
  { title: 'Career Tracking', description: 'Deadline-driven learning plan and progress.' },
]

export default function Landing() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-slate-50 to-white px-4">
      <div className="w-full max-w-2xl text-center">
        {/* Centered logo */}
        <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight mb-2">SkillGap</h1>
        <p className="text-xl text-gray-700 mb-10">
          You're one skill away from your dream job, what's stopping you?
        </p>

        {/* Feature tiles */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-10 text-left">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow"
            >
              <h3 className="font-semibold text-gray-900">{f.title}</h3>
              <p className="text-sm text-gray-600 mt-1">{f.description}</p>
            </div>
          ))}
        </div>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/register"
            className="inline-flex justify-center bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 font-medium"
          >
            Register
          </Link>
          <Link
            to="/login"
            className="inline-flex justify-center border border-gray-300 text-gray-800 py-3 px-6 rounded-lg hover:bg-gray-50 font-medium"
          >
            Login
          </Link>
        </div>
      </div>
    </div>
  )
}
