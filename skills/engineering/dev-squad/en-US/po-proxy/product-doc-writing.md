# Writing product documentation — PO directive

## Principle

Product documentation is written for a PERSON who has never seen the product,
not for an AI agent with the decision history open beside it.
If a passage only makes sense to someone who already knows what it is about, it has failed.

## The test

Before publishing any paragraph of product doc, ask:
"If I showed only this paragraph to an outsider, with nothing else,
would they understand what the product does and why?"
If the answer depends on opening another document first, rewrite it.

## Rule on decision codes (D-XX, J-XX, etc.)

Traceability codes (D-07, J-12...) NEVER carry meaning
on their own inside an explanatory sentence. There are two correct ways to use them:

1. As a LINK at the end of a paragraph that already explained itself:
   "...at sale time it uses the official WhatsApp Business API, which is more
   stable at scale. [→ full rationale in [[Closed decisions]]#D-07]"

2. Never as part of the subject or predicate of the sentence:
   ❌ "single channel per decision D-07"
   ❌ "per D-02, the product is called..."

## Rule on coupling to external/third-party state

A document about product X must never state the **current state** of an
entity external to X (parent brand, sister platform, another product of the same
group) — only X's **relationship** with that entity. External state changes for
reasons that have nothing to do with X, and each external change would force going back
to edit X's doc just to keep it from becoming outdated — unnecessary coupling
between documents that should evolve independently.

❌ Wrong (current state of a third party, becomes a lie the day it changes):
"AgentsTrail is the umbrella brand — today there is still no other active
product under that brand."
→ The day a second product is launched under AgentsTrail, that
sentence in Recepta's doc becomes false, and someone has to remember to come back
here to fix something unrelated to Recepta itself.

✅ Right (relationship with the third party, timeless — never needs correction):
"AgentsTrail is the umbrella brand, designed to host other vertical
AI agents in the future. Recepta is the first product launched under that
brand." (both facts are permanent: the brand's intent and the order of
launch never change, even if the catalog grows)

### How to recognize the pattern

