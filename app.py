"""Simulador web didáctico de FSK, DPSK y QAM con Streamlit."""

import json

import numpy as np
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(page_title="Laboratorio de módem", page_icon="📡", layout="wide")

BITS = [int(bit) for bit in "10110010"]
MUESTRAS_BIT = 2400
F_BAJA = 60.0
F_ALTA = 120.0


def generar_senal(tecnica):
    """Genera la portadora y los bits recuperados para la técnica elegida."""
    bits = np.array(BITS, dtype=int)
    if tecnica == "QAM":
        bits_qam = bits.copy()
        if len(bits_qam) % 2:
            bits_qam = np.append(bits_qam, 0)
        unidades = bits_qam.reshape(-1, 2)
        muestras_simbolo = 2 * MUESTRAS_BIT
    else:
        unidades = bits.reshape(-1, 1)
        muestras_simbolo = MUESTRAS_BIT

    senal = np.zeros(len(unidades) * muestras_simbolo, dtype=np.float32)
    fase_previa = 0.0
    for indice, unidad in enumerate(unidades):
        inicio = indice * muestras_simbolo
        fin = inicio + muestras_simbolo
        tiempo = np.arange(muestras_simbolo) / MUESTRAS_BIT
        if tecnica == "FSK":
            frecuencia = F_ALTA if unidad[0] else F_BAJA
            senal[inicio:fin] = np.cos(2 * np.pi * frecuencia * tiempo)
        elif tecnica == "DPSK":
            fase = fase_previa + (np.pi if unidad[0] else 0.0)
            senal[inicio:fin] = np.cos(2 * np.pi * F_BAJA * tiempo + fase)
            fase_previa = fase
        else:
            nivel_i = 1.0 if unidad[0] == 0 else -1.0
            nivel_q = 1.0 if unidad[1] == 0 else -1.0
            senal[inicio:fin] = (
                nivel_i * np.cos(2 * np.pi * F_BAJA * tiempo)
                - nivel_q * np.sin(2 * np.pi * F_BAJA * tiempo)
            ) / np.sqrt(2.0)

    # Este modelo no añade ruido: el receptor ideal recupera la secuencia original.
    return {"bits": BITS, "senal": senal.tolist(), "muestras_bit": MUESTRAS_BIT}


senales = {nombre: generar_senal(nombre) for nombre in ("FSK", "DPSK", "QAM")}
payload = json.dumps(senales, separators=(",", ":")).replace("<", "\\u003c")

html = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box} body{margin:0;background:#eef3f8;color:#18324b;font-family:Inter,Segoe UI,Arial,sans-serif}
.app{max-width:1180px;margin:0 auto;padding:12px 14px 18px}
.toolbar{background:#fff;border:1px solid #dbe4ed;border-radius:14px;padding:13px 16px;display:flex;align-items:center;gap:9px;flex-wrap:wrap;box-shadow:0 3px 12px #18324b0b}
label{font-size:12px;font-weight:700;letter-spacing:.07em;color:#5d7185}
select,button{font:600 14px Inter,Segoe UI,Arial,sans-serif;border:1px solid #cfdae5;border-radius:9px;padding:9px 12px;background:#fff;color:#18324b}
select{min-width:100px}button{cursor:pointer;transition:.15s}button:hover{transform:translateY(-1px);box-shadow:0 3px 9px #18324b20}
button.primary{background:#2563eb;border-color:#2563eb;color:#fff}button.sound{background:#e9f7f2;color:#14785e;border-color:#c5e9db}
.state{margin-left:auto;color:#5d7185;font-size:13px}.cards{display:grid;grid-template-columns:1fr;gap:10px;margin-top:11px}
.card{background:#fff;border:1px solid #dbe4ed;border-radius:13px;padding:12px 14px;box-shadow:0 3px 12px #18324b08}
.card h3{font-size:14px;margin:0 0 6px;color:#18324b}.card canvas{display:block;width:100%;height:145px}
.carrier canvas{height:175px}.caption{font-size:12px;line-height:1.55;color:#5d7185;background:#f7f9fc;border-radius:10px;margin-top:10px;padding:10px 12px}
@media(max-width:600px){.app{padding:8px}.card canvas{height:125px}.carrier canvas{height:155px}.state{margin-left:0;width:100%}}
</style>
</head>
<body>
<main class="app">
  <div class="toolbar">
    <label for="tech">TÉCNICA</label>
    <select id="tech"><option>FSK</option><option>DPSK</option><option>QAM</option></select>
    <button id="play" class="primary">▶ Reproducir</button>
    <button id="pause">Ⅱ Pausar</button>
    <button id="reset">↺ Reiniciar</button>
    <button id="listen" class="sound">♫ Escuchar</button>
    <span id="state" class="state">Lista para transmitir</span>
  </div>
  <section class="cards">
    <article class="card"><h3>1 · Bits digitales transmitidos</h3><canvas id="bits"></canvas></article>
    <article class="card carrier"><h3 id="signalTitle">2 · Portadora modulada (FSK)</h3><canvas id="signal"></canvas></article>
    <article class="card"><h3>3 · Bits recuperados en el receptor</h3><canvas id="received"></canvas></article>
  </section>
  <div id="caption" class="caption"></div>
</main>
<script>
const DATOS = __PAYLOAD__;
const DESCRIPCIONES = {
  FSK:"FSK: cada bit se representa con una frecuencia distinta.",
  DPSK:"DPSK: el bit se representa mediante un cambio de fase respecto al símbolo anterior.",
  QAM:"QAM de 4 estados: cada símbolo combina componentes I y Q y transporta dos bits."
};
const BIT_SEC=0.24, AUDIO_HZ=22050, VENTANA=0.20;
let tecnica="FSK", posicion=0, reproduciendo=false, contexto=null, fuente=null, inicioAudio=0, baseAudio=0, raf=null;
const el=id=>document.getElementById(id), bitsCanvas=el("bits"), signalCanvas=el("signal"), receivedCanvas=el("received");
function ajustar(canvas){const dpr=window.devicePixelRatio||1, r=canvas.getBoundingClientRect();canvas.width=Math.max(1,Math.round(r.width*dpr));canvas.height=Math.max(1,Math.round(r.height*dpr));const c=canvas.getContext("2d");c.setTransform(dpr,0,0,dpr,0,0);return {c,w:r.width,h:r.height}}
function fondo(c,w,h){c.clearRect(0,0,w,h);c.strokeStyle="#e7edf3";c.lineWidth=1}
function dibujarBits(canvas,lista,cursor,color){const {c,w,h}=ajustar(canvas);fondo(c,w,h);const L=42,R=12,T=10,B=24,pw=w-L-R,ph=h-T-B;
 c.font="11px Segoe UI,Arial";c.textAlign="right";c.fillStyle="#73869a";
 [0,1].forEach(v=>{const y=T+ph*(1-v);c.beginPath();c.moveTo(L,y);c.lineTo(w-R,y);c.stroke();c.fillText(String(v),L-9,y+4)});
 c.strokeStyle=color;c.lineWidth=2.3;c.lineJoin="round";c.beginPath();lista.forEach((v,i)=>{const x=L+pw*i/lista.length,y=T+ph*(1-v);if(i===0)c.moveTo(x,y);else{const py=T+ph*(1-lista[i-1]);c.lineTo(x,py);c.lineTo(x,y)}});c.lineTo(w-R,T+ph*(1-lista[lista.length-1]));c.stroke();
 c.fillStyle="#73869a";c.textAlign="center";for(let i=0;i<=lista.length;i++){const x=L+pw*i/lista.length;c.fillText(String(i),x,h-6)}
 const x=L+pw*Math.max(0,Math.min(1,cursor/lista.length));c.strokeStyle="#d64545";c.lineWidth=1.4;c.beginPath();c.moveTo(x,T);c.lineTo(x,T+ph);c.stroke();
}
function dibujarSenal(){const {c,w,h}=ajustar(signalCanvas);fondo(c,w,h);const L=44,R=12,T=10,B=26,pw=w-L-R,ph=h-T-B;
 const datos=DATOS[tecnica], senal=datos.senal, mpb=datos.muestras_bit, total=datos.bits.length;
 const inicio=Math.min(Math.max(0,posicion-VENTANA/2),Math.max(0,total-VENTANA)), fin=Math.min(total,inicio+VENTANA);
 const yv=v=>T+ph*(1-(v+1.25)/2.5);
 [-1,0,1].forEach(v=>{const y=yv(v);c.strokeStyle="#e7edf3";c.beginPath();c.moveTo(L,y);c.lineTo(w-R,y);c.stroke();c.fillStyle="#73869a";c.font="11px Segoe UI,Arial";c.textAlign="right";c.fillText(String(v),L-8,y+4)});
 c.strokeStyle="#e7edf3";c.beginPath();c.moveTo(L,T+ph);c.lineTo(w-R,T+ph);c.stroke();
 c.strokeStyle="#e68132";c.lineWidth=1.5;c.beginPath();let started=false;const i0=Math.max(0,Math.floor(inicio*mpb)),i1=Math.min(senal.length-1,Math.ceil(fin*mpb));
 for(let i=i0;i<=i1;i++){const x=L+pw*((i/mpb-inicio)/(fin-inicio)),y=yv(senal[i]);if(!started){c.moveTo(x,y);started=true}else c.lineTo(x,y)}c.stroke();
 c.fillStyle="#73869a";c.font="11px Segoe UI,Arial";c.textAlign="center";for(let j=0;j<=4;j++){const t=inicio+(fin-inicio)*j/4,x=L+pw*j/4;c.fillText(t.toFixed(2),x,h-6)}
 const xc=L+pw*(posicion-inicio)/(fin-inicio);c.strokeStyle="#d64545";c.lineWidth=1.4;c.beginPath();c.moveTo(xc,T);c.lineTo(xc,T+ph);c.stroke();
}
function dibujar(){const datos=DATOS[tecnica];dibujarBits(bitsCanvas,datos.bits,posicion,"#2563eb");dibujarSenal();dibujarBits(receivedCanvas,datos.bits,posicion,"#14866d")}
function actualizar(){el("signalTitle").textContent="2 · Portadora modulada ("+tecnica+")";el("caption").textContent=DESCRIPCIONES[tecnica]+" La gráfica de la portadora muestra una ventana ampliada que sigue la transmisión. El audio usa esa misma forma de onda, acelerada a 0,24 s por bit para que sea audible.";dibujar()}
function crearBuffer(){const senal=DATOS[tecnica].senal, nbits=DATOS[tecnica].bits.length, n=Math.floor(nbits*BIT_SEC*AUDIO_HZ), buffer=contexto.createBuffer(1,n,AUDIO_HZ), salida=buffer.getChannelData(0), mpb=DATOS[tecnica].muestras_bit;
 for(let i=0;i<n;i++){const bitTime=i/AUDIO_HZ/BIT_SEC, source=bitTime*mpb, lo=Math.floor(source), frac=source-lo;salida[i]=senal[lo]*(1-frac)+(senal[Math.min(lo+1,senal.length-1)]||0)*frac}
 const fade=Math.min(Math.floor(.008*AUDIO_HZ),Math.floor(n/4));for(let i=0;i<fade;i++){salida[i]*=i/fade;salida[n-1-i]*=i/fade}return buffer}
function tiempoActual(){return reproduciendo?baseAudio+contexto.currentTime-inicioAudio:baseAudio}
function detenerFuente(){if(fuente){try{fuente.stop()}catch(e){}fuente.disconnect();fuente=null}}
function iniciar(){if(reproduciendo)return;if(posicion>=DATOS[tecnica].bits.length)posicion=0;
 if(!contexto)contexto=new(window.AudioContext||window.webkitAudioContext)();contexto.resume();const dur=DATOS[tecnica].bits.length*BIT_SEC;baseAudio=Math.min(posicion/DATOS[tecnica].bits.length*dur,dur-.001);
 const buffer=crearBuffer();fuente=contexto.createBufferSource();fuente.buffer=buffer;fuente.connect(contexto.destination);inicioAudio=contexto.currentTime;fuente.start(0,baseAudio);reproduciendo=true;el("state").textContent="Transmitiendo y reproduciendo: "+tecnica;el("play").textContent="▶ En curso";bucle()}
function pausar(){if(!reproduciendo)return;baseAudio=tiempoActual();reproduciendo=false;detenerFuente();cancelAnimationFrame(raf);el("state").textContent="En pausa";el("play").textContent="▶ Reproducir";posicion=baseAudio/BIT_SEC;dibujar()}
function reiniciar(){pausar();detenerFuente();baseAudio=0;posicion=0;el("state").textContent="Lista para transmitir";actualizar()}
function bucle(){if(!reproduciendo)return;const t=tiempoActual(),dur=DATOS[tecnica].bits.length*BIT_SEC;posicion=Math.min(DATOS[tecnica].bits.length,t/BIT_SEC);dibujar();if(t>=dur){reproduciendo=false;detenerFuente();baseAudio=0;posicion=DATOS[tecnica].bits.length;el("state").textContent="Transmisión y audio completados";el("play").textContent="▶ Reproducir";dibujar();return}raf=requestAnimationFrame(bucle)}
el("tech").addEventListener("change",e=>{reiniciar();tecnica=e.target.value;actualizar()});el("play").addEventListener("click",iniciar);el("listen").addEventListener("click",reiniciar);el("listen").addEventListener("click",iniciar);el("pause").addEventListener("click",pausar);el("reset").addEventListener("click",reiniciar);window.addEventListener("resize",dibujar);actualizar();
</script>
</body>
</html>""".replace("__PAYLOAD__", payload)


st.markdown(
    """<style>
      .stApp {background: linear-gradient(180deg,#eaf1f8 0%,#f7f9fc 240px,#f7f9fc 100%);}
      .block-container {max-width: 1250px; padding-top: 1.4rem; padding-bottom: 1rem;}
      [data-testid="stHeader"] {background: transparent;}
    </style>""",
    unsafe_allow_html=True,
)
st.markdown(
    """<div style="background:#18324b;border-radius:16px;padding:20px 24px;color:white;margin-bottom:8px">
      <div style="font-size:12px;font-weight:700;letter-spacing:.12em;color:#a9c6e4">LABORATORIO DE COMUNICACIONES</div>
      <div style="font-size:30px;font-weight:750;margin-top:4px">Simulador de módem</div>
      <div style="font-size:15px;color:#d2dfec;margin-top:3px">Explora cómo viajan los bits y escucha la señal modulada.</div>
    </div>""",
    unsafe_allow_html=True,
)
components.html(html, height=850, scrolling=False)
