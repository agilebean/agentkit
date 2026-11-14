---
name: date-analysis
description: Analyze the recording of one of Chaehan's dates and write the note (Evernote notebook Affinity, or Hanji) - sex and past relationships decoded from indirect Korean, her feelings for him, how they changed since the earlier meetings, how the date compares with his other dates, and what he can do better and why, in a friend's plain words with verbatim quotes and their times. Reads the transcript straight from MacWhisper ("Whisper Transcription"). Use when Chaehan asks to analyze a date or a date recording, types /date, or asks to "evernote the date".
---

# Date analysis

One note per meeting, in the Evernote notebook **Affinity**, titled like the
recording: `YYYY-MM-DD <Her name> Date<N>` ("2026-11-10 Jiyoung Kim Date2"),
where N counts the meetings with this one woman. Chaehan, 2026-11-12: "name it
like the transcript (date 2, not second date)".

**Trigger.** `/date <recording>` (for example `/date 2026-11-11 Jiyoung Kim Date3`)
writes to Evernote; `/date <recording> Hanji` writes to Hanji instead, with
`note_build.py init --dest hanji` (the hanji skill; Hanji has no Affinity
notebook, so the note goes to "Chaehan's Life", as the date-1 note did).

**The transcription app.** MacWhisper is the app installed as "Whisper
Transcription" (bundle com.goodsnooze.MacWhisper): one app, two names. Every
recording Chaehan drops on it is in its database, so step 1 always checks it
first, before looking for an exported file.

## What Chaehan wants from it

Chaehan, 2026-11-12, after the first date-3 note: "no quality over quantity ...
it should not go through the big5 personality traits and collect as much as
possible but look what is the most apparant given she is a 37y korean woman ...
it should tell mostly about that [sex and past relationships], about what she
reveals about her feelings to me, how this changed or progressed over the last
dates, and how good it compares to other dates, and what i can do better and why."

So the note answers five things, in this order, and leaves out what serves none:

1. **Sex and past relationships, hers and his.** Every line on them, his own
   included, verbatim with its time and decoded. Where she stands between the
   two ends he guards against: too open (much experience, one-night stands,
   open relationships) and too conservative (no sex before marriage). Korean
   manners keep this indirect; `traits.md` has the decoding table.
2. **Her feelings for him.** What she reveals about how she feels toward him,
   in her words.
3. **The progression.** How 1 and 2 changed from her first meeting with him to
   this one, from the earlier notes on her.
4. **The comparison.** How this date compares with his other dates, from
   `memory/dating.md` (the other J Noble women and earlier dates).
5. **What he can do better, and why.** Each point tied to a moment of the date
   and to what it costs or gains him with her.

Children, his hard condition (`memory/partner-search.md`), go in the Takeaway
whenever the date touched them. Her personality is read only for the three to
five things most apparent in a 37-year-old Korean woman on a third meeting:
how she shows interest indirectly, how she sets limits, what she expects of
marriage and family; never a run through the Big Five.

Every claim rests on a Korean quote with the time of its turn; the analysis is
in English, in the register of `register.md`. Quality decides: a quote earns
its place only when it carries one of the five points.

## Steps

Work in a build folder, `$TMPDIR/date-<YYYY-MM-DD>-<name>/` (call it `B`).
`S=~/Software/Prototypes/agentkit/skills/date-analysis/scripts`.

1. **Transcript.** `python3 $S/mw_transcript.py list` shows MacWhisper's
   recent sessions (the "Whisper Transcription" app). When the recording reads "transcribed False", MacWhisper is
   still working: wait and check again every few minutes (the log in
   `~/Library/Containers/com.goodsnooze.MacWhisper/Data/Library/Application Support/MacWhisper/Logs/`
   names the session when it finishes). A transcript Chaehan exported as a file
   instead goes straight to step 3.
2. **Name the speakers.** `python3 $S/mw_transcript.py speakers "<session>"`
   prints each speaker's talk time and longest turns. Chaehan is the man who
   talks about KUBS, design thinking, AI, Germany and his travels; she is the
   woman whose life the record describes. Short speakers with a few lines are
   staff or neighbours: map them to "Other". Two speakers that both sound like
   her are mapped to her name. Write the mapping into `B/speakers.txt` with
   one reason per speaker.
3. **Export and count.**
   `python3 $S/mw_transcript.py export "<session>" --out B/transcript.md --map "Speaker 1=Chaehan" --map "Speaker 2=Jiyoung" ...`
   and the same with `stats --out B/stats.md`. The transcript has one line per
   turn, `T0123 [1:02:03] Jiyoung: ...`; the time in brackets is how every
   quote is cited.
