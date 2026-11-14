---
name: date-analysis
description: Analyze the recording of one of Chaehan's dates and write the note (Evernote notebook Affinity, or Hanji) - the turning point of the date and the talk that led to it, her feelings for him, sex and past relationships decoded from indirect Korean, how they changed since the earlier meetings, how the date compares with his other dates, and what he can do better and why, in a friend's plain words with verbatim quotes and their times. Reads the transcript Chaehan exported into the Affinity folder on Drive, and MacWhisper's database only when no such file exists. Use when Chaehan asks to analyze a date or a date recording, types /date, or asks to "evernote the date".
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

**The transcript.** Chaehan exports each date's transcript into the Affinity
folder on Drive, named like the recording:
`~/Library/CloudStorage/GoogleDrive-chaehan.so@virtualfriend.chat/My Drive/1 Projects/Affinity/<recording title>.md`.
That file, or the file he names, is the transcript. Chaehan, 2026-11-14: "do
not transcribe the audio again, the transcript is at ..." and "why don't you
conclude that must be in the skill to check first the transcript existence".
MacWhisper (the app installed as "Whisper Transcription", bundle
com.goodsnooze.MacWhisper) is reached only when no such file exists, and then
only through `mw_transcript.py`, which copies the app's database file and
reads the copy; it never opens the app and never transcribes.

## What Chaehan wants from it

Chaehan, 2026-11-12, after the first date-3 note: "no quality over quantity ...
it should not go through the big5 personality traits and collect as much as
possible but look what is the most apparant given she is a 37y korean woman ...
it should tell mostly about that [sex and past relationships], about what she
reveals about her feelings to me, how this changed or progressed over the last
dates, and how good it compares to other dates, and what i can do better and why."

Chaehan, 2026-11-14, on the second date-3 note: "i said to analyze the sex
topic and it made it much too prominent in position ... neither the old nor the
new captured the extremely important and deep conversational points preceding
that revelation which changed her whole attitude towards me, as after that she
allowed me holding her hand."

So the note answers six things, in this order, and leaves out what serves none:

1. **The turning point.** The moment her attitude toward him changed, the talk
   that led to it from where its subject first came up, and what she did after
   it. A turn is an event across the other five points, so it is found by step
   7, never by a topic code. When nothing in the date changed how she treated
   him, the note says so in one sentence.
2. **Her feelings for him.** What she reveals about how she feels toward him,
   in her words.
3. **The progression.** How her feelings and the topics below changed from her
   first meeting with him to this one, from the earlier notes on her.
4. **Sex and past relationships, hers and his.** Analyzed in full and placed
   here, after her feelings: every line on them, his own included, verbatim
   with its time and decoded. Where she stands between the two ends he guards
   against: too open (much experience, one-night stands, open relationships)
   and too conservative (no sex before marriage). Korean manners keep this
   indirect; `traits.md` has the decoding table.
5. **The comparison.** How this date compares with his other dates, from
   `memory/dating.md` (the other J Noble women and earlier dates).
6. **What he can do better, and why.** Each point tied to a moment of the date
   and to what it costs or gains him with her, judged by what she said and did
   after that moment.

Children, his hard condition (`memory/partner-search.md`), go in the Takeaway
whenever the date touched them. Her personality is read only for the three to
five things most apparent in a 37-year-old Korean woman on a third meeting:
how she shows interest indirectly, how she sets limits, what she expects of
marriage and family; never a run through the Big Five. A thing this date did
not show is left out, and the section holds only what it showed.

Every claim rests on a Korean quote with the time of its turn; the analysis is
in English, in the register of `register.md`. Quality decides: a quote earns
its place only when it carries one of the six points.

## Steps

Work in a build folder, `$TMPDIR/date-<YYYY-MM-DD>-<name>/` (call it `B`).
`S=~/Software/Prototypes/agentkit/skills/date-analysis/scripts`.

1. **Transcript.** First `ls` the Affinity folder above for the recording's
   title, and take any path Chaehan gave. When the file exists, it is the
   transcript, and steps 2 and 3 run `md_turns.py` on it; MacWhisper is not
   read. The file needs its timestamps (`*05:17:42*` under each speaker line);
   when it has none, ask Chaehan to export it again with timestamps. Only when
   no file exists, `python3 $S/mw_transcript.py list` shows MacWhisper's
   recent sessions; when the recording reads "transcribed False", the app is
   still working, so wait and check again every few minutes.
2. **Name the speakers.** `python3 $S/md_turns.py "<file>" --speakers` (from
   MacWhisper: `mw_transcript.py speakers "<session>"`) prints each speaker's
   turns and longest turns. Chaehan is the man who talks about KUBS, design
   thinking, AI, Germany and his travels; she is the woman whose life the
   record describes. The app splits one voice across several numbers, worst in
   a loud bar, and Chaehan's export can still file a line of hers under his
   name: read every line by its words. A speaker goes to "Other" only when
   most of its turns are about menus, prices or serving. A speaker whose turns
   answer Chaehan about her life, about him or about the two of them is mapped
   to her name. A mixed speaker keeps its own number (`Speaker 3`), so each of
   its turns is read on its own. Write the mapping into `B/speakers.txt` with
   one reason per speaker; on 2026-11-11 two of her questions sat under a
   speaker described there as video subtitles, and a later run dropped them.
