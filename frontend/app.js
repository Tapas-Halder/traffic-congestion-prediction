const API_BASE=window.API_BASE||"";
const $=id=>document.getElementById(id);
const map=L.map("map").setView([22.57,88.36],11);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"© OpenStreetMap contributors"}).addTo(map);
const routeLayer=L.layerGroup().addTo(map),markers=L.layerGroup().addTo(map);
let lastData=null, busy=false, locationsReady=false, pageReady=false;
const levelColors={"Free Flow":"#12b76a","Moderate":"#f79009","Heavy":"#f04438","Severe":"#b42318","Unknown":"#667085"};

async function get(url,timeoutMs=45000){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),timeoutMs);
  try{
    const response=await fetch(API_BASE+url,{cache:"no-store",signal:controller.signal});
    const text=await response.text();
    let body={};
    try{body=text?JSON.parse(text):{}}catch{}
    if(!response.ok)throw new Error(body.detail||body.message||`Server error (${response.status})`);
    return body;
  }catch(error){
    if(error.name==="AbortError")throw new Error("The live traffic request timed out. Please try Refresh again.");
    throw error;
  }finally{clearTimeout(timer)}
}

function setBusy(value){
  busy=value;
  $("predict").disabled=value||!locationsReady;
  $("refresh").disabled=value||!locationsReady;
  $("predict").innerHTML=value?"Analyzing…":"Check traffic <span>→</span>";\n  if(value)showLoader("Connecting to TomTom, weather and ML model…"); else hideLoader();
}

function setLevel(level){
  $("level").textContent=level||"—";
  $("levelHint").textContent=level==="Free Flow"?"Road is moving freely":level==="Moderate"?"Moderate traffic":level==="Heavy"?"Heavy traffic":level==="Severe"?"Severe congestion":"Choose a route";
  $("level").style.color=levelColors[level]||"";
}

function drawRoute(points,origin,destination,level){
  routeLayer.clearLayers();markers.clearLayers();
  const latlngs=(points||[]).map(p=>[Number(p.lat),Number(p.lon)]).filter(p=>Number.isFinite(p[0])&&Number.isFinite(p[1]));
  if(latlngs.length<2)throw new Error("TomTom returned no road geometry for this route.");
  const color=levelColors[level]||"#2563eb";
  L.polyline(latlngs,{color,weight:8,opacity:.9}).addTo(routeLayer);
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
  $("weatherIcon").innerHTML=w.icon?'<img alt="" src="https://openweathermap.org/img/wn/'+w.icon+'@2x.png">':"☁";
}

function renderRoutes(routes){
  const list=(routes||[]).slice().sort((a,b)=>a.travel_time_min-b.travel_time_min);
  $("routesList").innerHTML=list.length?list.map((r,i)=>'<div class="route-card '+(r.route_index===0?"selected":"")+'"><div><span class="route-rank">'+(i+1)+'</span><div><strong>'+r.label+'</strong><small>'+r.distance_km+' km • '+r.traffic_status+'</small></div></div><div class="route-time"><strong>'+r.travel_time_min+' min</strong><small>delay '+r.traffic_delay_min+' min</small></div></div>').join(""):'<div class="empty-card">No alternative route was returned by TomTom for this trip.</div>';
  $("routeBest").textContent=list.length?"Fastest by current TomTom estimate: "+list[0].label+" • "+list[0].travel_time_min+" min":"Fastest route: unavailable";
}

function renderRoads(roads){
  const list=(roads||[]).filter(r=>r&&r.name).slice().sort((a,b)=>(b.current_speed??-1)-(a.current_speed??-1));
  $("roadsList").innerHTML=list.length?'<div class="road-row road-head"><span>Road</span><span>Speed</span><span>Free flow</span><span>Traffic</span></div>'+list.map(r=>'<div class="road-row"><span><strong>'+r.name+'</strong><small>'+(r.road_numbers&&r.road_numbers.length?r.road_numbers.join(" / "):"Road segment")+'</small></span><span>'+(r.current_speed??"—")+' km/h</span><span>'+(r.free_flow_speed??"—")+' km/h</span><span class="road-level" style="color:'+(levelColors[r.congestion_level]||"")+'">'+r.congestion_level+'</span></div>').join(""):'<div class="empty-card">TomTom did not return named road guidance for this route.</div>';
}

