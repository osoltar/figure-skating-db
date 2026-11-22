# Ideas for future updates

## Data
- [ ] Add judges' names from the "Panel of Judges" documents (link J1–J9 to real people)
- [ ] Base value table: import the ISU Scale of Values (one per season) as a reference table, to check printed base values, see how elements are valued across seasons, and calculate values for things like "what if this jump had been fully rotated"
- [ ] Segment date: read it from the "printed:" line in the PDF (check it's reliable, a reprint would carry a later date) and store it on `segments`
- [ ] Nations reference: data/reference/nations.csv mapping each code to the country it represents (e.g. AIN2 → Russia, AIN1 → Belarus), so queries across seasons treat RUS and AIN2 as the same country (needed once pre-2022 seasons are added)
- [ ] Expand scope: Challenger Series, Grand Prix Final, Europeans, Four Continents, Worlds
- [ ] Add previous seasons
- [ ] Add pairs and ice dance
- [ ] Handle old scoring rules (GOE ±3 before 2018, old component names before 2022)
- [ ] Link skaters to their ISU page (isu-skating.com slug)
- [ ] Improve skater matching: PDFs have no birth date, so skaters are matched on first + last name for now; add birth date and handle name changes
- [ ] Name corrections: data/reference/skater_names.csv mapping a name as printed in protocols to the correct first/last name split (e.g. Sophie Jolene VON FELTEN, where "von" ends up in the first name), applied by the loader before matching; can also fix spelling differences between events

## Features
- [ ] Rankings: best elements by GOE, highest PCS, etc.
- [ ] Skater score progression over a season / career
- [ ] Judge analysis (scoring tendencies, national bias)

## Technical
- [ ] Automate PDF downloads instead of downloading by hand
- [ ] Measure load time (parsing vs inserting), then cache parsed PDFs as JSON in data/processed/parsed/ so a rebuild only re-parses new PDFs (delete the cache after changing the parser)