4. **Chaehan's record.** Read her section of `memory/dating.md`, the hard
   conditions in `memory/partner-search.md`, and the earlier notes on her that
   the record names. His own words about this date, when he gave them, go into
   `B/his.md` exactly as he wrote them; the note quotes them under "Your
   feedback".
5. **Read the whole transcript and collect.** Read it in parts of at most 300
   turns (a larger part keeps one model step silent past the runner's 120 s
   idle limit, which ended the 2026-11-12 rebuild of date 2), from the first
   turn to the last; the end of a long date often holds the most personal talk.
   For each part, append to `B/evidence.md` only lines that serve the five
   points: `[time] CODE: "Korean quote" - what it shows`, with codes `SEX`,
   `PAST` (past relationships), `FEEL` (her feelings for him), `KIDS`, `BETTER`
   (a moment he could have handled better) and `NOTE` (one of the few things
   most apparent about her). His own lines on sex and past relationships are
   collected like hers.
6. **Sex, past relationships and children, decoded.** Search the whole
   transcript for the words of `traits.md`'s decoding table (`rg -n` with all
   of them), read 15 turns before and after every hit, and add what the parts
   missed. Turns under a staff label whose words are hers count as hers.
7. **Write `B/draft.md`, one section per write** (append each section as its
   own step; one write of the whole note runs silent past the runner's 120 s
   idle limit). The sections below, in this order, in the register of
   `register.md`. Every section opens with one sentence that tells Chaehan its
   point. Rules from the runs of 2026-11-12:
   - **Read the turn a quote answers.** Before saying what she reacted to, read
     his turn before hers. "그런 것까지 생각했는지 몰랐어요" [5:36:35] answered
     his four minutes on age and swimming, and was once written up as her
     reaction to children.
   - **Dates and comparisons come from a source.** A date, a duration or a
     comparison with an earlier meeting stands in the transcript,
     `memory/dating.md` or an earlier note; when none holds it, leave it out. A
     relative day ("내일") stays in its quote with the day it was said.
   - **A plan agreed on the date is written as agreed**, never as still ahead.
   - **A quote from a turn under a staff label** that is hers by its words is
     marked "(her voice, filed under staff)" after its time.
8. **Check.** `python3 $S/date_check.py B/draft.md --transcript B/transcript.md [--verbatim B/his.md]`
   until it prints PASS. It fails robotic wording (with every contrast frame),
   a Korean quote without its time or not found in that turn, a missing
   section, a note over 1500 words outside its quotes, fewer than three quotes
   on sex and past relationships, and one sentence opening used four times or
   more. Then read the draft once aloud in your head against `register.md`.
9. **Write the note.** The evernote skill, section "A text you wrote":
   `python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_build.py init B/note --as-is B/draft.md --title "<title>" --notebook "Affinity" --person "<her name>" [--verbatim B/his.md]`,
   without the draft's `# title` line. `--person` lets her lead a sentence, as
   Chaehan chose on 2026-11-12 ("she may lead"): the gate takes she, her and her
   name as a subject beside you; all its other checks stay, the cap of seven
   list items per section among them (Chaehan, 2026-11-12: quality over quantity). On a gate failure, edit `B/note/draft.md` and run
   `note_build.py next B/note` until PASS. Then in opencode `note_build.py write B/note` and its one execute call; from
   Claude Code `note_test.py --write B/note --out B/run`. A photo for the top
   goes above the first heading as `![name](</path/photo.jpg>)`.
10. **Record.** Propose one dated line for her section of `memory/dating.md`
    (the date, how long, the verdict, the note's title) and write it when
    Chaehan agrees.



## The note's sections

At most 1500 words. A section holds at most seven bullets.

1. `## Takeaway`: three bullets: where she stands on sex and how she feels
   about you; what changed since the last meeting with her; the one thing to do
   better next time. Children here whenever the date touched them.
2. `## Your feedback`: only when Chaehan gave his words, as he wrote them.
3. `## Sex and past relationships`: her lines and yours, decoded; where she
   stands between too open and too conservative; what is still unknown.
4. `## Her feelings for you`: what she revealed, in her words.
5. `## How it changed since your first meeting`: sex, past relationships and
   her feelings on each earlier meeting with her, against this one.
6. `## Compared with your other dates`: this date against the other women in
   `memory/dating.md`, on interest, openness and what was settled.
7. `## What you can do better`: two to four points, each with the moment, what
   it cost or would gain, and why.
8. `## What stands out about her`: three to five things most apparent in her,
   each with one or two quotes.
9. `## Source`: the recording, its length, the speaker mapping, and that quotes
   come from an automatic transcript.
