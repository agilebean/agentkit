---
name: date-analysis
description: Analyze the recording of one of Chaehan's dates and write the note (Evernote notebook Affinity, or Hanji) - the turning point of the date and the idea that led to it as one train of thought, her feelings for him, sex and past relationships decoded from indirect Korean, how they changed since the earlier meetings, how the date compares with his other dates, and what he can do better and why, in a friend's plain words with verbatim quotes and their times. Reads the transcript in the Affinity folder on Drive, and when there is none exports it from Whisper Transcription with Chaehan and her named; from Claude Code, DeepSeek runs it and Claude Code checks the result. Use when Chaehan asks to analyze a date or a date recording, types /date, or asks to "evernote the date".
---

# Date analysis

One note per meeting, in the Evernote notebook **Affinity**, titled like the
recording: `YYYY-MM-DD <Her name> Date<N>` ("2026-11-10 Mina Lee Date2"),
where N counts the meetings with this one woman. Chaehan, 2026-11-12: "name it
like the transcript (date 2, not second date)".

**Trigger.** `/date <recording>` (for example `/date 2026-11-11 Mina Lee Date3`)
writes to Evernote; `/date <recording> Hanji` writes to Hanji instead, with
`note_build.py init --dest hanji` (the hanji skill; Hanji has no Affinity
notebook, so the note goes to "Chaehan's Life", as the date-1 note did).

