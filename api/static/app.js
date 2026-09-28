const $=id=>document.getElementById(id);
$("analyse").onclick=async()=>{const symbol=$("symbol").value.trim().toUpperCase(),timeframe=$("timeframe").value;$("result").textContent="Loading...";try{const r=await fetch("/analysis/"+encodeURIComponent(symbol)+"?timeframe="+timeframe);$("result").textContent=JSON.stringify(await r.json(),null,2)}catch(e){$("result").textContent=String(e)}};
if("serviceWorker"in navigator)navigator.serviceWorker.register("/static/sw.js").catch(()=>{});
