# Email Automation & Reminder System: Complete Student Guide

This guide walks through the project from idea to GitHub. **The full working code is already in `src/` and `main.py`** (section 7).

---

## 1. Project Explanation

### Simple explanation
Imagine you must remind 200 students about tomorrow's webinar, remind 30 clients about unpaid invoices, and tell your team about Monday's meeting. Writing each email by hand takes hours. An **Email Automation & Reminder System** does it for you: you keep a list of people, write the message once, say *when* to send it, and the program sends personalized emails automatically and keeps a record.

### Problem it solves
- Manual repetitive communication wastes time
- People forget follow-ups, so deadlines and payments slip
- Copy-paste mistakes (wrong name, wrong date)
- No record of who was contacted and who was not

### Why it is useful
| Team | Value |
|------|-------|
| Companies | Consistent, on-time communication with an audit trail |
| Trainers | Automatic webinar/class/assignment reminders reduce no-shows |
| HR | Onboarding steps, interview schedules, policy reminders |
| Sales | Follow-ups and payment reminders without chasing manually |
| Operations | Meeting alerts, shift and task notifications |

### How companies use it
- **Reminders / meeting alerts:** calendar-driven emails 24 hours and 1 hour before
- **Follow-ups:** "no reply in 3 days" triggers a nudge
- **Payment reminders:** before the due date, on the due date, and after
- **Webinar reminders:** confirmation, day-before, hour-before, thank-you
- **Task notifications:** assignee gets an email when a task is created or overdue

Real companies often use tools such as Outlook rules, Mailchimp, HubSpot, or custom scripts, and the logic is the same as this project: *list, template, schedule, send, track*.

### Technical explanation
The program reads two CSV files with **pandas**. For each reminder whose `send_date + send_time` has arrived, it looks up the contacts in the target group, fills `{placeholders}` in a text template using that row's data, builds a MIME message with `email.message.EmailMessage`, and sends it through **smtplib** over TLS. Every attempt is logged and written to a CSV report. A **scheduler** re-runs this check on a timer. A **dry-run** flag replaces the network step with a no-op.

### Workflow
```
contact list → message template → scheduled reminder → email sending → status tracking → report generation
 contacts.csv   templates/*.txt    reminders.csv        smtplib         log + status       outputs/*.csv
```

---

## 2. Tech Stack Options

| | **A: Easy** | **B: Intermediate** | **C: Advanced** |
|---|---|---|---|
| Tools | Python, csv, smtplib, `time.sleep` | Python, **pandas**, smtplib, email.message, schedule, logging, python-dotenv | B + Streamlit dashboard, SQLite, Jinja2 HTML templates, attachments, pytest |
| Difficulty | Beginner | Lower-intermediate | Intermediate to advanced |
| Output | Sends a fixed email to a list | Personalized, scheduled, logged emails + CSV reports | Web dashboard, upload CSVs, charts, delivery stats |

**Best for students: Option B.** It matches the course topics (pandas, smtplib, datetime, logging), looks professional on GitHub, and is doable in about 6 days. This project implements B, with an optional Streamlit dashboard as an extension (Option C).

---

## 3. Project Architecture

### Diagram
```
                 ┌──────────────────────────── INPUT ────────────────────────────┐
                 │  data/contacts.csv    data/reminders.csv    templates/*.txt   │
                 └──────────────┬────────────────┬──────────────────┬────────────┘
                                ▼                ▼                  ▼
                 ┌──────────────────────────── PROCESSING ──────────────────────────┐
                 │ data_loader  →  scheduler/select_due  →  template_engine         │
                 │ (read+validate)   (which reminders        (personalize message)  │
                 │                    are due?)                                      │
                 │                         ▼                                         │
                 │   email_builder  →  email_sender (SMTP or dry-run)  →  status     │
                 └──────────────┬──────────────────┬───────────────────┬────────────┘
                                ▼                  ▼                   ▼
                 ┌──────────────────────────── OUTPUT ────────────────────────────┐
                 │ sent emails    failed emails    logs/email_automation.log       │
                 │ outputs/email_report_<time>.csv    outputs/dry_run_preview.txt  │
                 └────────────────────────────────────────────────────────────────┘
```

### Data flow
1. `main.py` parses command-line options and decides dry-run vs live.
2. `engine.run_batch` loads both CSVs via `data_loader` (validating columns and emails).
3. `select_due` keeps reminders whose scheduled time is now or earlier.
4. For each reminder, the group's contacts are fetched. For each contact, a context dictionary (reminder columns + contact columns + sender name) fills the subject and body.
5. `email_builder` creates the message; `email_sender` sends it (or simulates).
6. Each outcome is logged and stored as a result record; live successes are saved to `send_history.csv` to prevent duplicates.
7. `report` writes the CSV and prints a summary.