3. **Turns and counts.**
   `python3 $S/md_turns.py "<file>" --out B/transcript.md --stats B/stats.md --map "Speaker 4=Other" ...`
   (from MacWhisper: `mw_transcript.py export` and `stats` with the same
   `--map`). The transcript has one line per timed block,
   `T0123 [1:02:03] Jiyoung: ...`; the time in brackets is how every quote is
   cited.
4. **Chaehan's record.** Read her section of `memory/dating.md`, the hard
   conditions in `memory/partner-search.md`, and the earlier notes on her that
   the record names. His own words about this date, when he gave them, go into
   `B/his.md` exactly as he wrote them; the note quotes them under "Your
   feedback". Touch is not in the audio: when his words say nothing about it,
   ask him with the question tool whether she let him hold her hand or come
   closer, and when he felt her change. The note states touch only from his
   words. A line in the transcript about an earlier moment ("손은 안
   잡았어요") never states how the evening ended (failure 210 in socrates
   `memory/agentic_ai.md`). Without his answer, the note says nothing about
   touch.
5. **Read the whole transcript and collect.** Read it in parts of at most 300
   turns (a larger part keeps one model step silent past the runner's 120 s
   idle limit, which ended the 2026-11-12 rebuild of date 2), from the first
   turn to the last; the end of a long date often holds the most personal talk.
   For each part, append to `B/evidence.md` only lines that serve the six
   points: `[time] CODE: "Korean quote" - what it shows`, with codes `TURN`
   (one of the signs in step 7), `SEX`, `PAST` (past relationships), `FEEL`
   (her feelings for him), `KIDS`, `BETTER` (a moment he could have handled
   better) and `NOTE` (one of the few things most apparent about her). His own
   lines on sex and past relationships are collected like hers. Read every
   turn under a staff label: in a stretch where nobody orders, most of them are
   hers, and on 2026-11-11 half her turns in the most personal hour sat there.
6. **Sex, past relationships and children, decoded.** Search the whole
   transcript for the words of `traits.md`'s decoding table (`rg -n` with all
   of them), read 15 turns before and after every hit, and add what the parts
   missed. Turns under a staff label whose words are hers count as hers.
7. **Find the turning point.** A turn spans many turns and several topics, so
   the parts and the codes cut it into separate lines; this step puts it back
   together. First list in `B/turn.md` every place with these signs, from the
   `TURN` lines and a search of the whole transcript:
   - a sentence about how she is changing, with him named as the cause:
     `-해줘서`, `덕분에`, `-고 있는 중`, `-었는데 ... 지금은`, `갑자기 확 깨닫게`,
     `처음으로`;
   - a fear, hurt or secret she says she has kept for a long time and tells him
     now: `오랫동안`, `상처`, `겁`, `무서워`, `사실`, `말 못해요`;
   - talk about the two of them and this meeting: `우리`, `번째 만나니까`,
     `가까워지면`, `멀어지려고`, `앞으로 우리가`;
   - his words and ideas coming back in her mouth, above all in her resolution
     form `-야겠다` applied to something he proposed;
   - her questions about his ideas (`어떻게 ...요?`, `언제부터 ...?`): his long
     turn after such a question answers her;
   - her longest turns of the night, which `stats.md` and the transcript show;
   - what follows within minutes: a plan she proposes, touch words (`손`,
     `손잡기`, `잡아`), his report of touch from step 4.
   Pick the place where her attitude toward him changed. When his words name
   the moment, that place is it. Then read backward from it, in one piece and
   across the part borders of step 5, to where its subject first came up,
   which can be an hour or more before her line. A deictic word in the turn
   ("이런 얘기", "그런 거") is followed back to the talk it points at. Then read
   forward to what she did next. Print that stretch whole with
   `sed -n '/^T<first> /,/^T<last> /p' B/transcript.md` and read every line,
   the lines under Other first: where nobody is ordering, they are hers, and
   MacWhisper also joins a question of hers to the front of his answer inside
   his turn. Write the arc into `B/turn.md` as numbered steps in time order,
   one line each: who said what, with its time, and what it moved. When no
   place shows these signs, write that one sentence, and the section of the
   note holds that sentence alone.
   - **The arc keeps every question she asks him in the stretch**, with the
     answer he gave, and every admission he makes about himself (a fear, a
     failure, a doubt): what he admits is often what lets her answer in kind.
   - **A fear or hurt she tells is named by what or whom it concerns**, in her
     words, from the line where she says it. The arc and the note quote that
     line; "a fear she kept" without its object leaves the turn empty.
   - **A long turn of his is judged by what she asked before it and what she
     said and did after it.** Talk share and turn length never judge it on
     their own; on 2026-11-11 two notes listed as the moment he lost her the
     turn that answered her question and led to her opening up.
   - **A line inside the arc is read as part of the arc** before any topic code
     is given to it: a line that names children or sex while she answers his
     question about touch is first an answer about touch.
   - **A view he quotes to reject it is not his.** In "사람 그렇게
     생각해요. ..." the words after the frame are what other people think, and
     they are quoted as such.
