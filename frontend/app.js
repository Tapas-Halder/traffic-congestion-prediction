const API_BASE=window.API_BASE||"https://YOUR-RENDER-SERVICE.onrender.com";
const $=id=>document.getElementById(id);

const map=L.map("map").setView([22.5726,88.3639],12);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"© OpenStreetMap"}).addTo(map);
let marker=L.marker([22.5726,88.3639]).addTo(map);

async function get(url,options){
  const response=await fetch(API_BASE+url,options);
  if(!response.ok) throw Error(await response.text());
  return response.json();
}

async function refresh(){
  try{
    const lat=+$("lat").value;
    const lon=+$("lon").value;

    const [live,weather]=await Promise.all([
      get("/api/live?lat="+lat+"&lon="+lon),
      get("/api/weather?lat="+lat+"&lon="+lon)
    ]);

    if(live.current_speed!=null) $("inputSpeed").value=Math.round(live.current_speed);
    if(live.free_flow_speed!=null) $("freeFlow").value=Math.round(live.free_flow_speed);

    const weatherImpact=weather.weather_impact??0;
    $("weather").value=weatherImpact;
    $("weatherText").textContent=
      "Weather: "+(weather.description||"—")+
      " | "+(weather.temperature??"—")+"°C"+
      " | impact "+weatherImpact+"%";

    const prediction=await get("/api/predict",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        latitude:lat,
        longitude:lon,
        speed:+$("inputSpeed").value,
        free_flow_speed:+$("freeFlow").value,
        weather:weatherImpact
      })
    });

    $("level").textContent=prediction.congestion_level;
    $("speed").textContent=(live.current_speed??$("inputSpeed").value)+" km/h";
    $("predicted").textContent=prediction.predicted_speed+" km/h";
    $("confidence").textContent=Math.round(prediction.probability*100)+"%";

    marker.setLatLng([lat,lon]);
    map.setView([lat,lon],12);
    $("status").textContent="Live traffic + weather + ML prediction updated.";
  }catch(error){
    $("status").textContent="Error: "+error.message;
  }
}

$("refresh").onclick=refresh;
$("predict").onclick=refresh;
