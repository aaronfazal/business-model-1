# Carpenter Website Template

One template, one settings file per client. Every client site is built the same way, so a new site takes a couple of hours, not days.

## What each site includes
- Click-to-call phone number and "Get a quote" button always visible
- Services with optional "from" prices (using the client's own rates)
- Recent work photo gallery
- Real customer reviews and a link to their Google profile
- A three-step "how it works" section
- Areas covered (helps local Google searches)
- Quote request form
- Hidden business details for Google (structured data) so the site supports their Google Business Profile
- Works on phones, which is where most customers will see it

## Setting up a new client
1. Copy `clients/example-joinery` to `clients/<client-name>`
2. Fill in `site.json` from their intake form ([../03-client-intake.md](../03-client-intake.md))
3. Replace the placeholder images in `images/` with their photos and update the file names in `site.json`
4. Paste in 3 real Google reviews
5. Build: `python3 build.py clients/<client-name>` (Jarvis can run this for you)
6. Fix anything the build warns about
7. Upload the `dist/` folder to hosting and connect their domain

## The quote form
Static sites need a form service to deliver enquiries by email. Sign up for a form service such as Formspree, create a form for the client, and paste its address into `form_endpoint`. If it's left blank, the form opens the visitor's email app instead, which works but loses some enquiries.

## Hosting
Free options include GitHub Pages and Netlify. The client buys their own domain (e.g. from a UK registrar) so they always own it.

## Before launch checklist
- [ ] No "Sample review" left in
- [ ] No placeholder photos left in
- [ ] Phone, email and address correct
- [ ] Form tested: submit an enquiry and check it arrives
- [ ] Checked on a phone
- [ ] Website link added to their Google Business Profile