8. **Write `B/draft.md`, one section per write** (append each section as its
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
     marked "(her voice, filed under staff)" after its time, and one filed
     under his name "(her voice, filed under your name)". A line that speaks of
     her life in the first person (`내가 ... 무서워한다거나`), or answers his
     question, is hers whatever its label.
   - **An example is not an event.** What she offers after `예를 들어서`,
     `만약에` or `이런 거` is a case she imagines, and it is never written as
     something she did.
   - **A time, a duration or a role stays as she said it.** "4시에 만나서 10시"
     is quoted, never turned into a clock time by arithmetic; a man in her
     story keeps the role she gives him, and a role she never names is not
     added.
   - **A garbled line is quoted, never retold.** When the words around a line
     do not make its sense clear, the note quotes the clear words or leaves the
     line out.
   - **The turning point is told as a story**, in paragraphs and in time order
     from `B/turn.md`, the way a friend retells what happened: what she said,
     what you answered, what she did next. Her words are quoted where they
     move the story on, and the paragraphs hold no bullets. What followed is
     told as what she did next, each with its time; it is never said to have
     caused everything after it.
9. **Check.** `python3 $S/date_check.py B/draft.md --transcript B/transcript.md [--verbatim B/his.md]`
   until it prints PASS. It fails robotic wording (with every contrast frame),
   a Korean quote without its time or not found in that turn, a missing
   section, a note over 1500 words outside its quotes, fewer than three quotes
   on sex and past relationships, a turning point written as bullets, and one
   sentence opening used four times or more. Then read the draft once aloud in your head against `register.md`.
   Each failure line names its fix, so the marker lists and the lint scripts
   are never read: on 2026-11-14 a run spent four minutes in them and stopped
   on the runner's idle limit before it had read the transcript.
10. **Write the note.** The evernote skill, section "A text you wrote":
   `python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_build.py init B/note --as-is B/draft.md --title "<title>" --notebook "Affinity" --person "<her name>" [--verbatim B/his.md]`,
   without the draft's `# title` line. `--person` lets her lead a sentence, as
   Chaehan chose on 2026-11-12 ("she may lead"): the gate takes she, her and her
   name as a subject beside you; all its other checks stay, the cap of seven
   list items per section among them (Chaehan, 2026-11-12: quality over quantity). On a gate failure, edit `B/note/draft.md` and run
   `note_build.py next B/note` until PASS. Then in opencode `note_build.py write B/note` and its one execute call; from
   Claude Code `note_test.py --write B/note --out B/run`. A photo for the top
   goes above the first heading as `![name](</path/photo.jpg>)`.
11. **Record.** Propose one dated line for her section of `memory/dating.md`
    (the date, how long, the verdict, the note's title) and write it when
    Chaehan agrees.



## The note's sections

At most 1500 words. A section holds at most seven bullets.

1. `## Takeaway`: three bullets: how she feels about you, with the turning
   point when there was one; what changed since the last meeting with her; the
   one thing to do better next time. Children here whenever the date touched
   them. Sex here only when something about it changed on this date.
2. `## Your feedback`: only when Chaehan gave his words, as he wrote them.
3. `## The turning point`: the arc of step 7 as a story in paragraphs, from
   where its subject came up to what she did after it, and in two or three
   sentences what it means for you. When nothing changed how she treated you,
   one sentence that says so.
4. `## Her feelings for you`: what she revealed, in her words, outside the
   turning point, grouped under colon subheads on their own lines (rule 106):
   what she said about you, what she asked you, what she offered or planned
   without being asked, and what cooled and when. Chaehan, 2026-11-14: the
   Date3-old note "had meaningful substructure in Her interest in you". A
   group the date did not show is left out; the groups hold at most seven
   bullets together.
5. `## How it changed since your first meeting`: her feelings, sex and past
   relationships on each earlier meeting with her, against this one.
6. `## Sex and past relationships`: her lines and yours, decoded; where she
   stands between too open and too conservative; what is still unknown.
7. `## Compared with your other dates`: this date against the other women in
   `memory/dating.md`, on interest, openness and what was settled.
8. `## What you can do better`: two to four points, each with the moment, what
   it cost or would gain judged by what she did after it, and why.
9. `## What stands out about her`: three to five things most apparent in her,
   each with one or two quotes.
10. `## Source`: the recording, its length, the speaker mapping, and that quotes
    come from an automatic transcript.
