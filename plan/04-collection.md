# Plan 04 — Collection runs
Seq: 4/5 · Prev: 03-labeler.md · Next: 05-detection.md
Design ref: README#collection-pipeline-locked
Status: queued · last done: — · next: step 1

- [ ] 1. First recording session: S21 in front of TV, stable framing, full quality,
         continuous capture. Transfer MP4 to the HDD; assign recNNN id.
      done when: a raw recNNN.mp4 sits on the HDD and plays back with audible TV audio
                 and a readable screen.
      reverse:   delete the file; re-record (TV footage is re-recordable).
- [ ] 2. Split the recording (02-splitter), label chunks with the labeler (03),
         back up CSVs to git/Drive.
      done when: every chunk of recNNN has a CSV committed/backed up.
      reverse:   CSVs are additive files; delete/redo. Raw stays untouched.
- [ ] 3. Repeat across channels/times/lighting — many shorter sessions, consciously
         varied (ad-variety risk: don't record the same few spots repeatedly).
      done when: enough distinct recordings to split cleanly by recording into
                 train/val/test (target: 10+ distinct sessions to start).
      reverse:   additive; nothing to undo.
- [ ] 4. Reserve dedicated recordings for live eval that never touch training.
      done when: reserved recordings are listed and excluded from dataset builds.
      reverse:   additive bookkeeping.
