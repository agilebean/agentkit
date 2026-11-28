---
name: foyer-claim
description: Build a Foyer Global Health reimbursement claim from the receipts of one doctor's visit or one prescription. It finds the day's scans in Evernote, sorts the pages by provider, puts a patient's note page in front that lists each invoice with its price and the total, orders the medical receipt before the prescription and the pharmacy invoices, names the file after the visit date and its amount, and saves it to the claims folder. Use when the user went to a doctor or a pharmacy, asks to file, assemble or sort claim receipts, mentions the claims folder, or asks which scan belongs to which doctor.
---

# foyer-claim

One claim is one PDF per provider. The insurer gets one file per doctor or
prescription, and its first page says what the invoices inside are and what
they add up to, so nobody has to add them up from the scans.

Page order inside the file: the note page, then the medical receipt, then the
prescription, then the pharmacy invoices. The medical receipt comes first
because it names the clinic, the date and the amount the insurer books the
claim under.

## Step 1: find the scans

The scans arrive in Evernote from the Scannable app as notes titled
"Scannable Document". Search with the MCP, never the app by hand:

```
search_notes({query: "Scannable Document", sortBy: "created", clientTimeZone: "Asia/Seoul"})
```

Take the ones created on the visit day. `created:` needs the client time zone,
so pass `Asia/Seoul`; the timestamps returned are UTC, and 14:31 in the note is
05:31Z, which is what the timestamps show.

## Step 2: read every page

Each note holds one PDF. `get_note` lists `resources[]` with the hash; take the
`downloadUrl` from `get_attachment` and download it at once, because the URL
lives five minutes. Render each page to PNG at 150 dpi with PyMuPDF and read
it, page by page. The page types are:

- **Medical receipt** (MEDICAL RECEIPT, 진료비 계산서·영수증): clinic, service date,
  itemized lines, total, physician and licence, clinic stamp.
- **Medical certificate** (MEDICAL CERTIFICATION): the diagnosis codes, the
  treatment given and the proposed treatment. Not every visit produces one.
- **Prescription** (처방전): the issuing clinic under 발행기관, the prescriber's name
  and licence, the medicine lines.
- **Pharmacy statement** (Pharmacy Statement & Receipt (Patient Use), 복약지도,
  약제비 계산서·영수증): the medicine name, the days supplied and the amount paid.
  This page does **not** name the prescriber. The clinic comes from the
  prescription or from the 약제비 계산서's 병원명 line, so pair the pharmacy pages
  with that clinic and never infer it from the medicine.

## Step 3: sort the pages by provider

A day's scans usually hold two providers, and a pharmacy batch can hold
receipts of several earlier prescriptions. Before grouping, check each receipt
against the claims already on file: the same date and amount already inside a
claim is the same receipt, and it stays out, or the insurer pays it twice.
Name the source of that check when reporting, which earlier file or claim.

The physician printed on the receipt and the doctor who wrote the prescription
are sometimes two different people at one clinic. Credit the diagnosis to
whoever signed the certificate, and leave the receipt as it is.

## Step 4: write the note page

Build it with `claim_pdf.py` (in this folder) from a JSON spec; the script lays
out the page and appends the scans in the order the spec lists them:

```
python3 claim_pdf.py spec.json out.pdf
```

```
{
  "rows": [["Patient", "<NAME>, born <YYYY-MM-DD>"],
           ["Clinic", "<clinic, street address>"],
           ["Physician", "<name, MD (license N)>"]],
  "invoices": [["Medical receipt, <treatment>", "<YYYY-MM-DD>", "208,700"],
               ["Pharmacy invoice, <what>", "<YYYY-MM-DD>", "10,000"]],
  "total": "218,700",
  "blocks": ["A paragraph on what the invoices cover.",
             "The follow-up paragraph, when a diagnosis is needed:",
             {"codes": [["H04.11", "Dry-eye syndrome"], ...]},
             "A closing paragraph."],
  "pages": ["receipt.pdf", "prescription.pdf"]
}
```

The page reads, in this order: the title `PATIENT'S NOTE ON THE ENCLOSED
INVOICES`, the patient/clinic/physician rows, the invoice table with one row per
invoice (what it is, its date, its amount), the total in bold, then the
paragraphs. Amounts keep the separator the receipts use, as in 208,700.

One sentence states what the invoices are: one visit, the treatment at the
clinic and the medicine dispensed the same day, or a prescription whose
consultation and filling fall on different days. Say which, with both dates.

**When the visit has no certificate of its own**, take the diagnosis from the
provider's previous claim, which is the same clinic's earlier certificate, and
write the paragraph that says this invoice is a follow-up of that diagnosis.
Name the certificate's date, number and signing physician, then the codes.
Close with the line that the certificate went with the earlier claim, so the
diagnosis is already on file. A claim for a prescription only, such as a
statin refill, needs no diagnosis and gets no code block.

## Step 5: name the file

`YYYY-MM-DD <what> KRW <amount>.pdf`, dated with the **first receipt in the
package**, which is the doctor visit, even when the pharmacy filled the
prescription days later. A claim whose consultation was on 2026-11-24 and whose
medicine was dispensed on 2026-11-27 is named 2026-11-24.

The amount follows the provider's own earlier files, which are in the claims
folder and in `_processed`: a clinic claim has the medical receipt's amount
(the eye clinic's 254860 and 208700), while a claim built from a prescription
and its pharmacy invoices has the sum of its invoices. Look for the provider's
earlier names before choosing, and follow them.

## Step 6: verify

Reopen the PDF and check the page count against the pages you meant to insert,
then render page one and read it: the table, the total and the paragraphs must
all be on it, and nothing may run off the page. Page sizes stay as scanned
(a prescription or a receipt strip is narrower than A4), and a page is never
scaled to fit.

## Step 7: file it

Save both to `~/Documents/Invoices/foyer_claims`. The claims folder keeps what
has not been submitted yet; once a claim is submitted, its file moves to
`~/Documents/Invoices/_processed`, together with the older ones still sitting
in the claims folder. The submission script picks the newest PDF in the claims
folder, so a stale file there is a claim that can be sent twice.

The scanned notes stay in Evernote as they are. The claim PDF duplicates their
pages, and that duplicate is what the insurer receives.

## Report

Say which provider each page went to, the invoice lines and the total, what
stayed out and why (already claimed), and the file names. One line per claim.
