import { useState, useEffect } from 'react'
import axios from 'axios'
import { Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const API_BASE = "http://64.227.96.236:8000" // Use your correct IP

function App() {
  const [currentTab, setCurrentTab] = useState("trenchmath")

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
  const [loreJson, setLoreJson] = useState(`{"name":"My Warband","units":["orc","goblin"]}`)

  useEffect(() => {
    getUser()
  }, [])

  useEffect(() => {
    computeAll()
  }, [params])

  async function getUser() {
    try {
      const resp = await axios.get(`${API_BASE}/me`, { withCredentials: true })
      setUser(resp.data)
    } catch (err) {
      setUser(null)
    }
  }

  const handleLogin = () => {
    window.location.href = `${API_BASE}/auth/discord/login`
  }

  async function computeAll() {
    try {
      // Compute success distribution first
      const sdResp = await axios.post(`${API_BASE}/compute_success_distribution`, params)
      setSuccessDistribution(sdResp.data.success_distribution)

      // Once we have success distribution, compute injury outcome
      const hit_distribution = sdResp.data.success_distribution
      const ioReq = {
        hit_distribution,
        injury_params: injuryParams
      }
      const ioResp = await axios.post(`${API_BASE}/compute_injury_outcome`, ioReq)
      setInjuryOutcome(ioResp.data)
    } catch (e) {
      console.error(e)
    }
  }

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

  async function submitWarbandLore() {
    try {
      const loreObj = JSON.parse(loreJson)
      const resp = await axios.post(`${API_BASE}/warband_lore`, loreObj)
      alert(resp.data.message)
    } catch (e) {
      console.error(e)
      alert("Invalid JSON or error in submission.")
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

      {/* Tabs */}
      <div className="bg-white p-2 flex border-b border-gray-300">
        <button
          className={`px-4 py-2 ${currentTab === 'trenchmath' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'}`}
          onClick={() => setCurrentTab('trenchmath')}
        >
          Trenchmath
        </button>
        <button
          className={`px-4 py-2 ${currentTab === 'warband_lore' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'}`}
          onClick={() => setCurrentTab('warband_lore')}
        >
          Warband Lore
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-grow p-4 flex flex-col items-center">
        {currentTab === 'trenchmath' && (
          <div className="w-full max-w-md space-y-6">
            <div className="bg-white p-4 rounded shadow">
              <h2 className="text-xl font-semibold mb-2">Roll Parameters</h2>
              <div className="space-y-2">
                <label className="block">
                  Advantage/Disadvantage (0=2d6, 1=3d6 advantage, -1=3d6 disadvantage):
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
                  Number of Rolls (if multi-shot):
                  <input
                    type="number"
                    value={params.num_rolls}
                    onChange={(e) => setParams({...params, num_rolls: parseInt(e.target.value)})}
                    className="block w-full border-gray-300 rounded mt-1"
                  />
                </label>
              </div>
            </div>

            <div className="bg-white p-4 rounded shadow">
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
                  <span>Injury Extra d6:</span>
                  <input
                    type="checkbox"
                    checked={injuryParams.extra_d6}
                    onChange={(e) => setInjuryParams({...injuryParams, extra_d6: e.target.checked})}
                    className="ml-2"
                  />
                </label>
                <label className="block">
                  Injury Flat Modifier:
                  <input
                    type="number"
                    value={injuryParams.flat_modifier}
                    onChange={(e) => setInjuryParams({...injuryParams, flat_modifier: parseInt(e.target.value)})}
                    className="block w-full border-gray-300 rounded mt-1"
                  />
                </label>
              </div>
              <button onClick={computeAll}
                className="mt-4 w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
                Compute All (Hit & Injury)
              </button>
            </div>

            {successChartData && (
              <div className="bg-white p-4 rounded shadow">
                <h2 className="text-xl font-semibold mb-2">Success Distribution</h2>
                <Bar data={successChartData} />
              </div>
            )}

            {injuryChartData && (
              <div className="bg-white p-4 rounded shadow">
                <h2 className="text-xl font-semibold mb-2">Injury Outcomes</h2>
                <Bar data={injuryChartData} />
              </div>
            )}
          </div>
        )}

        {currentTab === 'warband_lore' && (
          <div className="w-full max-w-md space-y-4 bg-white p-4 rounded shadow">
            <h2 className="text-xl font-semibold mb-2">Warband Lore</h2>
            <p>Enter your Warband data as JSON:</p>
            <textarea
              value={loreJson}
              onChange={(e) => setLoreJson(e.target.value)}
              className="w-full h-48 border-gray-300 rounded"
            ></textarea>
            <button onClick={submitWarbandLore} className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700">
              Save Warband Lore
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
