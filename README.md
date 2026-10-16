# Simulador web de módem antiguo

App educativa en Streamlit con FSK, DPSK y QAM. Incluye reproducción y pausa sincronizadas con el audio, una vista ampliada de la portadora, y los bits enviados y recuperados.

## Ejecutar en tu computadora

Requiere Python 3.10 o posterior.

```bash
python -m venv .venv
```

Activa el entorno virtual y luego instala las dependencias:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

La app se abrirá en el navegador. El audio se genera en el navegador, así que no requiere micrófono ni dispositivos de audio en el servidor.

## Publicar con GitHub y Streamlit Community Cloud

1. Crea un repositorio en GitHub y sube `app.py` y `requirements.txt` a la raíz del repositorio. Puedes incluir también este README.
2. Entra en [Streamlit Community Cloud](https://share.streamlit.io/) y conecta tu cuenta de GitHub.
3. Selecciona **Create app**, elige el repositorio y la rama, e indica `app.py` como archivo principal.
4. Pulsa **Deploy**. La app se publicará con una dirección `*.streamlit.app`.

Community Cloud instala las dependencias declaradas en `requirements.txt`. Al hacer cambios en GitHub, Streamlit puede actualizar la app desde ese repositorio.

## Modelo didáctico

La secuencia de ejemplo es `10110010`. La transmisión no agrega ruido; el receptor ideal recupera los bits originales. En la gráfica de la portadora se muestra una ventana ampliada que avanza con la animación, para distinguir las oscilaciones. El audio usa esa misma onda y la acelera para que sus frecuencias resulten audibles.