**The transcript.** Each date's transcript is a Markdown file named like the
recording, beside its audio in the Affinity folder on Drive or in a subfolder
of it (Chaehan files a woman's dates under her name):
`~/Library/CloudStorage/GoogleDrive-chaehan.so@virtualfriend.chat/My Drive/1 Projects/Affinity/`.
A file there, or the file he names, is the transcript. Chaehan, 2026-11-14: "do
not transcribe the audio again, the transcript is at ..." and "why don't you
conclude that must be in the skill to check first the transcript existence".
When no file exists, the agent exports it from Whisper Transcription, the app
that transcribed the recording, with `mw_transcript.py md` (step 1). Chaehan,
2026-11-20: "can you export the transcripts as md file yourself from
macwhisper ... label at least the first two speakers". The app's bundle and
folders carry its developer's name for it, MacWhisper
(com.goodsnooze.MacWhisper), and so do the script names; a note or a reply
calls it Whisper Transcription, the name on Chaehan's Mac. The script copies
the app's database and reads the copy; it never opens the app and never
transcribes.

**Who runs it.** DeepSeek runs every step (agentkit RULES.md 245: DeepSeek
does the work, and a fix goes into its instructions, never into its output).
In opencode, `/date` loads this skill into the agent. In Claude Code, `/date`
hands the whole run to DeepSeek and only checks what comes back; Claude Code
never runs steps 1 to 10 itself. Chaehan, 2026-11-20: "cant you send it to
deepseek as well and just check and correct the output so we can save tokens
processed by you?"

1. Ask Chaehan the touch question of step 4 when his words do not answer it,
   and write his words into `B/his.md`, since the run cannot ask him.
2. Copy `brief.md` beside this file into `B/brief.md` and fill its fields in
   angle brackets. When a note of that title exists, fetch it into
   `B/base.md` and keep the `--guid` clause (the note is rebuilt in place);
   otherwise delete the clause.
   Start `python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_test.py --brief B/brief.md --out B/run1 --expect B/idea.md B/turn.md B/draft.md --budget 2400`
   in the background. A run the idle limit cut continues with
   `--session <its session>` and a brief that says to continue.
3. Check what the run left against `B/stretch.md` and `B/transcript.md`:
   `B/idea.md` (the idea as a claim, her question about it, the steps he
   counts as steps, his words in her mouth), and in the turning point of
   `B/note/draft.md` every span of time it states against the times it cites,
   every act of hers against a line that shows it, a case she gave after
   `예를 들어서` or `만약에` written as an event, and her key line quoted whole.
   On 2026-11-17 a full run passed both gates with four such errors.
4. Send the fixes as one brief to the same session (`--session`): DeepSeek
   edits `B/note/draft.md` and runs the gate again. A class of error that
   recurs goes into this skill or `date_check.py`.
5. Write with `note_test.py --write B/note --out B/run-write`, then read the
   note back.

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

Chaehan, 2026-11-16, on the third date-3 note: the turning point "has no clear
train of thought. instead it recites the conversation like a normal summary";
"the most important content was the principle i told her that led her to ask"
her question at 4:08:38; and his answer to it was written with "no
understanding of the whole concept in three steps".

So the note answers six things, in this order, and leaves out what serves none:

1. **The turning point.** The moment her attitude toward him changed, and the
   talk that changed it as one train of thought: the idea that was told, what
   the other asked about it, the answer in its steps, and what she did with
   it. The talk is traced from where its subject first came up. A turn is an
   event across the other five points, so it is found by step
   7, never by a topic code. When nothing in the date changed how she treated
   him, the note has no turning point section.
2. **Her feelings for him.** What she reveals about how she feels toward him,
   in her words.
3. **The progression.** How her feelings and the topics below changed from her
   first meeting with him to this one, from the earlier notes on her. A first
   meeting has none, and its note has no such section.
4. **Sex and past relationships, hers and his.** Analyzed in full and placed
   here, after her feelings: every line on them, his own included, verbatim
   with its time and decoded. Where she stands between the two ends he guards
   against: too open (much experience, one-night stands, open relationships)
   and too conservative (no sex before marriage). Korean manners keep this
   indirect; `traits.md` has the decoding table. When neither of them spoke
   about sex or past relationships, the note has no such section: talk about
   marriage or children is not sex, and children go in the Takeaway.
5. **The comparison.** How this date compares with his other dates, from
   `memory/dating.md` (the other Noble women and earlier dates).
6. **What he can do better, and why.** Each point tied to a moment of the date
   and to what it costs or gains him with her, judged by what she said and did
   after that moment.

Children, his hard condition (`memory/partner-search.md`), go in the Takeaway
whenever the date touched them. Her personality is read only for the three to
five things most apparent in a 37-year-old Korean woman on a third meeting:
how she shows interest indirectly, how she sets limits, what she expects of
marriage and family; never a run through the Big Five. A thing this date did not show is left out, and the section holds only what it showed.

A section the date gave nothing for leaves the note, heading and all; it is
never a heading over a sentence saying that nothing happened. Chaehan,
2026-11-20, on the note of the 2026-11-19 date, which kept "The turning point"
over "You felt no change in her" and "Sex and past relationships" over
marriage talk: "sections turning point and sex should not be here if not
spoken about this is common sense!" (failure 230).

Every claim rests on a Korean quote with the time of its turn; the analysis is
in English, in the register of `register.md`. Quality decides: a quote earns
its place only when it carries one of the six points.

## Steps

Work in a build folder, `$TMPDIR/date-<YYYY-MM-DD>-<name>/` (call it `B`). In a shell command, set
`B=<the folder's full path>` and write `$B/...`, never a bare `B/...`: a bare `B/` names a
folder that does not exist, and the runs of 2026-11-17 and 2026-11-20 made one or crashed on it.
`S=~/Software/Prototypes/agentkit/skills/date-analysis/scripts`.

1. **Transcript.** First search the Affinity folder tree for the recording's
   title (`find "<Affinity folder>" -name "<recording>.md"`), and take any
   path Chaehan gave. When the file exists, it is the transcript, and steps 2
   and 3 run `md_turns.py` on it. When no file exists, export it:
   `mamba run -n socrates python $S/mw_transcript.py md "<recording>" --her "<her first name>"`
   writes `<recording>.md` beside the recording's audio, in the format of
   Chaehan's own export, and names the two speakers who talk most. A name the
   app already holds is kept; two unnamed speakers are told apart by voice
   pitch, the lower voice being Chaehan's (right in six of six recordings he
   had labelled, 32 to 98 Hz apart, test of 2026-11-20). Its last line says
   how it named them; speakers it leaves unnamed are named in step 2 by their
   words. `python3 $S/mw_transcript.py list` shows the recording names; one
   that reads "transcribed False" is still being transcribed, so wait and
   check again every few minutes. A file of his without timestamps
   (`*05:17:42*` under each speaker line) is replaced for the run by the same
   command with `--out B/export.md`, which holds the same lines with their
   times: the 2026-11-15 export carried none.
