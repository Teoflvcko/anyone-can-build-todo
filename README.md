# ⚡ TaskFlow Quantum — Next-Gen Productivity Workspace

> Una piattaforma completa di produttività personale, gamification e organizzazione sviluppata in **Python & Django**, con architettura moderna, design system cyberpunk scuro/viola e zero dipendenze esterne bloccanti.

---

## 🌟 Panoramica del Progetto

**TaskFlow Quantum** trasforma la classica To-Do list in un quartier generale per la gestione del tempo, del benessere e dei progetti. Il sistema accoglie l'utente con una **Landing Page introduttiva** dotata di pulsante **START** per entrare nell'applicazione, con supporto multilingua (Italiano / Inglese).

---

## 💎 Funzionalità Principali

### 1. 📋 Gestione Compiti Avanzata (Task Management)
- **Compiti e Sotto-Obiettivi (Subtasks):** Creazione task con priorità (*Low, Medium, High*), categorie, date di scadenza, tempo stimato in minuti e livelli energetici (*Deep Work, Medium, Low Energy*).
- **Stati Dinamici:** *To Do*, *In Progress*, *Done*, con supporto per task preferiti, duplicazione e archiviazione.
- **Scomposizione Intelligente AI:** Genera automaticamente 3 sotto-obiettivi pratici a partire dal titolo del compito.

### 2. 📊 Viste Multiple di Lavoro
- **📋 My Tasks:** visualizzazione a lista con filtri rapidi, ordinamento e ricerca.
- **📅 Timeline Gantt:** pianificazione orizzontale a 14 giorni per visualizzare i carichi di lavoro e le sovrapposizioni.
- **📊 Kanban Board:** bacheca visuale a colonne (*Da Fare*, *In Corso*, *Completati*).
- **📆 Calendario Mensile Interattivo:** griglia completa del mese con evidenziazione dei giorni, delle scadenze e indicatore del giorno corrente.
- **🎯 Matrice di Eisenhower:** categorizzazione automatica in 4 quadranti (*Urgente & Importante*, *Non Urgente ma Importante*, *Urgente non Importante*, *Né Urgente né Importante*).
- **📈 Analytics & Statistiche:** grafici di completamento, tasso di produttività e metriche di velocità settimanale.
- **🍅 Focus Timer Pomodoro:** timer integrato a intervalli di 25 minuti di lavoro e 5 minuti di pausa con suoni sintetizzati.

### 3. 🧠 Second Brain & Wiki della Conoscenza
- Rete di note e documenti categorizzati con tag.
- Grafo visuale delle connessioni (*Knowledge Graph*) animato in tempo reale su Canvas HTML5.

### 4. 💰 Finanze Personali & Budgeting
- Tracciamento di entrate e uscite con categorie (*Cibo, Casa, Trasporti, Svago, Salute*).
- Grafico interattivo a ciambella (*Donut Chart*) disegnato su Canvas con saldo del totale uscite.
- Salvadanai per obiettivi di risparmio (*Savings Goals*) con barre di avanzamento percentuali.

### 5. 📖 Diario Personale & Tracciamento Umore
- Pagine quotidiane di diario con riflessioni ed esercizio delle 3 cose per cui essere grati (*Gratitude Journal*).
- Selettore meteo del giorno e stato d'animo (*Raggiante, Motivato, Calmo, Stanco, Stressato*).

### 6. 🎮 Gamification RPG (Productivity RPG)
- Profilo eroe con livelli, punti esperienza (XP) e monete d'oro guadagnate lavorando.
- Statistiche di ruolo: *Disciplina, Creatività, Focus, Vitalità*.
- **Bacheca Missioni Giornaliere (*Daily Quests*):** 3 sfide giornaliere con barre di avanzamento.
- **🎁 Baule della Fortuna Giornaliero:** scrigno misterioso che accredita bonus di XP e monete una volta al giorno.
- **Negozio delle Ricompense:** negozio per acquistare premi della vita reale (es. "Pizza con amici", "1 ora di gaming") con le monete guadagnate.

