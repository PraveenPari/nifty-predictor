import { useEffect, useState, useRef } from 'react'
import { io } from 'socket.io-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Activity, TrendingUp, DollarSign } from 'lucide-react'
import { createChart, ColorType, CandlestickSeries, LineSeries } from 'lightweight-charts';
import { apiUrl, SOCKET_URL } from '@/lib/api';

// API host from VITE_API_URL, else same-origin (works locally + hosted)
const socket = io(SOCKET_URL, {
  transports: ['websocket'],
  autoConnect: true
})

interface MarketData {
  ltp: number
  change?: number
  percent_change?: number
}

interface MarketState {
  nifty: MarketData
  banknifty: MarketData
  timestamp: string
}

interface MarketSentiment {
  overall_sentiment: string
  sentiment_score: number
  signals: string[]
  pcr?: { pcr: number; sentiment: string; description: string }
  max_pain?: { max_pain: number; spot: number; distance: number; direction: string; description: string }
  oi_analysis?: { resistance: number; support: number; range: string }
}

interface TradeEstimate {
  option: string
  entry_premium: number
  target_premium: number
  stop_loss_premium: number
  lots: number
  lot_size: number
  capital_required: number
  profit_potential: number
  profit_percentage: number
  max_loss: number
  risk_reward: number
  recommendation: string
}