---

## 4. Implementation Plan

**Phase 1: Setup.** *Do:* install Python, VS Code, Git; create a GitHub account. *Why:* a clean toolchain avoids later errors. *Output:* `python --version` and `git --version` work. *Mistake:* forgetting "Add Python to PATH" on Windows.

**Phase 2: Folder creation.** *Do:* create the folders in section 5. *Why:* separating data, code, and outputs is what makes a project look professional. *Output:* the tree below. *Mistake:* putting everything in one file.

**Phase 3: Contact CSV.** *Do:* create `data/contacts.csv` with `contact_id,name,email,group,company`. *Why:* the audience is data, not code. *Output:* 10 to 15 dummy rows. *Mistakes:* using real people's emails; extra spaces; Excel changing the encoding (save as "CSV UTF-8").

**Phase 4: Email templates.** *Do:* write `.txt` files with `{name}`-style placeholders. *Why:* message written once, reused for everyone. *Output:* four templates. *Mistake:* placeholder names that do not match CSV column names.

**Phase 5: SMTP configuration.** *Do:* create `.env` from `.env.example`; for Gmail enable 2-Step Verification and generate an App Password. *Why:* keeps secrets out of code. *Output:* `get_smtp_settings()` returns your values. *Mistakes:* using the normal Gmail password; committing `.env`; wrong port (587 uses STARTTLS, 465 uses SSL).

**Phase 6: Personalization.** *Do:* `template_engine.render()` with a context dict. *Output:* "Hello Asha Verma, ...". *Mistake:* crashing on a missing field (this project leaves unknown placeholders untouched instead).

**Phase 7: Reminder scheduling.** *Do:* parse `send_date` + `send_time` into a datetime; compare with now; add `--schedule` loop. *Output:* only due reminders are processed. *Mistakes:* wrong date format (use `YYYY-MM-DD` and `HH:MM`); forgetting that the script must keep running for the timer to work.

**Phase 8: Sending.** *Do:* `EmailSender` with dry-run, retries, and one reused connection. *Output:* `SENT` / `FAILED` / `DRY_RUN` statuses. *Mistakes:* sending thousands of emails with no delay (Gmail limits you); testing live before dry-run.

**Phase 9: Logging and reports.** *Do:* `logging` to console and file; pandas `to_csv` for the report. *Output:* `logs/email_automation.log`, `outputs/email_report_*.csv`. *Mistake:* using `print` only, so nothing is saved.

**Phase 10: GitHub upload.** See section 10. *Mistake:* uploading `.env`.

---

## 5. Folder Structure

```
Email-Automation-Reminder-System/
│
├── data/              contacts.csv, reminders.csv  (input data, dummy only)
├── templates/         message templates with {placeholders}
├── src/               all application modules (one job per file)
├── tests/             unit tests
├── outputs/           CSV reports, dry-run email preview
├── logs/              email_automation.log
├── images/            screenshots for README
├── docs/              this guide, sample terminal output
├── README.md          project front page
├── requirements.txt   pip dependencies
├── .env.example       safe template for secrets
├── .gitignore         files Git must ignore (.env, venv, ...)
└── main.py            run this file
```

---

## 6. Installation Guide