### 7. 🎧 Oasi Sonora & Studio del Respiro
- **Mixer Web Audio dal vivo:** 5 canali sonori sintetizzati in tempo reale senza file pesanti (*Pioggia, Onde oceaniche, Camino, Caffetteria, Brezza del bosco*).
- **Guida Box Breathing:** animazione a sfera orbitale per la respirazione quadrata (4s Inspira • 4s Trattieni • 4s Espira • 4s Trattieni).

### 8. 🤖 Risolutore di Problemi AI (Conversational Chatbot)
- Chatbot integrato a fumetti con simulazione naturale di digitazione (`● ● ●`).
- Diagnosi psicologica della causa profonda, strategia in 3 passi e compiti operativi inseribili nella to-do list con un clic.

### 9. ⚡ Strumenti di Produttività Operativa
- **📌 Post-it Rapido Flottante (*Floating Scratchpad*):** blocco note adesivo con salvataggio automatico continuo in `localStorage` e conversione con 1 clic in To-Do.
- **🔍 Ricerca Globale Rapida Spotlight (`Cmd + K` / `Ctrl + K`):** barra di comando universale per cercare istantaneamente compiti, note o saltare alle sezioni.
- **🔔 Notifiche Desktop Reali:** allarmi del browser basati su Web Notifications API per le scadenze vicine.
- **📥 Centro Esportazione & Backup:** download in CSV (per Excel sia per Task che per Finanze), `.ics` (per Google Calendar e Apple Calendar), JSON completo e stampa PDF.
- **🔐 Autenticazione & Privacy:** sistema di registrazione e accesso con gestione sicura di password e sessioni utente.

---

## 🛠️ Architettura e Struttura File

| File | Responsabilità |
|---|---|
| `config/settings.py` | Configurazione globale di Django, impostazioni di sicurezza, sessioni e internazionalizzazione. |
| `config/urls.py` | Routing principale con supporto ad admin, auth (`/accounts/`, `/signup/`) e applicazione. |
| `todos/models.py` | Modelli del database SQLite (`Todo`, `Project`, `Habit`, `Transaction`, `SavingsGoal`, `WikiPage`, `JournalEntry`, `MediaItem`, `UserProfileRPG`, `RpgReward`, `Notification`). |
| `todos/urls.py` | Tutti gli endpoint e gli indirizzi dell'applicazione. |
| `todos/views.py` | Logica applicativa, controlli di sicurezza, calcoli finanziari, algoritmi AI ed esportazioni dati. |
| `todos/templates/todos/welcome.html` | Pagina iniziale di benvenuto con pulsante START, grafica cyberpunk e presentazione funzioni. |
| `todos/templates/todos/todo_list.html` | Interfaccia principale del workspace con tutte le viste, pannelli e script interattivi. |
| `todos/templates/registration/` | Pagine di Login e Registrazione (Signup) in stile scuro coordinato. |
| `todos/tests.py` | Suite di 54 test unitari automatizzati. |

---

## 🚀 Istruzioni per Avviare il Progetto

Il progetto utilizza **uv** per la gestione rapida e riproducibile delle dipendenze e di Python.

### 1. Requisiti e Installazione
```bash
# Installa le dipendenze e prepara il database
make setup
```
*(In alternativa: `uv sync && uv run python manage.py migrate`)*

### 2. Avviare il Server Locale
```bash
make run
```
Il sito si aprirà all'indirizzo **http://127.0.0.1:8000/** mostrando la pagina iniziale di benvenuto. Premendo il pulsante **START** si accede all'applicazione.

### 3. Eseguire i Test
```bash
make test
```
Tutti i **54 test unitari** vengono eseguiti automaticamente verificando ogni singola funzionalità.

### 4. Controlli di Qualità del Codice
```bash
make check
```
Esegue i linter Ruff, il controllo di formattazione del codice, i controlli pre-commit e l'intera suite di test.
