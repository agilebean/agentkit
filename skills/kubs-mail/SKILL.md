---
name: kubs-mail
description: Read the KUBS mailbox chaehanso@korea.ac.kr and turn it into a ranked list of what is worth attending, in-person socializing first, each row carrying its venue and its exact registration link. Use when the user says "check my kubs email", "anything from korea.ac.kr", "KUBS 메일", or asks what is happening at the university and which events are worth going to.
---

# KUBS mailbox → what to attend

The mailbox is a broadcast channel, not a conversation: measured 2026-11-05,
114 messages in 30 days, every one an institutional notice from a
`korea.ac.kr` office, zero senders from outside the university in 365 days, and
an empty sent folder. So do not hunt for personal mail; report that finding in
one line and spend the effort on the events. Never read the primary
`chaehan.so@gmail.com` in its place.

## Step 1 — token

Only the Korea University token reads this mailbox:

    ~/.google/oauth_token_korea.json

The bundled script already points at it. `invalid_grant` means the token is
dead: stop and report it for `chaehanso@korea.ac.kr`, re-consent with the
command in the `gmail-setup` skill, and never fall back to the default token.

## Step 2 — list

    python ~/.agents/skills/kubs-mail/scripts/mail.py list "newer_than:14d -in:spam -in:trash" 80

Widen to `newer_than:30d` when the table comes back thin. Two lines per message:
headers first, then the snippet. "Look for personal mail" becomes one query —
`-from:korea.ac.kr` over a year; an empty result is the answer.

## Step 3 — read the body, not the subject

    python ~/.agents/skills/kubs-mail/scripts/mail.py show <id>

The subject line says 특강 or 세미나 for both modes. In-person is decided by the
venue line: a room, a hall, a building (`백주년기념관 국제원격회의실`,
`SK미래관 최종현홀`, `하나스퀘어 B115`, `문과대학 서관 B110`). Online is decided by
`온라인`, `Zoom`, `실시간`, `메타버스` in the 장소 field. A hybrid event counts as
in-person only if it names a room and offers a lunch or a reception.

## Step 4 — register links

    python ~/.agents/skills/kubs-mail/scripts/mail.py links <id>

Take the URL from the href, not from the visible anchor text — many mails read
"신청하기" or "참석 조사 링크" while the address sits only in the link. The
mailbox's own unsubscribe (`ems.korea.ac.kr/trace/reject_confirm`) is filtered
out; ignore anything else that is not a form, a `zoom.us` room, or an event
site. If there is no link, the mail says walk-in — write `없음 (walk-in)`, never
a guessed address.

## Step 5 — rank by who is in the room, then by socializing yield

The user's standing aim is contact with PhD candidates and postdocs whose
papers he could contribute data science to, where the subject is psychological
or AI. That makes the audience line of the invitation the first key, and the
venue the second:

1. **Invitation names 대학원생 / 신진연구인력 / 박사후** — his population. Go.
2. **Room of people** — booths, a lunch, a reception, named networking breaks,
   a prize draw. Second only to the audience above.
3. **Faculty room** — 교원, 의료원 연구자, 연구자. Worth the lunch, not the
   afternoon.
4. **Lecture in a hall** — a seat, a speaker, a walk out. Only when the subject
   is his (AI, psychology, cognitive science, Germany/Europe, startups).
5. **Online** — one line below the table as watch-later, never a table row when
   he asked for socializing.

Read the 대상 line, not the subject: 정신건강특강 reads as his domain and is
addressed to 학생·직원 (undergraduate-heavy); Lab to Life reads as generic and
is the one invite that names 대학원생 from 28 universities. Measured 2026-11-05:
that inversion is the whole point of this step.

## Step 6 — the table

Columns, in this order: `When | Event | Who is in the room | Tags | Where | Register`.

Two language rules, measured against the event he has to search for later:

- **The event name and the venue keep their Korean exactly as the mail writes
  them, with the English in parentheses after it**: `제14회 KU-KUM 콜로키움 (14th
  KU-KUM Colloquium)`, `하나스퀘어 B115 멀티미디어룸 (Hana Square multimedia room
  B115)`. The Korean is the search key in the university's own pages and in the
  mail archive; a translation alone cannot be found there. Everything else —
  When, Who, Tags, the notes below — is English.
