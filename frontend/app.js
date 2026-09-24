const API_BASE=window.API_BASE||"https://YOUR-RENDER-SERVICE.onrender.com";
const $=id=>document.getElementById(id);
const map=L.map("map").setView([22.5726,88.3639],12);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"© OpenStreetMap"}).addTo(map);
let marker=L.marker([22.5726,88.3639]).addTo(map);
async function get(url,options){const r=await fetch(API_BASE+url,options);if(!r.ok)throw Error(await r.text());return r.json()}
async function refresh(){
 try{
  const lat=+$("lat").value,lon=+$("lon").value;
  const live=await get("/api/live?lat="+lat+"&lon="+lon);
  if(live.current_speed!=null)$("inputSpeed").value=Math.round(live.current_speed);
  if(live.free_flow_speed!=null)$("freeFlow").value=Math.round(live.free_flow_speed);
  const p=await get("/api/predict",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({latitude:lat,longitude:lon,speed:+$("inputSpeed").value,free_flow_speed:+$("freeFlow").value,weather:+$("weather").value})});
  $("level").textContent=p.congestion_level;
  $("speed").textContent=(live.current_speed??$("inputSpeed").value)+" km/h";
  $("predicted").textContent=p.predicted_speed+" km/h";
  $("confidence").textContent=Math.round(p.probability*100)+"%";
  marker.setLatLng([lat,lon]);map.setView([lat,lon],12);
  $("status").textContent="Live traffic + ML prediction updated.";
 }catch(e){$("status").textContent="Error: "+e.message}
}
$("refresh").onclick=refresh;
$("predict").onclick=refresh;