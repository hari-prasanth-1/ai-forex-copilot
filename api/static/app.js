const $ = id => document.getElementById(id);
const state = { charts: [], chartElements: new Map(), data: null, syncing: false, resizeObserver: null, loading: false, lastUpdated: null };
const POLL_INTERVAL_MS = 10000;
const fmt = (value, digits=5) => value == null || !Number.isFinite(Number(value)) ? "—" : Number(value).toFixed(digits);
const pretty = value => value == null ? "—" : Number(value).toLocaleString(undefined,{maximumFractionDigits:2});
function setTone(el, value) { el.classList.remove("positive","negative","neutral"); el.classList.add(value==="BUY"||value==="BUY BIAS"||value==="BULLISH" ? "positive" : value==="SELL"||value==="SELL BIAS"||value==="BEARISH" ? "negative" : "neutral"); }
function createChart(id,height){const el=$(id);const chart=LightweightCharts.createChart(el,{width:el.clientWidth,height,layout:{background:{type:"solid",color:"#0e1726"},textColor:"#91a1b8",fontFamily:"Inter,system-ui,sans-serif",fontSize:11},grid:{vertLines:{color:"#1b2a3d"},horzLines:{color:"#1b2a3d"}},rightPriceScale:{borderColor:"#27364c"},timeScale:{borderColor:"#27364c",timeVisible:true,secondsVisible:false},crosshair:{vertLine:{color:"#61748f"},horzLine:{color:"#61748f"}}});state.charts.push(chart);state.chartElements.set(chart,el);return chart}
function syncCharts(){for(const chart of state.charts){chart.timeScale().subscribeVisibleLogicalRangeChange(range=>{if(!range||state.syncing)return;state.syncing=true;for(const other of state.charts){if(other!==chart){try{other.timeScale().setVisibleLogicalRange(range)}catch{}}}state.syncing=false})}}
function addLine(chart,color,title){return chart.addLineSeries({color,lineWidth:2,title,priceLineVisible:false,lastValueVisible:true})}
function addHorizontal(chart,price,color,title){return chart.addLineSeries({color,lineWidth:1,lineStyle:LightweightCharts.LineStyle.Dashed,title,priceLineVisible:false,lastValueVisible:false}).setData([])}
function render(payload){
  if(!window.LightweightCharts)throw new Error("Chart library did not load. Check internet access and reload.");
  state.charts.forEach(c=>c.remove());state.charts=[];state.chartElements.clear();state.data=payload;
  const candles=payload.candles||[];if(!candles.length)throw new Error("MT5 returned no candles.");
  const price=createChart("price-chart",document.getElementById("price-chart").clientHeight||370);
  const candleSeries=price.addCandlestickSeries({upColor:"#2dd4a7",downColor:"#ff687d",borderUpColor:"#2dd4a7",borderDownColor:"#ff687d",wickUpColor:"#2dd4a7",wickDownColor:"#ff687d",priceLineVisible:true});
  candleSeries.setData(candles.map(c=>({time:c.time,open:c.open,high:c.high,low:c.low,close:c.close})));
  addLine(price,"#67a9ff","EMA 20").setData(candles.filter(c=>c.ema20!=null).map(c=>({time:c.time,value:c.ema20})));
  addLine(price,"#f4c45f","EMA 50").setData(candles.filter(c=>c.ema50!=null).map(c=>({time:c.time,value:c.ema50})));
  addLine(price,"#bba1ff","EMA 200").setData(candles.filter(c=>c.ema200!=null).map(c=>({time:c.time,value:c.ema200})));
  const markers=candles.filter(c=>c.signal).map(c=>({time:c.time,position:c.signal==="BUY"?"belowBar":"aboveBar",color:c.signal==="BUY"?"#2dd4a7":"#ff687d",shape:c.signal==="BUY"?"arrowUp":"arrowDown",text:c.signal}));
  if(markers.length)candleSeries.setMarkers(markers);
  const volume=createChart("volume-chart",document.getElementById("volume-chart").clientHeight||125);
  const volumeSeries=volume.addHistogramSeries({priceFormat:{type:"volume"},priceScaleId:"volume",lastValueVisible:false,priceLineVisible:false});
  volume.priceScale("volume").applyOptions({scaleMargins:{top:.08,bottom:.02},borderVisible:false});
  volumeSeries.setData(candles.map(c=>({time:c.time,value:c.volume,color:c.close>=c.open?"#2dd4a777":"#ff687d77"})));
  const rsiChart=createChart("rsi-chart",document.getElementById("rsi-chart").clientHeight||145);
  const rsiSeries=addLine(rsiChart,"#bba1ff","RSI 14");rsiSeries.setData(candles.filter(c=>c.rsi14!=null).map(c=>({time:c.time,value:c.rsi14})));
  for(const level of [30,50,70]){const s=rsiChart.addLineSeries({color:level===50?"#53647c":"#35445b",lineStyle:LightweightCharts.LineStyle.Dashed,lineWidth:1,priceLineVisible:false,lastValueVisible:false});s.setData(candles.map(c=>({time:c.time,value:level})))}
  rsiChart.priceScale("right").applyOptions({autoScale:false,scaleMargins:{top:.08,bottom:.08}});rsiChart.timeScale().applyOptions({visible:false});
  const macdChart=createChart("macd-chart",document.getElementById("macd-chart").clientHeight||145);
  const macdHist=macdChart.addHistogramSeries({priceLineVisible:false,lastValueVisible:false});macdHist.setData(candles.filter(c=>c.macd_histogram!=null).map(c=>({time:c.time,value:c.macd_histogram,color:c.macd_histogram>=0?"#2dd4a777":"#ff687d77"})));
  addLine(macdChart,"#67a9ff","MACD").setData(candles.filter(c=>c.macd!=null).map(c=>({time:c.time,value:c.macd})));
  addLine(macdChart,"#f4c45f","Signal").setData(candles.filter(c=>c.macd_signal!=null).map(c=>({time:c.time,value:c.macd_signal})));
  macdChart.timeScale().applyOptions({visible:false});
  syncCharts();for(const chart of state.charts)chart.timeScale().fitContent();
  const latest=payload.latest||{},trend=payload.trend||"UNKNOWN";
  $("price").textContent=fmt(latest.close);$("market-label").textContent=payload.symbol+" · "+payload.timeframe;
  $("trend").textContent=trend;setTone($("trend"),trend);$("structure").textContent="Structure: "+(payload.structure_event||"—");
  const currentSignal = getCurrentSignal(latest);
  $("decision").textContent=currentSignal.label;
  setTone($("decision"),currentSignal.label);
  $("decision").title=currentSignal.reason;
  $("rsi-value").textContent=fmt(latest.rsi14,2);$("macd-value").textContent=fmt(latest.macd_histogram,6);
  $("atr-value").textContent=fmt(latest.atr14,5);$("volume-value").textContent=pretty(latest.volume);
  const alignment=latest.ema20==null||latest.ema50==null?"INSUFFICIENT DATA":latest.ema20>latest.ema50?"BULLISH":latest.ema20<latest.ema50?"BEARISH":"MIXED";
  $("ema-state").textContent=alignment;setTone($("ema-state"),alignment);
  $("candle-count").textContent=pretty(candles.length);$("data-source").textContent="Source: "+payload.source;
  $("signal-count").textContent=markers.length+" historical signals";$("chart-note").textContent="Signals are historical confluence markers, not guaranteed entries.";
  const list=[
    ["Trend",trend+" · "+(payload.structure_event||"No event")],
    ["EMA alignment",alignment+" (20 / 50 / 200)"],
    ["RSI (14)",latest.rsi14==null?"Not enough data":fmt(latest.rsi14,2)+(latest.rsi14>70?" · overbought zone":latest.rsi14<30?" · oversold zone":latest.rsi14>=50?" · bullish momentum bias":" · bearish momentum bias")],
    ["MACD",latest.macd_histogram==null?"Not enough data":Number(latest.macd_histogram)>=0?"Histogram positive":"Histogram negative"],
    ["ATR (14)",latest.atr14==null?"Not enough data":fmt(latest.atr14,5)+" · current volatility"],
    ["Volume",pretty(latest.volume)+" tick volume on latest candle"],
    ["Swing high / low",fmt(payload.swing_high)+" / "+fmt(payload.swing_low)],
    ["Execution","OFF · this dashboard cannot place orders"]
  ];
  $("analysis-list").innerHTML=list.map(([title,detail])=>'<div class="analysis-item"><b>'+escapeHtml(title)+'</b><span>'+escapeHtml(detail)+'</span></div>').join("");
  state.lastUpdated = new Date();
  $("connection").textContent = "LIVE · updated " + state.lastUpdated.toLocaleTimeString();
  $("chart-note").textContent = "Auto-refresh every 10 seconds · " + currentSignal.reason;
  $("error").hidden=true;
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]))}
async function loadChart(){if(state.loading)return;const symbol=$("symbol").value.trim().toUpperCase(),timeframe=$("timeframe").value,limit=$("limit").value;if(!/^[A-Z0-9.]{3,12}$/.test(symbol)){showError("Enter a valid broker symbol.");return}const btn=$("analyse");state.loading=true;btn.disabled=true;$("refresh").disabled=true;if(!state.data)$("connection").textContent="Connecting to MT5…";$("error").hidden=true;try{const response=await fetch("/mt5/chart/"+encodeURIComponent(symbol)+"?timeframe="+timeframe+"&limit="+limit,{headers:{Accept:"application/json"},cache:"no-store"});const payload=await response.json();if(!response.ok)throw new Error(payload.detail||"Request failed with HTTP "+response.status);render(payload)}catch(error){showError(error.message||String(error));$("connection").textContent="Connection failed · retrying automatically"}finally{state.loading=false;btn.disabled=false;$("refresh").disabled=false}}
function getCurrentSignal(latest){
  const e20=Number(latest.ema20), e50=Number(latest.ema50), close=Number(latest.close);
  const rsi=Number(latest.rsi14), histogram=Number(latest.macd_histogram);
  if(![e20,e50,close,rsi,histogram].every(Number.isFinite))
    return {label:"WAIT",reason:"Waiting for enough valid indicator data."};
  if(e20>e50 && close>e20 && rsi>=50 && rsi<70 && histogram>0)
    return {label:"BUY BIAS",reason:"Bullish confluence: EMA20 above EMA50, price above EMA20, RSI 50–70 and MACD histogram positive."};
  if(e20<e50 && close<e20 && rsi<=50 && rsi>30 && histogram<0)
    return {label:"SELL BIAS",reason:"Bearish confluence: EMA20 below EMA50, price below EMA20, RSI 30–50 and MACD histogram negative."};
  return {label:"WAIT",reason:"No complete directional confluence right now; this is analysis only, not an entry instruction."};
}
function showError(message){$("error").textContent=message;$("error").hidden=false}
function scheduleRefresh(){window.setTimeout(async()=>{await loadChart();scheduleRefresh()},POLL_INTERVAL_MS)}
$("analyse").addEventListener("click",loadChart);$("refresh").addEventListener("click",loadChart);document.querySelectorAll(".watch-symbol").forEach(button=>button.addEventListener("click",()=>{document.querySelectorAll(".watch-symbol").forEach(item=>item.classList.toggle("active",item===button));$("symbol").value=button.dataset.symbol;loadChart()}));$("timeframe").addEventListener("change",()=>{if(state.data)loadChart()});
if("ResizeObserver"in window){state.resizeObserver=new ResizeObserver(entries=>{for(const entry of entries){for(const chart of state.charts){if(state.chartElements.get(chart)===entry.target)chart.applyOptions({width:entry.target.clientWidth})}}});for(const id of ["price-chart","volume-chart","rsi-chart","macd-chart"])state.resizeObserver.observe($(id))}
if("serviceWorker"in navigator)navigator.serviceWorker.register("/static/sw.js").catch(()=>{});
loadChart().finally(scheduleRefresh);