- **Register carries a clickable link, not a URL to copy.** In an Evernote note
  that is a markdown link `[RSVP form](https://…)`; in chat the bare address is
  the only clickable form. Anchor text names what the link accepts (`RSVP form`,
  `registration form`, `labtolife.kr`), never "here".

- `When` — `Thu 11/12 12:30–13:30`, weekday included, because a wrong weekday is
  the mistake that costs an event.
- `Who is in the room` — the 대상 and program lines read straight: 대학원생, 교원,
  의료원, 학생, or `대상 명시 없음`. This is the column that decides whether he
  goes, so it never borrows a guess from the subject.
- `Tags` — two or three plain words that give the event's vibe and shape at a
  glance: `showcase, booths, prize draw`; `lunch, small room, clinicians`;
  `papers, roundtable, formal`; `lecture, undergrads, Pepero`. They are not a
  second telling of the topic and not angle-bracketed genre labels; the subject
  already sits in the event name, and the tags answer "what is it like to be in
  that room".
- `Where` — Korean venue with the English in parentheses, as above.
  **Korea University's Seoul campus (Anam-dong, Seongbuk-gu) carries no district
  marker** — 하나스퀘어, SK미래관, 백주년기념관, 백주년기념삼성관, 문과대 서관,
  운초우선교육관 are all there. A KU building in another part of Seoul is marked
  with its gu (the medical campus in Jongno-gu reads `의대본관 (종로구)`); any
  off-campus venue reads `장소 (구)`.
- `Register` — `[RSVP form](https://…)` for a single form, or two links joined by
  `·` when a festival site sits beside a competition site. No form and no signup
  in the body reads `none, walk-in`, never a guessed address.

Rows sort by the Step 5 order, then by date. Below the table: the clash line when
two in-person events overlap, and a deadline line for anything registering today
or tomorrow. Close with the files changed (usually none).

## Step 7 — the details block

The table is the scan layer; under it a `## Details` section carries one bold
entry per event, named in Korean with the English in parentheses, saying what
actually happens: the run of the day with hours and rooms, the speakers with
their institutions, the host office, what the registration asks, and the fact
that changes the decision (a missing session topic, food banned in the room, the
Zoom password). Two to four sentences each, no bullet nesting.

The row that reads thinnest in the table is the one that needs this most: the
KU-KUM row cannot show a session title because the mail has none, so the entry
names the host office, the two campuses the lunch joins, the hybrid room, the
password and the fact that the subject is unannounced. Detail he could not
derive from the table is the test for keeping a sentence here.


## Known venues, for shortening

| Mail writes | Write |
|---|---|
| 백주년기념관 국제원격회의실 | 백주년기념관 국제원격회의실 |
| 백주년기념삼성관 국제원격회의실 | 백주년기념삼성관 |
| SK미래관 1층 최종현홀 & 로비(인재림) | SK미래관 최종현홀·인재림 |
| 하나스퀘어 멀티미디어룸(B115호) | 하나스퀘어 B115 |
| 운초우선교육관 203호 강당 | 운초우선교육관 203 |
| 문과대학(서관) B110호 | 문과대 B110 |

## Recorded readings

- The scan has a twin in Evernote: `2026-11-05 Korea University Events Worth Attending` in the
  **2026 Events** notebook. Campus-event notes go there, not into KUBS Admin.
- 2026-11-05: 정신건강특강 "AI에게 마음을 털어놓아도 될까" — in person (백주년기념삼성관
  국제원격회의실, 11/10 15:00), registration `forms.gle/JJTeFcN6dYwu7Gzj9`, but a lecture
  hall with Pepero handed out at the door: tier 2.
- 2026-11-05: BK21 K-3MT 결승 + Lab to Life 연구페스티벌 — in person (SK미래관 최종현홀·인재림,
  11/11 09:00–17:00), `labtolife.kr` for the festival and `bk21-k-3mt.kr` for the
  competition, 28 universities, booths, career tables, prize draw, 외국인 대학원생
  지원 부스. The only invite in the inbox that names 대학원생: first.
- 2026-11-05: KU-KUM Colloquium — in person with lunch (하나스퀘어 B115, 11/12 12:30),
  RSVP `forms.cloud.microsoft/r/QVv7wKveVj`, but addressed to 교원 and 의료원
  researchers and carrying no session title: a faculty lunch, second.