2. **Name the speakers.** `python3 $S/md_turns.py "<file>" --speakers` prints
   each speaker's turns and longest turns. The two who talk most come named
   from his export or from step 1; check them by their words. Chaehan is the man who talks about KUBS, design
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
   `python3 $S/md_turns.py "<file>" --out B/transcript.md --stats B/stats.md --map "Speaker 4=Other" ...`.
   The transcript has one line per timed block,
   `T0123 [1:02:03] Mina: ...`; the time in brackets is how every quote is
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
   missed. Turns under a staff label whose words are hers count as hers. When
   no hit is about sex or past relationships, `B/evidence.md` says so in one
   line and the note has no such section.
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
   Whisper Transcription also joins a question of hers to the front of his answer inside
   his turn. Before any line is quoted, write `B/idea.md` from that stretch in
   your own words, with no quote in it: what he was telling her (or she him),
   as a claim someone could disagree with; what the other asked about it; the
   answer in its steps; and where the idea comes back in the other's mouth.
   Then write the arc into `B/turn.md` as the numbered steps of that thought,
   one line each: what the turn added to the idea (states it, asks about it,
   explains a step, hands it to her, says it back, applies it to herself), who
   said it, and its time. A turn that adds nothing to the thought stays out of
   the arc, however personal it is. When no place shows these signs, `B/turn.md` says so in one line, and the
   note has no turning point section.
   - **The stretch is read for what was said, in a step of its own.** One pass
     over the whole evening does not hold it. On 2026-11-14 the hour of the
     turn got one read among six, the arc was written from the evidence list
     in 11 s, and the idea that led to her question at 4:08:38 stood in none
     of its 23 lines; asked on that stretch alone "what did he tell her?", the
     same model named the idea in a minute (test of 2026-11-16). So `sed` the
     stretch into `B/stretch.md` and write `B/idea.md` from that file alone,
     before the arc and before any rule of the section is read: what the talk
     was and what he told her, what each step he counts is, and where his
     words come back in her mouth. On 2026-11-17 a full run that did so named
     the idea and gave the counted steps as steps, and its slowest step took
     104 s; most earlier runs called the counted steps three doubts.
   - **An idea is written as its content, never as the act of saying it.** "He
     admitted his fear" names an act, and "you gave her four minutes: language,
     the two girlfriends, and the fear under it" a list of topics. The content
     is the claim: his fear is his own to get over first, and he must not wait
     for the other person to take it away [4:06:00]. Whoever reads the
     sentence can explain the idea to a third person, or it is rewritten.
   - **Steps he counts stay steps.** `첫째`, `두번째`, `세 번째` in one answer are
     the steps of one method, each named by what it does (name the doubts;
     find the bad experience behind each; catch the fear at the root and admit
     it), never three items of one list.
   - **His idea is put together from all his turns in the stretch.** He speaks
     Korean as a learner and the transcriber garbles it (`시민초코덜` for
     symptoms, `인종해야` for 인정해야), so the idea stands in no single clean
     line. It is written in English, and a garbled word it rests on is given
     beside its reading.
   - **His words are followed into her mouth.** The same verb or noun said by
     her (`넘어가다`, `깨다`, `겁`) marks where she asks about his idea, says it
     back, and applies it to herself; these lines are the joints of the arc.
   - **The arc keeps every question she asks him about the idea**, with what
     he answered, and every admission he makes about himself (a fear, a
     failure, a doubt): what he admits is often what lets her answer in kind.
     An admission made inside an idea is told as part of that idea.
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
   - **A garbled line of hers is quoted, never retold.** When the words around
     a line do not make its sense clear, the note quotes the clear words or
     leaves the line out. His own idea is the exception of step 7: it is put
     together from all his turns, and he can check it himself.
   - **The turning point is told as a train of thought**, from `B/idea.md` and
     `B/turn.md`, the way a friend explains what happened between the two of
     you: what changed, the idea that did it in two or three sentences, what
     she asked, the answer in its steps, how she said it back and applied it
     to herself, and her line. It runs in paragraphs with no bullets, in time
     order where the thought runs in time. A quote stands where a step of the
     thought rests on it, one per step at most. Talk that adds nothing to the
     thought (a stretch she showed him, a concert, the ride home) goes to "Her
     feelings for you" or stays out. What followed is told as what she did
     next, each with its time; it is never said to have caused everything
     after it.
