---
name: ver-video
description: Hace que Claude «vea» un vídeo. Lo baja de un enlace (Instagram, TikTok, YouTube…) o lo coge de la computadora, saca sus cuadros y escribe lo que se dice con su segundo. Después lo explica segundo a segundo (el gancho, cada corte, por qué funciona) y da ideas para hacer uno como ese. Úsala cuando la persona pegue el enlace de un vídeo o arrastre uno y pida verlo, analizarlo, explicarlo o sacar ideas de él, o cuando escriba /ver-video.
argument-hint: "[enlace o vídeo]"
---

# Ver vídeos

Claude no ve vídeos: ve fotos y lee texto. Esta skill le prepara el vídeo así:
- los cuadros, en hojas, cada uno con su segundo;
- lo que se dice, escrito con su segundo;
- los cambios de plano;
- los datos de la publicación.

Con eso lo «ve» entero. Todo corre en la computadora de la persona.

**La carpeta de esta skill** es la que sale arriba como «Base directory» (aquí, `BASE`). El programa se corre **desde la
carpeta de trabajo de la persona** (donde estás), con la ruta completa, y deja lo suyo en `videos-vistos/`:

- Mac y Linux: `"BASE/.venv/bin/python" "BASE/ver.py" …`
- Windows: `"BASE\.venv\Scripts\python.exe" "BASE\ver.py" …`

Aquí lo llamamos `VER …`.

## Antes de nada (una vez por conversación)

1. `VER --comprobar`. Si dice «Todo bien.», sigue.
2. Si no existe `.venv` o algo sale «MAL», corre la instalación desde `BASE` y vuelve a comprobar:
   - Mac y Linux: `bash instalar.sh`
   - Windows: `powershell -ExecutionPolicy Bypass -File instalar.ps1`

   La primera vez tarda unos minutos. Dile a la persona que espere.

## Paso a paso

1. **El vídeo.** `VER "<enlace>"` o `VER "<ruta del vídeo>"`.
   - En un vídeo de minuto y medio tarda entre 20 segundos y un minuto.
   - La primera vez baja el modelo de voz y tarda más.
   - Si falla, dile a la persona lo que dice el mensaje, con palabras normales. Lo más común: el vídeo no es público, o es
     una publicación de fotos.
2. **Lee, en este orden:**
   - `videos-vistos/<nombre>/RESUMEN.md`: los datos, lo que se dice con su segundo, los cortes y la lista de imágenes;
   - `gancho.jpg`: los 3 primeros segundos;
   - cada `hoja-NN.jpg`, en orden.
3. **Mientras miras, cuéntalo en el chat**, sin esperar al final. Al terminar cada hoja, escribe una o dos líneas con lo que
   pasa en ese tramo: lo que se ve, lo que se dice y el texto en pantalla. Por ejemplo:
   > **0:00–0:03** · Un carro sale disparado por una rampa y se oye «El carro volador de Tesla no está a la venta».
   > Choca con lo que crees: ahí está el gancho.

   Así la persona va viendo que lo estás mirando de verdad.

   **Si hizo una pregunta concreta, contesta ESO**, con el segundo y lo que se ve o se dice ahí. Por ejemplo:
   - «¿de qué va este vídeo?»;
   - «¿en qué segundo enseña el precio?»;
   - «resúmeme esta entrevista»;
   - «¿qué app usa?»;
   - «¿cómo hizo esa transición?».

   Sirve con cualquier vídeo, no solo con Reels. El análisis completo de abajo, solo si pide analizarlo, entender por qué
   funcionó o no dice qué quiere. Después, ofrécelo en una línea.
4. **El análisis**, con estos apartados y en este orden:
   - **En una frase:** de qué va y por qué para el dedo.
   - **El gancho (0–3 s):** lo que se ve, lo que se oye y lo que se lee. Qué pregunta deja abierta o qué contradice. Si el
     gancho es flojo, dilo.
   - **Bloque a bloque:** una tabla con *Segundos · Qué dice · Qué se ve*. Un bloque es cada parte con su propia idea:
     no hace falta una fila por corte.
   - **El ritmo:**
     - cada cuánto cambia el plano (y los cortes con el mismo encuadre, que se ven en las hojas);
     - las palabras por minuto;
     - cuánto dura;
     - cada cuánto pasa algo nuevo en pantalla.
   - **Por qué funciona:** de 4 a 6 razones, cada una con su segundo. Nada genérico: «buena edición» no vale; «cada
     1–2 s entra algo nuevo: una tarjeta, un contador, un sello» sí.
   - **Lo flojo:** dónde se le puede ganar.
   - **Los números**, si la plataforma los da (vistas, Me gusta, comentarios, compartidos). Sin inventarte los que faltan:
     Instagram no da las vistas sin entrar en una cuenta.
5. **Ideas para hacer el tuyo.** Si no sabes de qué es su negocio o su cuenta, pregúntaselo antes de esta parte, en una
   sola pregunta. Después, 3 ideas:
   - **Con la misma forma:**
     - el mismo tipo de gancho;
     - el mismo orden de bloques;
     - el mismo remate.
   - **Con su tema y sus palabras.**
   - **Cada idea, con su gancho ya escrito** y lo que se vería en los 3 primeros segundos.
   - **Lo que se copia y lo que no.** Se copian la idea y la forma. Las palabras, el diseño y la música del otro, no.
6. **Si escoge una idea, escríbele el guion** con la misma forma que el vídeo que miraste:
   - frase a frase, en una tabla *Segundos · Qué dice · Qué se ve*;
   - los bloques en el mismo orden y con duraciones parecidas;
   - el mismo número de palabras por minuto, más o menos;
   - y el remate al final.

## Si el vídeo es suyo (para revisarlo antes de publicarlo)

Haz el mismo análisis y termina con **qué cambiaría antes de publicarlo**, cada cosa con su segundo:
- el gancho: ¿se entiende en 3 segundos qué va a pasar o qué pregunta queda abierta?
- lo que sobra: los tramos donde no entra nada nuevo y la gente se puede aburrir;
- el final: ¿deja claro qué hacer (seguir, comentar, guardar)?

Es tu opinión de cómo está hecho, no una predicción: no digas cuántas vistas va a tener.

## Reglas

- **No te inventes lo que no ves ni oyes.** La música y los efectos de sonido no los tienes: no digas qué canción suena. Si
  algo no se distingue en los cuadros, dilo.
- **La transcripción puede traer alguna palabra mal oída.** Corrígela por el contexto y por lo que se lee en pantalla.
- **Para un tramo con más detalle** (un efecto rápido, una transición), vuelve a pasar el vídeo ya bajado con más cuadros:
  `VER "videos-vistos/<nombre>/video.mp4" --cada 0.25`. Se queda en su misma carpeta.
- **Para comparar dos vídeos**, pasa los dos y compáralos apartado por apartado.
- **En vídeos largos** (más de 8 minutos), el programa saca menos cuadros por segundo para no pasar de unas 12 hojas. Si
  la persona quiere un tramo concreto, pásalo con `--cada` más pequeño.
- **Es para estudiar vídeos públicos.** No ofrezcas volver a subir el vídeo de otro ni quitarle la marca de agua.
- **Habla claro y corto, en el idioma de la persona.** Nada de jerga: «el gancho», «los cortes», «lo que pasa en pantalla».
- Al terminar, dile que los vídeos bajados se quedan en `videos-vistos/` por si quiere borrarlos.