1. **Python:** download Python 3.9+ from python.org. On Windows tick **"Add Python to PATH"**. Check with `python --version` (Windows) or `python3 --version` (Mac).
2. **Virtual environment** (an isolated box for this project's libraries):

| | Windows | Mac / Linux |
|---|---|---|
| Create | `python -m venv venv` | `python3 -m venv venv` |
| Activate | `venv\Scripts\activate` | `source venv/bin/activate` |
| Install | `pip install -r requirements.txt` | `pip3 install -r requirements.txt` |

3. **Libraries:** pandas (CSV handling), python-dotenv (read `.env`), schedule (timer). `smtplib`, `email`, `datetime`, `logging`, `csv` are built into Python.
4. PowerShell error "running scripts is disabled"? Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt.

---

## 7. Full Project Code

All code is included in the repository, fully commented:

| File | Responsibility |
|------|----------------|
| `main.py` | CLI options: `--send`, `--all`, `--as-of`, `--schedule`, `--generate-sample` |
| `src/config.py` | Paths, `.env` loading, SMTP settings |
| `src/data_loader.py` | Read contacts/reminders, validate emails and dates |
| `src/template_engine.py` | Load template, fill placeholders safely |
| `src/email_builder.py` | Create `EmailMessage` |
| `src/email_sender.py` | SMTP send, dry-run, retries |
| `src/engine.py` | The main workflow and duplicate protection |
| `src/scheduler.py` | Repeating timer |
| `src/report.py` | CSV report and summary |
| `src/logger_setup.py` | Logging |
| `src/sample_data.py` | Dummy data generator |
| `tests/test_core.py` | 9 unit tests |

---

## 8. Virtual Simulation

You do not need a company system. Simulate everything:

- **Dummy contacts:** `python main.py --generate-sample` creates 11 people across 4 groups, all `@example.com` (a domain reserved so it can never reach a real person). One address is deliberately broken to demonstrate failure handling.
- **Sample reminders:** the same command creates 5 reminders (webinar, payment, meeting, task) dated relative to today.
- **Templates:** edit the files in `templates/`; add your own and reference them in `reminders.csv` by file name (without `.txt`).
- **Dry-run:** `python main.py` or `python main.py --all`. The full workflow runs, nothing is sent.
- **Time travel:** `python main.py --as-of "2026-11-25 10:30"` pretends it is that moment, so you can show future reminders firing.
- **Logs/reports:** produced automatically in `logs/` and `outputs/`.
- **Optional live test:** put your own second email address in `contacts.csv`, fill `.env`, run `python main.py --all --send`. Send only to yourself.

### In a real company
Contacts would come from a CRM/HR database instead of CSV, reminders from a calendar or ticketing system, SMTP from a company mail service (Microsoft 365, SendGrid, Amazon SES), and the script would run on a server via cron/Task Scheduler instead of your laptop. The code structure stays the same.

### Capture on GitHub
Screenshots (section 13), `outputs/email_report_*.csv`, `outputs/dry_run_preview.txt`, `logs/email_automation.log`, `docs/sample_output.txt`.

### Never upload
- `.env` or any real password / app password
- Real people's names, emails, phone numbers
- `outputs/send_history.csv` from live runs
- Logs from live runs containing real addresses
- Screenshots that show your real email address or inbox

---

## 9. How to Run

| Goal | Command |
|------|---------|
| Fresh dummy data | `python main.py --generate-sample` |
| Dry-run (due reminders) | `python main.py` |
| Dry-run (everything) | `python main.py --all` |
| Simulate a date | `python main.py --as-of "2026-11-25 10:30"` |
| Repeating check | `python main.py --schedule --interval 5` (Ctrl+C to stop) |
| **Live** sending | `python main.py --send` (asks you to type `yes`) |
| Tests | `python -m unittest discover -s tests -v` |

On Mac use `python3`.

**Expected terminal output:** see `docs/sample_output.txt`. You will see one line per email (`DRY_RUN` or `FAILED`) and a final summary with counts per status and reminder.
**Generated:** `logs/email_automation.log` (every event with a timestamp), `outputs/email_report_<timestamp>.csv` (columns: timestamp, reminder_id, contact_id, name, email, subject, mode, status, error), `outputs/dry_run_preview.txt` (the full text of every email).

---

## 10. GitHub Upload Steps

```bash
# one-time Git identity
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"

# inside the project folder
git init
git add .
git status                      # CHECK: .env must NOT be listed
git commit -m "Initial commit: project structure and sample data"

# create an EMPTY repo on github.com (no README), then:
git branch -M main
git remote add origin https://github.com/<your-username>/Email-Automation-Reminder-System.git
git push -u origin main
```

Later changes: `git add .` → `git commit -m "..."` → `git push`.

- **Repo name:** `Email-Automation-Reminder-System`
- **Description:** *Python automation project that sends personalized, scheduled reminder emails from CSV contact lists with dry-run mode, logging and CSV reports.*
- **Topics/tags:** `python` `automation` `email-automation` `smtp` `pandas` `scheduler` `csv` `reminder-system` `student-project` `productivity`
- **Screenshots/output files:** put images in `images/`, commit with `git add images outputs docs`, then reference them in the README.
- **Security checklist:** passwords only in `.env`; `.env` listed in `.gitignore`; share `.env.example` with fake values. If you ever commit a password by accident, **change that password immediately** (deleting the commit is not enough because it stays in history).

---

## 11. README.md

The complete README (overview, problem statement, industry relevance, features, stack, structure, setup, environment variables, how to run, sample output, screenshots, learning outcomes) is in the repository root: `README.md`. Replace `<your-username>` and add your screenshots.

---

## 12. Proof-Building Strategy (6 days)

| Day | Work | Commit | Commit message | Save |
|-----|------|--------|----------------|------|
| 1 | Setup: Python, venv, folders, `.gitignore`, `requirements.txt` | folder skeleton | `chore: initial project structure` | folder screenshot |
| 2 | Contacts CSV and templates | `data/`, `templates/` | `feat: add sample contacts and email templates` | contacts CSV + template screenshots |
| 3 | Personalization, email builder, config | `src/config.py`, `data_loader.py`, `template_engine.py`, `email_builder.py` | `feat: load CSVs and personalize emails` | `dry_run_preview.txt` |
| 4 | Scheduler and sender with dry-run | `email_sender.py`, `engine.py`, `scheduler.py`, `main.py` | `feat: add reminder scheduling and dry-run sending` | dry-run terminal output, schedule output |
| 5 | Logging, reports, tests | `logger_setup.py`, `report.py`, `tests/` | `feat: add logging, CSV reports and unit tests` | log file, report CSV, passing tests |
| 6 | Documentation | `README.md`, `docs/`, `images/` | `docs: add README, guide and screenshots` | GitHub repo preview |

---

## 13. Screenshots / Outputs

| # | Capture | How | Save as |
|---|---------|-----|---------|
| 1 | Project folder | VS Code Explorer with all folders expanded | `images/01_project_folder.png` |
| 2 | Sample contacts CSV | Open `data/contacts.csv` in VS Code or Excel | `images/02_contacts_csv.png` |
| 3 | Email template | Open `templates/webinar_reminder.txt` | `images/03_template.png` |
| 4 | Dry-run terminal output | `python main.py --all` | `images/04_dry_run.png` |
| 5 | Reminder schedule output | `python main.py --as-of "2000-01-01 00:00"` (nothing due) then `python main.py` (some due) | `images/05_schedule.png` |
| 6 | Sent/failed log | Open `logs/email_automation.log`, show a `FAILED` line | `images/06_log_file.png` |
| 7 | Generated report CSV | Open `outputs/email_report_*.csv` | `images/07_report_csv.png` |
| 8 | GitHub repo preview | Your repo page on github.com | `images/08_github_repo.png` |

Before sharing, blur or avoid any real email address or personal data.

---

## Bonus: Interview Preparation

**Explain the project in 30 seconds.** "I built a Python system that reads contacts and reminders from CSV, personalizes emails from templates, schedules them by date and time, sends them via SMTP, and logs every result into a CSV report. It has a dry-run mode for safe testing and prevents duplicate sends."

**Likely questions**

1. **Why dry-run mode?** To test the whole pipeline without side effects. Emailing real people by mistake cannot be undone.
2. **How do you protect credentials?** Environment variables loaded from `.env`, which is git-ignored; `.env.example` has placeholders.
3. **Why STARTTLS / what does it do?** Starts on a plain connection then upgrades to an encrypted one before login, so the password is not sent in clear text. Port 587 uses it; 465 uses implicit SSL.
4. **Why a Gmail App Password?** Google blocks sign-ins with the main password for scripts; an app password is revocable and limited to this use.
5. **How do you avoid duplicate emails?** I record `reminder_id|email` after each live send and skip pairs already present. This is idempotency.
6. **What happens if one email fails?** The exception is caught, retried up to twice with a fresh connection, then logged as `FAILED` with the reason; the run continues.
7. **How does scheduling work?** Each reminder has a datetime; a job compares it to the current time and runs on a timer (`schedule` library). In production I would use cron, Task Scheduler, or a cloud scheduler instead of a long-running script.
8. **How would you scale it?** Database instead of CSV, a queue (Celery/RabbitMQ) for sending, a transactional provider (SendGrid/SES) for deliverability, bounce handling, unsubscribe list, rate limiting.
9. **How did you test it?** Unit tests with `unittest` and `unittest.mock`, patching `smtplib.SMTP` so tests verify behavior without sending anything.
10. **What would you improve?** HTML templates (Jinja2), attachments, a Streamlit dashboard, timezone handling, SQLite storage.
11. **Why pandas for CSVs?** Easy validation, filtering by group, and one-line report export; for tiny files the built-in `csv` module also works.
12. **What are the compliance concerns?** Consent, unsubscribe option, not storing personal data unnecessarily (GDPR / CAN-SPAM style rules).

**Roles this supports:** Python Developer (modular code, testing), Automation Engineer (scheduling, retries, idempotency), Operations/Admin/HR (real reminder workflows), Business Productivity (time-saving, reporting).

**Resume bullet:** *Built a Python email automation system (pandas, smtplib, schedule) that sends personalized scheduled reminders from CSV data, with dry-run testing, duplicate-send protection, logging and CSV reporting; 9 unit tests.*
