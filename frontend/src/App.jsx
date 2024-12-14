import { useState, useEffect } from 'react'
import axios from 'axios'
import { Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const API_BASE = "http://64.227.96.236:8000" // Use your correct IP or domain

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

  // Warband Lore State
  const [warbandText, setWarbandText] = useState(` Slimy Boys | The Cult of the Black Grail 
[ DUCATS ] Total : 0 | Spent : 500 (15 Lost) | Available : -500
[ GLORY ] Total : 0 | Spent : 0 (0 Lost)    | Available : 0
[ ELITE MEMBERS ]
 Ser Theodosia of the Black | Plague Knight | 155 ducats 0 glory ---
[ EQUIPMENT ]
-Putrid Shotgun (20 ducats)
-Plague Blade (15 ducats)
-Reinforced Armour (40 ducats)
-Black Grail Shield (20 ducats)

 Corpse Guard | Corpse Guard | 55 ducats 0 glory ---

 Lord of Tumours | Lord of Tumours | 130 ducats 0 glory ---

[ INFANTRY ]
 Sweety Girl | Hound of the Black Grail | 60 ducats 0 glory ---
[ UPGRADES ]
-Hound Infection (5 ducats)

 Herald of Beelzebub | Herald of Beelzebub | 50 ducats 0 glory ---

 Herald of Beelzebub | Herald of Beelzebub | 50 ducats 0 glory ---

 Hound of the Black Grail | Hound of the Black Grail | 55 ducats 0 glory ---


[ EXPLORATION MODIFIERS ]
  Reroll`)
  const [themeInfo, setThemeInfo] = useState("")
  const [loreOptions, setLoreOptions] = useState(null)
  const [selectedLoreIndex, setSelectedLoreIndex] = useState(null)

  useEffect(() => {
    getUser()
  }, [])

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

  async function generateWarbandLore() {
    setLoreOptions(null)
    setSelectedLoreIndex(null)
    try {
      const resp = await axios.post(`${API_BASE}/warband_lore/generate`, {
        warband_text: warbandText,
        theme_info: themeInfo || null
      })
      if (resp.data.error) {
        alert("Error: " + resp.data.error)
      } else {
        setLoreOptions(resp.data.options)
      }
    } catch (e) {
      console.error(e)
      alert("Failed to generate lore. Check console for error.")
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

      <div className="flex-grow p-4 flex flex-col items-center overflow-auto">
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
          <div className="w-full max-w-md space-y-6">
            <div className="bg-white p-4 rounded shadow">
              <h2 className="text-xl font-semibold mb-2">Generate Warband Lore</h2>
              <label className="block mb-2">
                <span className="block font-semibold">Warband Text:</span>
                <textarea
                  value={warbandText}
                  onChange={(e) => setWarbandText(e.target.value)}
                  className="w-full h-40 border border-gray-300 rounded mt-1 p-2"
                ></textarea>
              </label>
              <label className="block mb-2">
                <span className="block font-semibold">Theme Info (Optional):</span>
                <textarea
                  value={themeInfo}
                  onChange={(e) => setThemeInfo(e.target.value)}
                  className="w-full h-20 border border-gray-300 rounded mt-1 p-2"
                  placeholder="Enter theme info or leave blank"
                ></textarea>
              </label>
              <button
                onClick={generateWarbandLore}
                className="bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 w-full"
              >
                Generate Lore
              </button>
            </div>

            {loreOptions && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Select One of the Lore Options:</h3>
                {loreOptions.map((opt, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded shadow bg-white border-2 ${selectedLoreIndex === idx ? 'border-blue-600' : 'border-transparent'}`}
                  >
                    <h4 className="text-md font-semibold mb-2">Option {idx+1}</h4>
                    <p><strong>Member Names:</strong> {opt.member_names.join(', ')}</p>
                    <p><strong>Warband Description:</strong> {opt.warband_description}</p>
                    <p><strong>Warband Goal:</strong> {opt.warband_goal}</p>
                    <p><strong>Micro-Story:</strong> {opt.micro_story}</p>
                    <button
                      onClick={() => setSelectedLoreIndex(idx)}
                      className="mt-2 bg-blue-600 text-white py-1 px-2 rounded hover:bg-blue-700"
                    >
                      Select This Option
                    </button>
                  </div>
                ))}
              </div>
            )}

            {selectedLoreIndex !== null && (
              <div className="bg-white p-4 rounded shadow">
                <h3 className="font-semibold mb-2">Selected Lore:</h3>
                <p>You've selected Option {selectedLoreIndex+1}.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
