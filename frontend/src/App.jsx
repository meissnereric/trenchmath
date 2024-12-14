import { useState, useEffect } from 'react'
import axios from 'axios'
import { Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const API_BASE = "http://64.227.96.236:8000" // Adjust as needed

function App() {
  const [params, setParams] = useState({
    modified_dice: 0,
    extra_d6: false,
    flat_modifier: 0,
    threshold: 7,
    num_rolls: 1
  })
  const [injuryParams, setInjuryParams] = useState({
    modified_dice: -1,
    extra_d6: true,
    flat_modifier: -3
  })

  const [successDistribution, setSuccessDistribution] = useState(null)
  const [injuryOutcome, setInjuryOutcome] = useState(null)
  const [user, setUser] = useState(null)

  // Check if user is logged in
  useEffect(() => {
    getUser()
  }, [])

  async function getUser() {
    try {
      const resp = await axios.get(`${API_BASE}/me`, { withCredentials: true })
      setUser(resp.data)
    } catch (err) {
      // User not logged in or no valid token
      setUser(null)
    }
  }

  // Fetch success distribution whenever parameters change
  useEffect(() => {
    fetchSuccessDistribution()
  }, [params])

  async function fetchSuccessDistribution() {
    try {
      const resp = await axios.post(`${API_BASE}/compute_success_distribution`, params)
      setSuccessDistribution(resp.data.success_distribution)
    } catch (e) {
      console.error(e)
    }
  }

  async function fetchInjuryOutcome() {
    if (!successDistribution) return
    const hit_distribution = successDistribution // {hits: probability}
    const data = {
      hit_distribution,
      injury_params: injuryParams
    }
    try {
      const resp = await axios.post(`${API_BASE}/compute_injury_outcome`, data)
      setInjuryOutcome(resp.data)
    } catch(e) {
      console.error(e)
    }
  }

  const handleLogin = () => {
    window.location.href = `${API_BASE}/auth/discord/login`
  }

  // Prepare data for success distribution chart
  let successChartData = null
  if (successDistribution) {
    const hits = Object.keys(successDistribution).map(k => Number(k))
    const probs = hits.map(h => successDistribution[h])
    successChartData = {
      labels: hits.map(h => `Hits: ${h}`),
      datasets: [
        {
          label: 'Probability',
          data: probs,
          backgroundColor: 'rgba(54, 162, 235, 0.5)'
        }
      ]
    }
  }

  // Prepare data for injury outcome chart
  let injuryChartData = null
  if (injuryOutcome) {
    const markers = injuryOutcome.blood_marker_distribution.markers
    const probs = injuryOutcome.blood_marker_distribution.probabilities
    const outActionProb = injuryOutcome.out_of_action_probability

    const labels = markers.map(m => `Blood Markers: ${m}`).concat(["Out of Action"])
    const values = probs.concat([outActionProb])

    injuryChartData = {
      labels: labels,
      datasets: [
        {
          label: 'Probability',
          data: values,
          backgroundColor: labels.map((l,i) => i === labels.length-1 ? 'rgba(255,99,132,0.5)' : 'rgba(75,192,192,0.5)')
        }
      ]
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      {/* Top Navigation Bar */}
      <header className="w-full bg-white shadow p-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Trench Crusade</h1>
        <div>
          {user ? (
            <span className="text-sm text-gray-700">Logged in as {user.username}</span>
          ) : (
            <button
              onClick={handleLogin}
              className="bg-purple-600 text-white py-1 px-3 rounded hover:bg-purple-700 text-sm"
            >
              Login with Discord
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-grow p-4 flex flex-col items-center">
        <div className="bg-white p-4 rounded shadow max-w-md w-full mb-6">
          <h2 className="text-xl font-semibold mb-2">Roll Parameters</h2>
          <div className="space-y-2">
            <label className="block">
              Advantage / Disadvantage (0 = 2d6, -1 = 3d6 Disadvantage, 1 = 3d6 advantage, etc.):
              <input
                type="number"
                value={params.modified_dice}
                onChange={(e) => setParams({...params, modified_dice: parseInt(e.target.value)})}
                className="block w-full border-gray-300 rounded mt-1"
              />
            </label>
            <label className="block">
              Flat Modifier to roll:
              <input
                type="number"
                value={params.flat_modifier}
                onChange={(e) => setParams({...params, flat_modifier: parseInt(e.target.value)})}
                className="block w-full border-gray-300 rounded mt-1"
              />
            </label>
            <label className="block">
              Number of Rolls (if multi-shot for instance):
              <input
                type="number"
                value={params.num_rolls}
                onChange={(e) => setParams({...params, num_rolls: parseInt(e.target.value)})}
                className="block w-full border-gray-300 rounded mt-1"
              />
            </label>
          </div>
        </div>

        {successChartData && (
          <div className="bg-white p-4 rounded shadow max-w-md w-full mb-6">
            <h2 className="text-xl font-semibold mb-2">Success Distribution</h2>
            <Bar data={successChartData} />
          </div>
        )}

        <div className="bg-white p-4 rounded shadow max-w-md w-full mb-6">
          <h2 className="text-xl font-semibold mb-2">Injury Parameters</h2>
          <div className="space-y-2">
            <label className="block">
              Injury Adv/Disadv:
              <input
                type="number"
                value={injuryParams.modified_dice}
                onChange={(e) => setInjuryParams({...injuryParams, modified_dice: parseInt(e.target.value)})}
                className="block w-full border-gray-300 rounded mt-1"
              />
            </label>
            <label className="block flex items-center">
              <span>Injury Extra d6 (Bloodbath, Artillery Witch, etc):</span>
              <input
                type="checkbox"
                checked={injuryParams.extra_d6}
                onChange={(e) => setInjuryParams({...injuryParams, extra_d6: e.target.checked})}
                className="ml-2"
              />
            </label>
            <label className="block">
              Injury Flat Modifier (i.e. Standard Armor = -1, Reinforced = -2, etc. ):
              <input
                type="number"
                value={injuryParams.flat_modifier}
                onChange={(e) => setInjuryParams({...injuryParams, flat_modifier: parseInt(e.target.value)})}
                className="block w-full border-gray-300 rounded mt-1"
              />
            </label>
          </div>
          <button onClick={fetchInjuryOutcome}
            className="mt-4 w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
            Compute Injury Outcomes
          </button>
        </div>

        {injuryChartData && (
          <div className="bg-white p-4 rounded shadow max-w-md w-full">
            <h2 className="text-xl font-semibold mb-2">Injury Outcomes</h2>
            <Bar data={injuryChartData} />
          </div>
        )}
      </div>
    </div>
  )
}

export default App