function localKey(o,d){return "trafficpulse:"+o+":"+d}
function saveLocal(o,d,data){
  try{
    const key=localKey(o,d),items=JSON.parse(localStorage.getItem(key)||"[]");
    items.push({timestamp:data.updated_at,current_speed:data.current_speed,congestion_level:data.congestion_level,traffic_delay_min:data.traffic_delay_min});
    localStorage.setItem(key,JSON.stringify(items.slice(-24)));
  }catch{}
}

function renderTimeline(data,serverHistory){
  let local=[];
  try{local=JSON.parse(localStorage.getItem(localKey($("origin").value,$("destination").value))||"[]")}catch{}
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
  $("status").textContent="Loading Kolkata locations…";
  const data=await get("/api/locations",15000);
  const origin=$("origin"),destination=$("destination");
  origin.innerHTML="";destination.innerHTML="";
  (data.locations||[]).forEach(name=>{origin.add(new Option(name,name));destination.add(new Option(name,name))});
  if(!data.locations||data.locations.length<2)throw new Error("The backend returned fewer than two Kolkata locations.");
  origin.value=data.locations[0];
  destination.value=data.locations[1];
  locationsReady=true;
  setBusy(false);
  $("status").textContent="Choose locations and click Check traffic.";
}

async function predict(){
  if(busy||!locationsReady)return;
  const origin=$("origin").value,destination=$("destination").value;
  if(!origin||!destination||origin===destination){
    $("status").textContent="Please choose two different Kolkata locations.";
    return;
  }
  setBusy(true);
  $("status").textContent="Getting TomTom route, live road traffic and weather…";
  try{
    showLoader("TomTom route received. Running ML congestion prediction…");\n    const data=await get("/api/route-predict?origin="+encodeURIComponent(origin)+"&destination="+encodeURIComponent(destination),70000);
    if(!data.route_points||data.route_points.length<2)throw new Error("No real road geometry was returned.");
    lastData=data;
    setLevel(data.congestion_level);
    $("speed").textContent=data.current_speed+" km/h";
    const next=data.forecast&&data.forecast[0];
    $("predicted").textContent=(next?next.predicted_speed:data.predicted_speed)+" km/h";
    $("predictedLevel").textContent=(next?next.congestion_level:data.congestion_level)+" • ML forecast";
    $("confidence").textContent=Math.round(Number(data.probability||0)*100)+"%";
    $("distance").textContent=data.distance_km+" km";
    $("travelTime").textContent=data.travel_time_min+" min";
    $("delay").textContent=data.traffic_delay_min+" min";
    $("routeSource").textContent=data.route_source||"TomTom route";
    renderWeather(data.weather||{});
    drawRoute(data.route_points,origin,destination,data.congestion_level);
    renderRoutes(data.routes||[]);
    renderRoads(data.roads||[]);
    saveLocal(origin,destination,data);
    let history={items:[]};
    try{history=await get("/api/route-history?origin="+encodeURIComponent(origin)+"&destination="+encodeURIComponent(destination),10000)}catch{}
    renderTimeline(data,history.items||[]);
    renderAlert(data);
    $("status").textContent="Updated "+new Date(data.updated_at).toLocaleTimeString()+" • Real road route + live traffic + weather";
  }catch(error){
    $("status").textContent="Prediction failed: "+error.message;
    setLevel(null);
  }finally{
    setBusy(false);
  }
}

$("predict").addEventListener("click",()=>predict());
$("refresh").addEventListener("click",()=>predict());
$("origin").addEventListener("change",()=>{if($("origin").value===$("destination").value&&$("destination").options.length>1)$("destination").selectedIndex=$("origin").selectedIndex===0?1:0});
$("destination").addEventListener("change",()=>{if($("origin").value===$("destination").value&&$("origin").options.length>1)$("origin").selectedIndex=$("destination").selectedIndex===0?1:0});

window.addEventListener("error",event=>{
  if(event.error)console.error(event.error);
  if(!busy)$("status").textContent="Page error: "+(event.message||"Please refresh the page.");
});

document.addEventListener("DOMContentLoaded",()=>{\n  if(!$("predict")||!$("origin")||!$("destination"))return;\n});\n\nloadLocations().catch(error=>{
  $("status").textContent="Could not load locations: "+error.message;
  $("predict").disabled=true;$("refresh").disabled=true;
});
setInterval(()=>{if(lastData&&!busy&&locationsReady)predict()},300000);
