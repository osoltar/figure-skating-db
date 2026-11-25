# Ideas for future updates

## Data
- [x] Add judges' names from the "Panel of Judges" documents (link J1–J9 to real people)
- [x] Base value table: import the ISU Scale of Values (one per season) as a reference table, to check printed base values, see how elements are valued across seasons, and calculate values for things like "what if this jump had been fully rotated"
- [x] Segment date: read each segment's day and time from the schedule on the results index page (already read by download.py) and store it on `segments`; more reliable than the "printed:" line in the PDF
- [ ] Nations reference: data/reference/nations.csv mapping each code to the country it represents (e.g. AIN2 → Russia, AIN1 → Belarus), so queries across seasons treat RUS and AIN2 as the same country (needed once pre-2022 seasons are added)
- [ ] Expand scope: ~~Challenger Series~~ (done), NHK Trophy, Grand Prix Final, Europeans, Four Continents, Worlds
- [ ] Add previous seasons
- [x] Add pairs and ice dance
- [x] Full base value check: combinations and sequences (sum of parts), +REP, dance elements with a level per partner (CiStW + CiStM), pattern dance key points, combined lifts, invalid elements; then turn it into a loader validation like TES/PCS
- [ ] Download the Scales of Values automatically (US Figure Skating hosts them)
- [ ] Pairs and dance details: pattern dance key points one by one, lift groups and types, each lift of a combined lift, Advanced Novice / junior pattern dance sequences (FO1Sq4...) if lower levels are ever added
- [ ] Handle old scoring rules (GOE ±3 before 2018, old component names before 2022)
- [ ] Link skaters to their ISU page (isu-skating.com slug)
- [ ] Improve skater matching: PDFs have no birth date, so skaters are matched on first + last name for now; add birth date and handle name changes
- [ ] Name corrections: data/reference/skater_names.csv mapping a name as printed in protocols to the correct first/last name split (e.g. Sophie Joline von FELTEN, where "von" ends up in the first name), applied by the loader before matching; can also fix spelling differences between events
- [ ] Find out what the `+RFE` flag means (not in the TP Handbook 2026/27, Communication 2788, the protocol legend or the ISU abbreviation list); valued like +REP (80%) in the protocols
- [ ] Find out what `P` means in the Info column (seen on 1A+2A*+Eu*+3S<*+SEQ+RFE, Budapest Trophy)

## Features
- [x] Rankings: best elements by GOE, best spinners, most used jumps
- [ ] Skater score progression over a season / career
- [x] Judge analysis: GOE compared with the rest of the panel, home judge difference
- [x] Recompute GOE and component scores from the judges' marks (trimmed mean), store each judge's GOE in points
- [ ] Judge analysis on component marks
- [ ] Technical panel analysis: rotation and edge calls by technical specialist / controller

## Technical
- [x] Automate downloads (download.py, from results_url in competitions.csv)
- [ ] Measure load time (parsing vs inserting), then cache parsed PDFs as JSON in data/processed/parsed/ so a rebuild only re-parses new PDFs (delete the cache after changing the parser)