function App() {
  const [data, setData] = useState<MarketState | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [chartContainer, setChartContainer] = useState<HTMLDivElement | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Pro Trading States
  const [sentiment, setSentiment] = useState<MarketSentiment | null>(null);
  const [tradeEstimate, setTradeEstimate] = useState<TradeEstimate | null>(null);
  const [loading, setLoading] = useState({ sentiment: false, estimate: false });
  const [selectedIndex, setSelectedIndex] = useState<string>('nifty'); // NEW: Track selected index
  const [refreshTrigger, setRefreshTrigger] = useState(0); // NEW: Force refresh ticker

  useEffect(() => {
    try {
      socket.on('connect', () => {
        console.log('Connected to Backend - Socket ID:', socket.id);
        setIsConnected(true)
        socket.emit('subscribe', { index: selectedIndex }) // Subscribe to selected
      })

      socket.on('disconnect', () => {
        console.log('Disconnected from Backend');
        setIsConnected(false)
      })

      socket.on('price_update', (newData: any) => {
        setData(prev => ({
          ...prev,
          nifty: newData.nifty || prev?.nifty,
          banknifty: newData.banknifty || prev?.banknifty,
          timestamp: newData.timestamp
        } as MarketState))
      })

      socket.on('connect_error', (err) => {
        console.error('Socket Connection Error:', err);
      });

    } catch (err) {
      console.error('Initialization error:', err);
      setError(String(err));
    }

    return () => {
      socket.off('connect')
      socket.off('disconnect')
      socket.off('price_update')
      socket.off('connect_error')
    }
  }, [selectedIndex]) // Re-run when index changes

  // Fetch Pro Trading Data: Sentiment & Trade Estimate
  useEffect(() => {
    const fetchProData = async () => {
      setLoading(prev => ({ ...prev, sentiment: true }));
      try {
        console.log(`Refreshing data for ${selectedIndex}...`);
        // Fetch Sentiment
        const sentRes = await fetch(apiUrl(`/api/market-sentiment?index=${selectedIndex}`));
        const sentData = await sentRes.json();
        setSentiment(sentData);

        // Auto-generate estimate when sentiment is fetched
        const currentLtp = selectedIndex === 'nifty' ? data?.nifty?.ltp : data?.banknifty?.ltp;

        if (sentData && sentData.overall_sentiment !== 'NEUTRAL' && currentLtp) {
          const ltp = currentLtp;
          const direction = sentData.overall_sentiment.includes('BULLISH') ? 'BULLISH' : 'BEARISH';
          const targetOffset = direction === 'BULLISH' ? 100 : -100;
          const slOffset = direction === 'BULLISH' ? -50 : 50;

          const estRes = await fetch(apiUrl(`/api/trade-estimate?index=${selectedIndex}&direction=${direction}&entry=${ltp}&target=${ltp + targetOffset}&stop_loss=${ltp + slOffset}&lots=2`));
          const estData = await estRes.json();
          setTradeEstimate(estData);
        }
      } catch (err) {
        console.error("Error fetching pro-trading data:", err);
      } finally {
        setLoading(prev => ({ ...prev, sentiment: false }));
      }
    };

    if (isConnected) {
      fetchProData();
      const interval = setInterval(fetchProData, 60000); // Polling every minute
      return () => clearInterval(interval);
    }
  }, [isConnected, selectedIndex, refreshTrigger, data?.nifty?.ltp, data?.banknifty?.ltp]); // Depend on refreshTrigger

  // Robust Chart Effect
  const chartRef = useRef<any>(null);

  useEffect(() => {
    if (!chartContainer || chartRef.current) return;

    const initChart = async () => {
      try {
        console.log(`Initializing chart for ${selectedIndex}...`);

        // Clear previous chart if it exists
        if (chartRef.current) {
          chartRef.current.remove();
          chartRef.current = null;
        }

        const chart = createChart(chartContainer, {
          layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#DDD' },
          grid: { vertLines: { color: '#333' }, horzLines: { color: '#333' } },
          width: chartContainer.clientWidth,
          height: 300,
        });

        chartRef.current = chart;

        // lightweight-charts v5 uses chart.addSeries(SeriesType, options)
        let series: any = null;
        try {
          // v5 API: use addSeries with CandlestickSeries or LineSeries
          series = chart.addSeries(CandlestickSeries, {
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
          });
          console.log("Created CandlestickSeries successfully");
        } catch (seriesError) {
          console.warn("CandlestickSeries failed, trying LineSeries:", seriesError);
          try {
            series = chart.addSeries(LineSeries, { color: '#26a69a' });
            console.log("Created LineSeries as fallback");
          } catch (lineError) {
            console.error("All series creation failed:", lineError);
          }
        }

        if (series) {
          // Fetch REAL Yahoo Finance data from backend
          try {
            const response = await fetch(apiUrl(`/api/chart-data?index=${selectedIndex}&interval=5m&period=5d`));
            const result = await response.json();

            if (result.candles && result.candles.length > 0) {
              console.log(`Loaded ${result.candles.length} REAL candles for ${selectedIndex}`);
              series.setData(result.candles);
              chart.timeScale().fitContent();
            } else {
              console.warn("No candles received from API, chart will be empty");
            }
          } catch (fetchErr) {
            console.error("Failed to fetch chart data:", fetchErr);
          }
        } else {
          console.error("Failed to create any series on chart object:", chart);
        }

        const handleResize = () => {
          if (chartContainer && chartRef.current) {
            chartRef.current.applyOptions({ width: chartContainer.clientWidth });
          }
        };
        window.addEventListener('resize', handleResize);

        return () => {
          window.removeEventListener('resize', handleResize);
          if (chartRef.current) {
            chartRef.current.remove();
            chartRef.current = null;
          }
        };
      } catch (err) {
        console.error('Chart creation error:', err);
      }
    };

    initChart();
  }, [chartContainer, selectedIndex, refreshTrigger]); // Re-init chart when selectedIndex or refreshTrigger changes

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black text-red-500">
        <p>Fatal Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="border-b border-border p-4 flex justify-between items-center bg-card">
        <div className="flex items-center gap-2">
          <Activity className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-green-400 text-transparent bg-clip-text">
            Stock ML Analyzer Pro
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <Badge variant={isConnected ? "success" : "destructive"}>
            {isConnected ? "Connected" : "Disconnected"}
          </Badge>
          <Button variant="outline" size="sm">Settings</Button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 border-r border-border bg-card/50 hidden md:block p-4 space-y-4">
          <Button variant="secondary" className="w-full justify-start">📊 Dashboard</Button>
          <Button variant="ghost" className="w-full justify-start">⭐ Watchlist</Button>
          <Button variant="ghost" className="w-full justify-start">📈 Active Trades</Button>
          <Button variant="ghost" className="w-full justify-start">💡 Recommendations</Button>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6 space-y-6 overflow-auto">

          {/* Market Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card
              className={`cursor-pointer transition-all hover:bg-card/80 ${selectedIndex === 'nifty' ? 'border-primary ring-2 ring-primary/20' : ''}`}
              onClick={() => { setSelectedIndex('nifty'); setRefreshTrigger(prev => prev + 1); }}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">NIFTY 50</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data?.nifty?.ltp?.toFixed(2) || "Loading..."}
                </div>
                <p className="text-xs text-muted-foreground">+0.45% Today</p>
              </CardContent>
            </Card>
            <Card
              className={`cursor-pointer transition-all hover:bg-card/80 ${selectedIndex === 'banknifty' ? 'border-primary ring-2 ring-primary/20' : ''}`}
              onClick={() => { setSelectedIndex('banknifty'); setRefreshTrigger(prev => prev + 1); }}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">BANK NIFTY</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data?.banknifty?.ltp?.toFixed(2) || "Loading..."}
                </div>
                <p className="text-xs text-muted-foreground">+0.12% Today</p>
              </CardContent>
            </Card>
            <Card className="bg-primary/5 border-primary/20">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">PCR (Ratio)</CardTitle>
                <Activity className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${sentiment?.pcr?.sentiment?.includes('BULLISH') ? 'text-green-500' : 'text-red-500'}`}>
                  {sentiment?.pcr?.pcr || "---"}
                </div>
                <p className="text-xs text-muted-foreground">{sentiment?.pcr?.sentiment || "Fetching..."}</p>
              </CardContent>
            </Card>
            <Card className="bg-primary/5 border-primary/20">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Max Pain</CardTitle>
                <TrendingUp className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {sentiment?.max_pain?.max_pain || "---"}
                </div>
                <p className="text-xs text-muted-foreground">Dist: {sentiment?.max_pain?.distance || 0}</p>
              </CardContent>
            </Card>
          </div>

          {/* Market Intelligence */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2 border-primary/20 bg-gradient-to-br from-card to-primary/5">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Activity className="h-5 w-5 text-primary" />
                  AI Market Sentiment Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col md:flex-row gap-6">
                  <div className="flex-1 space-y-4">
                    <div className="flex items-center gap-4">
                      <div className={`text-3xl font-black px-4 py-2 rounded-lg border-2 ${sentiment?.overall_sentiment?.includes('BULLISH') ? 'bg-green-500/10 border-green-500/50 text-green-500' :
                        sentiment?.overall_sentiment?.includes('BEARISH') ? 'bg-red-500/10 border-red-500/50 text-red-500' :
                          'bg-blue-500/10 border-blue-500/50 text-blue-500'
                        }`}>
                        {sentiment?.overall_sentiment || "ANALYZING..."}
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Sentiment Score</div>
                        <div className="text-xl font-bold">{sentiment?.sentiment_score || 0}%</div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm font-medium">Leading Signals:</div>
                      <div className="flex flex-wrap gap-2">
                        {sentiment?.signals.map((s, i) => (
                          <Badge key={i} variant="outline" className="bg-primary/5 border-primary/20">
                            {s}
                          </Badge>
                        )) || <span className="text-muted-foreground text-xs italic">Awaiting NSE data buildup...</span>}
                      </div>
                    </div>
                  </div>
                  <div className="w-full md:w-64 space-y-3 p-4 bg-black/20 rounded-xl border border-border">
                    <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Trading Strategy</div>
                    <div className="text-sm font-medium">{sentiment?.pcr?.description || "Calculating intraday Greek exposure..."}</div>
                    <div className="pt-2 border-t border-border/50 text-xs italic text-primary/70">
                      🎯 Strike Magnet: {sentiment?.max_pain?.max_pain}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-green-500/30 bg-green-500/5">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2 text-green-500">
                  <DollarSign className="h-5 w-5" />
                  Profit Estimator
                </CardTitle>
              </CardHeader>
              <CardContent>
                {tradeEstimate ? (
                  <div className="space-y-4">
                    <div className="p-3 bg-black/40 rounded-lg border border-green-500/20">
                      <div className="text-xs text-muted-foreground uppercase">Expected Profit</div>
                      <div className="text-3xl font-black text-green-500">₹{tradeEstimate.profit_potential.toLocaleString()}</div>
                      <div className="text-xs font-bold text-green-400">+{tradeEstimate.profit_percentage}% Return</div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Entry Premium</span>
                        <span className="font-bold">₹{tradeEstimate.entry_premium}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Target / SL</span>
                        <span className="font-bold">₹{tradeEstimate.target_premium} / ₹{tradeEstimate.stop_loss_premium}</span>
                      </div>
                      <div className="flex justify-between pt-2 border-t border-border">
                        <span className="text-muted-foreground">Capital Required</span>
                        <span className="font-bold">₹{tradeEstimate.capital_required.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-32 flex items-center justify-center text-muted-foreground text-sm italic">
                    Waiting for high-confidence signal...
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Charts & Signals */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2 overflow-hidden shadow-xl border-primary/20 bg-black/60 backdrop-blur">
              <CardHeader className="border-b border-border/50">
                <CardTitle className="text-lg flex items-center gap-2">
                  Live Candlesticks <Badge className="bg-primary/20 text-primary border-primary/30">Nifty</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div ref={setChartContainer} className="w-full h-[400px]" />
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card className="bg-gradient-to-br from-card to-card/50 border-primary/10 shadow-lg relative overflow-hidden">
                <div className={`absolute top-0 right-0 w-32 h-32 opacity-10 blur-3xl rounded-full ${sentiment?.overall_sentiment?.includes('BULLISH') ? 'bg-green-500' : 'bg-red-500'}`} />
                <CardHeader>
                  <CardTitle className="text-sm font-bold text-primary flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    ML PRO RECOMMENDATION
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {tradeEstimate ? (
                    <>
                      <div className="flex justify-between items-center">
                        <span className="text-xl font-black">{tradeEstimate.option}</span>
                        <Badge className={`${tradeEstimate.recommendation?.includes('BUY') ? 'bg-green-500' : 'bg-red-500'} text-white`}>
                          {tradeEstimate.recommendation?.includes('BUY') ? 'BUY' : 'SELL'}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="p-2 bg-black/30 rounded border border-border">
                          <div className="text-xs text-muted-foreground">Entry @</div>
                          <div className="font-bold">₹{tradeEstimate.entry_premium}</div>
                        </div>
                        <div className="p-2 bg-green-500/10 rounded border border-green-500/20">
                          <div className="text-xs text-green-500">Target @</div>
                          <div className="font-bold text-green-500">₹{tradeEstimate.target_premium}</div>
                        </div>
                        <div className="p-2 bg-red-500/10 rounded border border-red-500/20">
                          <div className="text-xs text-red-500">Stop Loss @</div>
                          <div className="font-bold text-red-500">₹{tradeEstimate.stop_loss_premium}</div>
                        </div>
                        <div className="p-2 bg-black/30 rounded border border-border">
                          <div className="text-xs text-muted-foreground">Lots x Units</div>
                          <div className="font-bold">{tradeEstimate.lots} x {tradeEstimate.lot_size}</div>
                        </div>
                      </div>
                      <div className="p-3 bg-primary/10 rounded-lg text-xs font-medium border border-primary/20 text-center uppercase tracking-widest text-primary">
                        Predicted Movement: {sentiment?.overall_sentiment}
                      </div>
                    </>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-10 text-muted-foreground space-y-2">
                      <Activity className="h-10 w-10 animate-pulse text-muted-foreground/30" />
                      <p className="text-sm italic">Scanning NSE data flow...</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Key Support & Resistance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-red-400">Resistance</span>
                      <span className="font-mono font-bold">{sentiment?.oi_analysis?.resistance || "---"}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500"
                        style={{ width: '100%' }}
                      />
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-green-400">Support</span>
                      <span className="font-mono font-bold">{sentiment?.oi_analysis?.support || "---"}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

        </main>
      </div>
    </div>
  )
}

export default App