9. **Check.** `python3 $S/date_check.py B/draft.md --transcript B/transcript.md [--verbatim B/his.md]`
   until it prints PASS. It fails robotic wording (with every contrast frame),
   a Korean quote without its time or not found in that turn, a missing
   section the note always has, a turning point, progression or sex section
   that opens by saying nothing happened, a note over 1500 words outside its
   quotes, a turning point written as bullets or holding more than 14 quotes, and one
   sentence opening used four times or more. Then read the draft once aloud in your head against `register.md`.
   Each failure line names its fix, so the marker lists and the lint scripts
   are never read: on 2026-11-14 a run spent four minutes in them and stopped
   on the runner's idle limit before it had read the transcript.
10. **Write the note.** The evernote skill, section "A text you wrote":
   `python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_build.py init B/note --as-is B/draft.md --title "<title>" --notebook "Affinity" --person "<her name>" [--verbatim B/his.md]`,
   with the draft's `# title` line deleted first: `--as-is` writes the file as it stands, so a
   kept H1 repeats the note's title in the body (failure 225). `--person` lets her lead a sentence, as
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

1. `## Takeaway`: at most three bullets: how she feels about you, with the
   turning point when there was one; what changed since the last meeting with
   her, from the second meeting on; the one thing to do better next time. Children here whenever the date touched
   them. Sex here only when something about it changed on this date.
2. `## Your feedback`: only when Chaehan gave his words, as he wrote them.
3. `## The turning point`: the train of thought of step 7 in paragraphs: what
   changed, the idea that did it, her question, the answer in its steps, what
   she did with it, and in two or three sentences what it means for you. Only
   when something changed how she treated you; otherwise the note has none.
4. `## Her feelings for you`: what she revealed, in her words, outside the
   turning point, grouped under colon subheads on their own lines (rule 106):
   what she said about you, what she asked you, what she offered or planned
   without being asked, and what cooled and when. Chaehan, 2026-11-14: the
   Date3-old note "had meaningful substructure in Her interest in you". A
   group the date did not show is left out; the groups hold at most seven
   bullets together.
5. `## How it changed since your first meeting`: her feelings, sex and past
   relationships on each earlier meeting with her, against this one. Only
   from the second meeting on.
6. `## Sex and past relationships`: her lines and yours, decoded; where she
   stands between too open and too conservative; what is still unknown. Only
   when either of you spoke about them.
7. `## Compared with your other dates`: this date against the other women in
   `memory/dating.md`, on interest, openness and what was settled.
8. `## What you can do better`: two to four points, each with the moment, what
   it cost or would gain judged by what she did after it, and why.
9. `## What stands out about her`: three to five things most apparent in her,
   each with one or two quotes.
10. `## Source`: the recording, its length, the speaker mapping, and that quotes
    come from an automatic transcript.
