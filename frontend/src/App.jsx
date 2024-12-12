import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = "http://64.227.96.236:8000" // Adjust if needed

function App() {
  const [text, setText] = useState('')
  const [message, setMessage] = useState(null)
  const [user, setUser] = useState(null)

  useEffect(() => {
    // Check if user is logged in
    axios.get(`${API_BASE}/me`, { withCredentials: true })
      .then(resp => {
        setUser(resp.data)
      })
      .catch(err => {
        setUser(null)
      })
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage(null)
    try {
      await axios.post(`${API_BASE}/submit`, { text }, { withCredentials: true })
        .then(response => {
          setMessage(response.data.message)
          setText('')
        })
    } catch (err) {
      console.error(err)
      setMessage("Error storing text.")
    }
  }

  const handleLogin = () => {
    window.location.href = `${API_BASE}/auth/discord/login`
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 bg-gray-100">
      <div className="bg-white shadow-lg rounded-lg p-6 w-full max-w-md">
        {!user ? (
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Welcome</h1>
            <button
              onClick={handleLogin}
              className="w-full bg-purple-600 text-white rounded-md py-2 font-semibold hover:bg-purple-700 transition-colors"
            >
              Login with Discord
            </button>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-bold mb-4 text-center">Welcome, {user.username}</h1>
            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="text"
                className="block w-full border-gray-300 rounded-md"
                placeholder="Enter something..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                required
              />
              <button
                type="submit"
                className="w-full bg-blue-600 text-white rounded-md py-2 font-semibold hover:bg-blue-700 transition-colors"
              >
                Submit
              </button>
            </form>
            {message && (
              <div className="mt-4 text-green-600 text-center">
                {message}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default App