Sentences with "today", "currently", "not yet", "for now" describing the
state of something that **is not the subject of the document** are a warning sign.
Ask: "if this count/state changes tomorrow, will anyone remember to
come back to exactly this document to fix it?" If the answer is "no,
probably not" — the fact should not be here. Either it becomes a
timeless statement about the relationship, or it points to the external source of truth (the
entity's own documentation), never duplicating its state here.

## Rule that every pain point cited needs a traceable solution

If a document lists customer pain points/problems (a "the problem" section,
a "why this matters"), each item on that list needs an
**explicit and findable** answer in the product — not implicit, not merely suggested
by another similar capability, and not buried pages later in a
"differentiators" section the reader may never get to.

The test: for each pain point on the list, could a salesperson, using only this
document, point in one sentence to the exact feature that solves
it? If the answer is "they would have to infer it" or "it is described only
way up front, with no link back to the pain" — it is a real argumentative
gap. A prospective customer will ask exactly that ("and the hole
left in the schedule when someone cancels at the last minute?"),
and the salesperson needs a ready answer, not a deduction.

Recommended form: a table or short list right after the list of pain points,
linking each pain point to the mechanic that solves it — there is no need to re-explain the
mechanic in detail there (that already lives elsewhere in the document or in its own
doc), just close the loop visually.

## Rule on mechanic consistency across similar journeys

When a mechanic is established for ONE specific scenario (e.g. "every
time Bia learns something new from a human, she asks whether it is worth it only
for now or whether it can apply always, and the 'always' goes through approval before
becoming a rule"), that same mechanic usually needs to hold **everywhere
else in the documentation where the same kind of moment happens** — not
only where it was originally specified.

The typical mistake: the mechanic is born well defined in one journey (e.g. J-43, "the
secretary corrects Bia"), but a sibling journey, which triggers the same kind of
learning through a different path (e.g. J-31, "Bia asks because
she does not know what to do"), is described in a more simplistic way ("the guidance
becomes memory", without the same one-off-or-always question) — as if it were a
different mechanism, when in practice it should be the same filter.

When closing any new decision or mechanic, ask: "what other
journeys/documents trigger this same kind of moment, and do they already
describe the same behavior, or were they left behind?" Trace and align
before considering the topic closed — same principle as the "reflect
changes in related documents" rule of the review process, but applied
during the *creation* of a new mechanic, not only when correcting text.

## Rule on proper names and new concepts

Every proper name in the product (persona, brand, feature) needs, on its
first appearance in each document, a sentence saying WHAT it is and
WHY it exists — not just that it exists.

❌ "under the AgentsTrail umbrella (agentstrail.dev)"
✅ "Recepta is the first product of an umbrella brand called
    AgentsTrail, designed to host other vertical agents in the
    future." (explains what it is and why it exists, without stating the current
    state of a third party's catalog — see the coupling rule above)

## Rule on ordering: capabilities before implementation/roadmap

The main body of a product document first tells WHAT the
product DOES and WHAT VALUE it delivers — without interruptions about "how this is
delivered over time" (phases, versions, MVP × commercial, rollout).

Implementation/roadmap detail CAN and SHOULD exist, but as a
separate, clearly labeled block, AFTER the flow of capabilities — never
interleaved in the middle of the explanation of what the product does.

Format of the separate technical block:
> **Technical note — {subject}:** {technical/roadmap content}.
> [→ link to decision/detail, if any]

❌ Wrong (interrupts the flow of capabilities with phase detail):
"She answers on WhatsApp (in the pilot via an unofficial integration, at sale
via the official API), schedules appointments, remembers the history..."

✅ Right (complete flow of capabilities, technical note afterwards):
"She answers on WhatsApp, schedules appointments, remembers the history...
[end of the capabilities paragraph]

**Technical note — WhatsApp connection roadmap:** in the pilot..."

## Critical rule — relationship links between documents

Every reference to another document, decision, section or concept defined
elsewhere MUST be a navigable link on the target platform —
never plain text citing the document/section name without a link.

This applies both to cross-references between documents and to
anchors within the SAME document (e.g. "see section X" further down on
the same page).

### Syntax per platform

| Platform | Link syntax |
|---|---|
| Local Markdown (Obsidian) | `[[Document Name]]` or `[[Document Name#Section]]` |
| ClickUp Doc | direct link to the target page/section inside the workspace |
| Confluence (or another future platform) | the platform's native link to the target page/anchor |

When publishing/syncing a local Markdown document to an external
platform, the Markdown `[[...]]` wikilinks MUST be converted to
that platform's native link format — never left as plain
`[[Name]]` text nor removed.

## Rule on the content of decision records (the target of the D-XX link)

A link `[[Closed decisions]]#D-07` only fulfills its purpose if, when clicking,
the reader finds the full context — not just the outcome. Each
decision entry must record:

1. **Question** — what was open before the decision (the doubt or
   trade-off that motivated the discussion)
2. **Decision** — what became valid
3. **Reason** — why this option beat the alternatives
4. **Impact** — which documents/areas change because of it

A record without the **Question** field forces the reader to guess which
problem was being solved — the same "writing for someone who already knows
what it is about" flaw that this skill exists to avoid, just
transferred into the decisions document itself.

## Process — when the user asks for review/correction of existing product documentation

When the request is of the type "review and fix the documentation following
this directive" (not writing from scratch), follow this process, not a mechanical
"find & replace":

1. **First of all, ensure a clean worktree.** If there is any
   unrelated pending commit in the repository, commit it
   first (grouped by theme), so that the documentation review commits
   stay isolated and reviewable on their own.
2. **Reload this skill and the directives accumulated in the conversation** before
   touching any file — including running `recall-directives`
   if the conversation is long or has been compacted, so as not to lose
   an adjustment the PO asked for that fell out of the visible context window.
3. **Read linearly, the way a person would.** Follow the actual
   reading order of the document (do not jump to the end, do not process by
   search-and-replace). For each block of text, evaluate it against this skill's
   criteria before deciding whether to touch it or not.
4. **Reflect changes in related documents.** An adjustment in one
   document almost always requires the same adjustment (or an
   equivalent one) in documents that cite the same concept, decision or
   proper name. Trace and adjust the related ones before considering the
   topic closed — do not leave the same problem solved in one place and
   pending in another.
5. **Commit partially, by theme, as you go** — do not
   accumulate the entire review in a single giant commit. Each closed
   theme (one document, or a small group of strongly
   related documents) becomes a commit.
6. **No rush.** Analyze each block of text carefully before
   deciding on the fix. It is preferable to go slower and not forget
   anything than to apply quickly and leave a hole.
7. **Create new content when necessary.** If, during reading, it becomes
   clear that a page, a section or a technical note block is missing for the documentation to be
   complete and coherent with these criteria, create it — there is no need to
   ask permission to fill a gap that the quality directive itself requires.
8. **At the end, resync** the pages actually changed on the
   external platform in use (e.g. ClickUp), not the whole set —
   only what actually changed.

## Calibration reference

Read the public product documentation of renowned SaaS products (Stripe, Linear,
Intercom) as a yardstick: they write for the reader to decide whether
to buy, not for the next engineer to trace a decision. Product
doc is not a changelog or an ADR.

## Checklist before publishing/reviewing a product page

- [ ] No decision code (D-XX) appears outside a link
- [ ] Every proper name cited has a "what it is / why it exists" sentence
      on its first appearance in the document
- [ ] The document's opening paragraph passes the outside-reader test
- [ ] No sentence looks copied from a decision note or changelog
- [ ] No phase/version/rollout detail appears inside the paragraph
      that describes product capabilities
- [ ] Every technical/roadmap detail is in a separate block labeled
      "Technical note —", positioned after the main flow
- [ ] Every mention of another document is a link, not plain text with the name
- [ ] Every mention of a specific section (own or of another doc) links
      directly to that anchor, not just to the top of the document
- [ ] When publishing outside Obsidian, every wikilink was converted to the
      native link syntax of the target platform (ClickUp, Confluence)
- [ ] No broken links (document/section renamed without updating whatever
      points to it)
- [ ] Every linked decision entry (D-XX) has the four fields:
      Question, Decision, Reason, Impact
- [ ] No sentence states the current state ("today", "not yet", "for
      now") of an entity external to the document's subject (parent brand,
      sister product, third-party platform) — only the timeless relationship with it
- [ ] Every pain point listed in a "problem" section has an explicit
      and findable solution in the document, not just implicit or distant
- [ ] Every new mechanic (e.g. "learns something and asks whether it is a
      permanent rule") was checked against the other journeys/documents that
      trigger the same kind of moment, and all describe the same behavior
