# RrjetaKompjuterike_Gr34

## Projekt 2 – Rrjetat Kompjuterike

### Përshkrimi
Ky projekt implementon një sistem **klient-server TCP** në Python për një rrjet lokal me të paktën 4 pajisje.  
Serveri menaxhon lidhjet dhe komunikimin e klientëve, ndërsa klientët mund të lexojnë, shkruajnë, dërgojnë, marrin dhe menaxhojnë file në server sipas privilegjeve.

---

### Teknologjitë
- **Python 3.x**  
- **Socket programming (TCP)**  
- **Threading** për menaxhimin e shumë klientëve  
- **File handling**  
- **Logging** për monitorimin e trafikut  

---

### Serveri – Funksionalitetet
- Vendos IP dhe port të serverit  
- Dëgjon lidhjet nga të gjithë klientët  
- Kufizon numrin e lidhjeve dhe i vendos klientët në pritje nëse kalon pragun  
- Lexon dhe ruan mesazhet e klientëve  
- Mbyll lidhjet inaktive dhe rikuperon klientët kur rifuten  
- Jep qasje të plotë për klientët me privilegje të plota  
- Monitoron trafikun dhe shfaq:
  - Numrin e lidhjeve aktive  
  - IP-të e klientëve  
  - Numrin e mesazheve për secilin klient  
  - Trafikun total në bytes  
- Statistikët shfaqen me komandën `STATS` ose ruhen në `server_stats.txt`

---

### Klienti – Funksionalitetet
- Krijon socket lidhjen me serverin (IP + port)  
- Klientët **admin** kanë privilegje të plota dhe mund të ekzekutojnë komandat e mëposhtme:

| Komanda | Përshkrimi |
|---------|------------|
| `/list` | Liston file në directory |
| `/read <filename>` | Lexon përmbajtjen e file-it |
| `/upload <filename>` | Dërgon file në server |
| `/download <filename>` | Shkarkon file nga serveri |
| `/delete <filename>` | Fshin file në server |
| `/search <keyword>` | Kërkon file me një fjalë kyçe |
| `/info <filename>` | Shfaq madhësinë, datën e krijimit dhe modifikimit të file-it |

- Klientët **read-only** mund vetëm të lexojnë file  
- Lexon përgjigjet nga serveri dhe dërgon mesazhe tekst  
- Qasje më e shpejtë për klientët admin

---

### Udhëzime Ekzekutimi
```bash
python -m server.server
python -m client.client
