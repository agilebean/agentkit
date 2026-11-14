# How a date note sounds

Chaehan, 2026-11-12, on the note of 2026-11-10: "your task was to make deepseek
make the analysis in a clearly human wording - but you still have lots of
robotic wordings like took no exit, mechanisms, contrasts (and had not), her own
line is closed".

Write the note the way a perceptive friend who heard the whole recording would
tell Chaehan about it over dinner. Every sentence has a person as its subject,
an everyday verb, and a fact from the transcript. Say what she did and said,
then what it tells him about her. No figure of speech: a person's view is never
a line, a door, a position or a stance; a date never has exits, tests or
signals; a talk never has mechanisms, functions or modes.

The test for each sentence: would Chaehan say it aloud to a friend who asked
"how was it?" If he would say it differently, write it his way.

`scripts/date_check.py` fails the figures below mechanically
(`date_markers.tsv`), and the shared contrast frames as well. Anything the
check misses that fails the test above is still a failure.

## Robotic sentences from the 2026-11-10 note, and the plain version

| Robotic | Why it fails | Plain |
| --- | --- | --- |
| You gave it 8.5 hours, lunch into night, and took no exit. | "Exit" is a figure; nobody left anything. | You stayed together 8.5 hours, from lunch until late at night, and neither of you tried to end it. |
| Her own line is closed. | A line that is closed is a picture, and the reader must translate it. | She would not want an open relationship herself. |
| Your turns mostly explain a mechanism. | "Mechanism" is lab talk about a conversation. | You mostly explained how things work: how mezcal is made, why breathing calms you. |
| She had wanted to ask how open you are and had not. | The clipped "and had not" sounds like a report. | She had wondered how open you are about relationships but did not dare to ask. |
| The remaining asymmetry is not volume but function. | Contrast frame and two analyst nouns. | You talked about as much as she did. You explained things, and she brought up new subjects. |
| You passed the two tests she ran under the conversation. | She ran no tests; "passed" turns a date into an exam. | She asked you two things that mattered to her, and she liked both answers. |
| Her complaint about most people is the mirror of it. | "Mirror" makes the reader work out the link. | She also said what bores her in most people: they like things without knowing why. You always say why. |
| Your AI work is the one subject in her family's language. | "Her family's language" is a riddle. | Her brother and her uncle work in science and AI, so your work is something her family understands. |
| That life cannot move, which is the shape your plan has to meet. | "Shape" and "meet" are pictures. | She will not leave Songpa, so any plan with her has to work from Seoul. |
| The date produced nothing on either. | A date does not produce. | You still do not know whether she wants children or how many years she has to have them. |
| What would reverse this reading. | Analyst frame. | You would think again if she routes her messages through the manager again, or says no to children. |
| A short sober baseline. | Lab word for a meeting. | Meet her once in daytime without alcohol. |
| It is the one answer that makes everything else either worth building or moot. | Abstract frame, "moot". | If she does not want children, nothing else matters, so ask early. |

## Small rules that keep it human

- Name her by her name or "she", and Chaehan as "you".
- Say times as times of day or hours into the date ("in the fifth hour", "at the
  last bar"), and cite the quote's turn time in brackets after the quote.
- Numbers stay: hours, minutes of talk, counts of questions. Each number comes
  with what it is compared with.
- One idea per sentence. A sentence over 25 words is split.
- No "not X but Y", "rather than", "instead of", "although", "even though",
  "yet". Say each fact on its own.
- Korean quotes stay in Korean; the rest is English.
