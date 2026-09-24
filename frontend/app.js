const API_BASE=window.API_BASE||"";
const $=id=>document.getElementById(id);
const map=L.map("map").setView([22.57,88.36],11);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"© OpenStreetMap contributors"}).addTo(map);
const routeLayer=L.layerGroup().addTo(map),markers=L.layerGroup().addTo(map);
let lastData=null;
const levelColors={"Free Flow":"#12b76a","Moderate":"#f79009","Heavy":"#f04438","Severe":"#b42318"};

async function get(url){
  const response=await fetch(API_BASE+url,{cache:"no-store"});
  if(!response.ok){
    let message="Request failed";
    try{const body=await response.json();message=body.detail||message}catch{}
    throw new Error(message);
  }
  return response.json();
}
function setBusy(busy){
  $("predict").disabled=busy;$("refresh").disabled=busy;
  $("predict").innerHTML=busy?"Checking live traffic…":"Check traffic <span>→</span>";
}
function setLevel(level){
  $("level").textContent=level||"—";
  $("levelHint").textContent=level==="Free Flow"?"Road is moving freely":level==="Moderate"?"Moderate traffic":level==="Heavy"?"Heavy traffic":level==="Severe"?"Severe congestion":"Choose a route";
  $("level").style.color=levelColors[level]||"";
}
function drawRoute(points,origin,destination,level){
  routeLayer.clearLayers();markers.clearLayers();
  const latlngs=points.map(p=>[p.lat,p.lon]);
  if(latlngs.length<2)return;
  const color=levelColors[level]||"#2563eb";
  L.polyline(latlngs,{color,weight:7,opacity:.85}).addTo(routeLayer);
  L.circleMarker(latlngs[0],{radius:8,color:"#fff",weight:3,fillColor:"#12b76a",fillOpacity:1}).bindTooltip("FROM: "+origin).addTo(markers);
  L.circleMarker(latlngs[latlngs.length-1],{radius:8,color:"#fff",weight:3,fillColor:"#f04438",fillOpacity:1}).bindTooltip("TO: "+destination).addTo(markers);
  map.fitBounds(L.latLngBounds(latlngs),{padding:[30,30]});
}
function renderWeather(w){
  $("weatherText").textContent="Weather: "+(w.description||"—");
  $("weatherDetails").textContent=(w.temperature??"—")+"°C • clouds "+(w.clouds??"—")+"% • visibility "+((w.visibility||0)/1000).toFixed(1)+" km";
  $("feelsLike").textContent=(w.feels_like??"—")+"°C";
  $("humidity").textContent=(w.humidity??"—")+"%";
  $("rain").textContent=(w.rain_1h??0)+" mm";
  $("wind").textContent=(w.wind_speed??"—")+" m/s";
  if(w.icon)$("weatherIcon").innerHTML='<img alt="" src="https://openweathermap.org/img/wn/'+w.icon+'@2x.png">';
}
function localKey(o,d){return "trafficpulse:"+o+":"+d}
function saveLocal(o,d,data){
  const key=localKey(o,d);
  const items=JSON.parse(localStorage.getItem(key)||"[]");
  items.push({timestamp:data.updated_at,current_speed:data.current_speed,congestion_level:data.congestion_level,traffic_delay_min:data.traffic_delay_min});
  localStorage.setItem(key,JSON.stringify(items.slice(-24)));
}
function renderTimeline(data,serverHistory){
  const key=localKey($("origin").value,$("destination").value);
  const local=JSON.parse(localStorage.getItem(key)||"[]");
  const all=[...(serverHistory||[]),...local].sort((a,b)=>new Date(a.timestamp)-new Date(b.timestamp));
  const past=all.filter((x,i,a)=>i===a.findIndex(y=>y.timestamp===x.timestamp)&&new Date(x.timestamp)<new Date(data.updated_at)).slice(-4)
    .map(x=>({label:"-"+Math.max(1,Math.round((new Date(data.updated_at)-new Date(x.timestamp))/60000))+"m",speed:x.current_speed,level:x.congestion_level,delay:x.traffic_delay_min}));
  const future=(data.forecast||[]).map(x=>({label:"+"+x.minutes_ahead+"m",speed:x.predicted_speed,level:x.congestion_level,delay:null}));
  const items=[...past,{label:"NOW",speed:data.current_speed,level:data.congestion_level,delay:data.traffic_delay_min},...future];
  $("timeline").innerHTML=items.map(x=>'<div class="time-card '+(x.label==="NOW"?"now":x.label.startsWith("+")?"future":"past")+'"><span>'+x.label+'</span><strong>'+x.speed+' km/h</strong><b style="color:'+(levelColors[x.level]||"")+'">'+x.level+'</b><small>'+(x.delay!=null?"Delay "+x.delay+" min":"Forecast")+'</small></div>').join("");
  $("timelineNote").textContent=past.length+" previous check(s)";
}
function renderAlert(data){
  const severe=(data.forecast||[]).find(x=>x.congestion_level==="Severe");
  const heavy=(data.forecast||[]).find(x=>x.congestion_level==="Heavy");
  $("alertBox").textContent=severe?"Severe congestion may occur in "+severe.minutes_ahead+" minutes.":heavy?"Heavy congestion may occur in "+heavy.minutes_ahead+" minutes.":"No heavy or severe congestion is predicted in the next hour.";
}
async function loadLocations(){
  const data=await get("/api/locations");
  const origin=$("origin"),destination=$("destination");
  (data.locations||[]).forEach(name=>{origin.add(new Option(name,name));destination.add(new Option(name,name))});
  if(origin.options.length>1){origin.value=origin.options[0].value;destination.value=origin.options[1].value}
}
async function predict(){
  setBusy(true);
  $("status").textContent="Getting live traffic and weather…";
  try{
    const origin=$("origin").value,destination=$("destination").value;
    if(!origin||!destination||origin===destination)throw new Error("Please choose two different locations.");
    const data=await get("/api/route-predict?origin="+encodeURIComponent(origin)+"&destination="+encodeURIComponent(destination));
    lastData=data;
    setLevel(data.congestion_level);
    $("speed").textContent=data.current_speed+" km/h";
    const next=data.forecast&&data.forecast[0];
    $("predicted").textContent=(next?next.predicted_speed:data.predicted_speed)+" km/h";
    $("predictedLevel").textContent=(next?next.congestion_level:data.congestion_level)+" • 15 min";
    $("confidence").textContent=Math.round(data.probability*100)+"%";
    $("distance").textContent=data.distance_km+" km";
    $("travelTime").textContent=data.travel_time_min+" min";
    $("delay").textContent=data.traffic_delay_min+" min";
    renderWeather(data.weather||{});
    drawRoute(data.route_points||[],origin,destination,data.congestion_level);
    saveLocal(origin,destination,data);
    let history={items:[]};
    try{history=await get("/api/route-history?origin="+encodeURIComponent(origin)+"&destination="+encodeURIComponent(destination))}catch{}
    renderTimeline(data,history.items||[]);
    renderAlert(data);
    $("status").textContent="Updated "+new Date(data.updated_at).toLocaleTimeString()+" • Live traffic + weather";
  }catch(error){
    $("status").textContent="Could not get prediction: "+error.message;
    setLevel(null);
    $("timelineNote").textContent="Try Refresh again";
  }finally{setBusy(false)}
}
$("predict").onclick=predict;
$("refresh").onclick=predict;
loadLocations().catch(error=>{$("status").textContent="Could not load locations: "+error.message});
setInterval(()=>{if(lastData)predict()},300000);