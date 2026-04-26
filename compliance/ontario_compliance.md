# Ontario Compliance — READ BEFORE LAUNCH

**You are based in Ontario. This is not generic advice — it is specific to your jurisdiction.**

## The three layers of risk

### 1. AGCO (Alcohol and Gaming Commission of Ontario)
- Regulates all iGaming (sports betting) in Ontario via iGaming Ontario
- Governs what affiliates and marketers can and cannot do
- Key rule: advertising to Ontario residents can only promote AGCO-registered operators

### 2. Competition Bureau Canada
- Deceptive marketing enforcement under the Competition Act
- A fabricated track record, fake testimonials, or fake expert persona = actionable
- Max penalty: $10M (first offense) / $15M (subsequent) for corporations

### 3. PIPEDA (Personal Information Protection and Electronic Documents Act)
- Applies to any personal data you collect (newsletter emails, payment info)
- Requires privacy policy, consent, breach notification

## The transparency-brand model avoids the worst risks, but doesn't eliminate them

SharpSignals is structured as a **media/analytics brand that shows its work publicly**. This is a materially different legal posture than a tipster selling paid picks, because:

1. Free public picks + transparent log = journalism/content, not gambling product
2. Paid newsletter sells **analysis/methodology/education**, not locked predictions
3. Affiliate revenue comes from AGCO-registered operators (who bear the gambling-service risk)

That said, you still need to comply with the rules below.

## Sportsbook affiliates — Ontario-facing content

**Only promote AGCO-registered operators to Ontario audiences.**

Current AGCO-registered sportsbooks (verify current list at igamingontario.ca before use):
- PROLINE+ (OLG)
- DraftKings Ontario
- FanDuel Ontario
- bet365 Ontario
- BetMGM Ontario
- Caesars Ontario
- Rivalry
- theScore Bet (PENN Entertainment)

**Promoting non-AGCO operators to Ontario residents is a regulatory violation.** If audience is international, different rules apply per jurisdiction — safest default: Ontario audiences only see AGCO-registered links.

## Required disclaimers — every public-facing post

Minimum text that must appear on every IG post, Telegram post, Reel, YouTube video, and newsletter:

> **18+ only. Analytical content for entertainment — not betting advice. Gambling can be addictive. If you or someone you know needs help, call ConnexOntario at 1-866-531-2600 or visit connexontario.ca.**

For Reels/video with voiceover: also include spoken version of the 18+ and helpline line at start OR end.

For affiliate links specifically, add:

> "This link is an affiliate link. We may earn a commission from new account signups. This does not affect our analysis or pick selection."

## Banned language (auto-check in compliance.py)

Never use anywhere:

- `lock` (as in "lock of the day")
- `guaranteed` / `guarantee`
- `sure thing` / `sure bet`
- `can't lose` / `100% winner`
- `fixed` / `fixed match`
- `inside info` / `insider info`
- `rigged game`
- `secret tip`
- `exclusive pick`

Replace with neutral language: "model pick", "higher-conviction signal", "value opportunity", "positive-EV selection".

## Paid newsletter — structuring for compliance

The paid Substack must sell:
- ✅ Methodology deep-dives
- ✅ Model explanations
- ✅ Weekly analytics reports
- ✅ Bankroll management education
- ✅ Historical deep-dives / research
- ✅ Data visualizations

Must NOT sell:
- ❌ Locked/exclusive picks not also posted publicly
- ❌ "VIP predictions"
- ❌ Anything positioned as specific gambling advice for a fee

If ALL picks are also published publicly on IG at the same time as to newsletter subs, the paid product is analysis/media — which is much cleaner legally.

## Age verification

- IG: built-in for 18+ accounts
- Substack: optional age-gate; add to signup form
- Telegram: add "By joining, you confirm you are 18+" to channel description

## Record-keeping for your own protection

Keep:
- Every pick's full metadata (the JSON logged by pick_logger)
- Server logs of when each pick was posted (proves timestamping)
- Screenshots of disclaimers on each post (automated monthly)
- All affiliate signup screenshots (proves they are AGCO-registered when used)

Retention: 7 years (Canadian standard for marketing records).

## Terms of Service + Privacy Policy

Needed before you take any paid subscriber. Templates:

- ToS: adapt from Substack's generic template + add "No betting advice provided" + "18+ only" + "Use at own risk" language
- Privacy Policy: PIPEDA-compliant template; discloses analytics (Google Analytics, IG/Meta pixels), email list, payment processor (Stripe), data retention

Budget ~$150 for a Canadian lawyer to review your ToS + Privacy before paid launch. Worth every penny.

## If you want to run Meta ads (post-week 4)

- Meta gambling policy requires the advertiser to hold or be authorized by a gambling license in the target jurisdiction
- As an AGCO affiliate (not operator), you can run ads promoting **yourself as a content/analysis brand** — NOT ads promoting specific sportsbooks, unless the sportsbook is also the advertiser
- Submit for Meta's gambling advertising review before spending: https://www.facebook.com/business/help/gambling-ads
- Budget: allow 2–4 weeks for approval

## Red-flag checklist (pre-launch)

- [ ] Domain registered, privacy-protected
- [ ] ToS + Privacy Policy published
- [ ] 18+ disclaimer on every surface (IG bio, newsletter footer, site footer)
- [ ] ConnexOntario helpline on every post template
- [ ] Affiliate links all point to AGCO-registered operators
- [ ] No banned language anywhere in templates
- [ ] Compliance.py runs on every automated post
- [ ] Picks log is public and shows ALL picks including losses
- [ ] No testimonials unless 100% real + written-consent on file
- [ ] No celebrity/athlete images (right-of-publicity)
