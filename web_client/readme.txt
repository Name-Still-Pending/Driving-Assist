Projekt je primeren za postavitev na spletni strežnik.

Najbolj enostavna možnost zagona je preko navodil: https://threejs-journey.com/lessons/first-threejs-project#basic-website
Kratka navodila:
 * V tej mapi zaženi: npm install vite
 * V package.json dodaj (če še ni): 
    "scripts": {
     "dev": "vite",
     "build": "vite build"
    }
 * Zaženi strežni z: npm run dev
 * Na http://localhost:5173/ThreeJS_Primer.html se nahaja spletna aplikacija



Vizualizacija v primeru odpiranja spletne strani lokalno ne bo delovala, saj spletni brskalnik blokira dostop do ostalih datotek na lokalnem disku. Vir: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS/Errors/CORSRequestNotHttp

Rešitev za firefox: 
 - Da omogočite branje datotek v javascript, v about:config nastavite "security.fileuri.strict_origin_policy" na "false"
