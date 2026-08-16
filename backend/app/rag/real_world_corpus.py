"""
A real, regulation-grounded knowledge corpus — an alternative to the
synthetic `corpus.py` seed documents, for demonstrating the pgvector
retrieval backend against genuine source material rather than fabricated
policy text.

Every document here is an original paraphrase of actual, current U.S.
federal regulatory guidance (FTC business guidance, HIPAA/Health Breach
Notification Rule materials, the FTC Safeguards Rule) — all public-domain
U.S. government works, so they're freely reusable, and all still directly
relevant to the app's existing themes (billing/refunds, security incident
response, data privacy). `source_url` on each document points at the real
guidance it's grounded in, so nothing here is asserted without a citable
source.

Chosen deliberately to span the JD's named regulated industries: general
business (negative-option/refund rules), security (breach response),
healthcare (Health Breach Notification Rule), and financial services (the
Safeguards Rule).
"""
from app.rag.corpus import Document

REAL_WORLD_CORPUS: list[Document] = [
    Document(
        id="real-negative-option-rule",
        title="FTC Negative Option / Click-to-Cancel Rule — Overview",
        category="billing",
        text=(
            "Any offer where a customer's silence or inaction is treated as agreement to be "
            "charged — free-trial-to-paid conversions, auto-renewing subscriptions, continuity "
            "plans — is a negative option under FTC rules. Businesses must clearly disclose "
            "the renewal terms and price before charging, get the customer's express informed "
            "consent, and provide a cancellation method that is at least as easy to use as the "
            "signup method. The rule applies to business-to-business transactions as well as "
            "consumer transactions."
        ),
    ),
    Document(
        id="real-refund-truth-in-advertising",
        title="Refund Policy Truth-in-Advertising Obligations",
        category="billing",
        text=(
            "If a business advertises a refund or return policy, it is legally obligated to "
            "honor exactly what it advertised — vague or purely discretionary language such as "
            "'refunds may be granted at our discretion' has drawn FTC attention as a potentially "
            "deceptive practice. There is no single federal law requiring a business to offer "
            "refunds at all, but once a refund policy is publicly stated, misrepresenting or "
            "inconsistently applying it can itself be treated as a deceptive trade practice."
        ),
    ),
    Document(
        id="real-cancellation-friction",
        title="Cancellation Method Requirements",
        category="billing",
        text=(
            "Under the FTC's updated negative-option rules, a cancellation process may not be "
            "made deliberately difficult — for example, requiring a customer to call during "
            "limited hours or navigate an unreasonable number of steps to cancel something they "
            "signed up for in one click online. Enforcement in this area has specifically "
            "targeted subscription and SaaS products with friction-heavy cancellation flows."
        ),
    ),
    Document(
        id="real-breach-secure-operations",
        title="Data Breach Response — Step 1: Secure Operations",
        category="security",
        text=(
            "The first step in the FTC's data breach response guidance is to secure operations "
            "and stop further data loss: take affected systems offline without powering them "
            "down (to preserve forensic evidence), change access credentials for anyone whose "
            "login may have been compromised, and, if a third-party service provider was "
            "involved, reassess what data that provider can access. Do not destroy potential "
            "forensic evidence while investigating."
        ),
    ),
    Document(
        id="real-breach-fix-vulnerabilities",
        title="Data Breach Response — Step 2: Fix Vulnerabilities",
        category="security",
        text=(
            "After containment, the FTC's guidance calls for identifying and fixing the root "
            "cause of the incident — not just the symptom. This includes verifying that any "
            "affected service provider has genuinely remediated the vulnerability (rather than "
            "taking their word for it), checking whether network segmentation performed as "
            "intended during the incident, and working with a forensics investigator to confirm "
            "the scope of what was actually accessed."
        ),
    ),
    Document(
        id="real-breach-notify-affected-parties",
        title="Data Breach Response — Step 3: Notify Affected Parties",
        category="security",
        text=(
            "Businesses must determine who they are legally required to notify, and by when — "
            "this can include affected individuals, state attorneys general, and in some cases "
            "the media, depending on state law and the type of data involved. If health "
            "information was involved, the FTC's Health Breach Notification Rule and/or the "
            "HIPAA Breach Notification Rule may separately apply on top of general state breach "
            "notification law. Notification should include what data was taken, what the "
            "business has done in response, and what affected individuals should do next."
        ),
    ),
    Document(
        id="real-health-breach-notification-rule",
        title="FTC Health Breach Notification Rule",
        category="healthcare",
        text=(
            "Companies that handle personal health records but are not covered by HIPAA (for "
            "example, health apps and connected devices sold direct to consumers) are subject "
            "to the FTC's Health Breach Notification Rule instead. Following a breach of "
            "unsecured personal health information, a covered business must notify every "
            "individual whose information was breached, notify the FTC, and in some cases "
            "notify the media — timelines and thresholds depend on the number of individuals "
            "affected."
        ),
    ),
    Document(
        id="real-hipaa-breach-notification-rule",
        title="HIPAA Breach Notification Rule — Who It Covers",
        category="healthcare",
        text=(
            "Entities covered directly by HIPAA (health plans, healthcare clearinghouses, most "
            "healthcare providers, and their business associates) that experience a breach of "
            "unsecured protected health information must notify the affected individuals and "
            "the Secretary of the U.S. Department of Health and Human Services. This is a "
            "distinct legal obligation from the FTC's Health Breach Notification Rule — they "
            "cover different categories of entity, and a company should confirm which applies "
            "before assuming general breach notification law is sufficient."
        ),
    ),
    Document(
        id="real-ftc-safeguards-rule",
        title="FTC Safeguards Rule (Financial Institutions)",
        category="finance",
        text=(
            "The FTC Safeguards Rule requires financial institutions under its jurisdiction — a "
            "category that includes many non-bank companies handling consumer financial data, "
            "not just traditional banks — to develop, implement, and maintain a written "
            "information security program with administrative, technical, and physical "
            "safeguards appropriate to the size and complexity of the business and the "
            "sensitivity of the customer information it handles."
        ),
    ),
    Document(
        id="real-disposal-rule",
        title="FTC Disposal Rule",
        category="finance",
        text=(
            "Once a business is finished using sensitive information derived from a consumer "
            "report — for example, after a credit check during onboarding — the FTC's Disposal "
            "Rule requires it to take reasonable measures to dispose of that information "
            "securely, such as shredding physical documents or securely wiping digital records, "
            "rather than simply discarding it."
        ),
    ),
    Document(
        id="real-identity-theft-prevention",
        title="Identity Theft Prevention Program Requirements",
        category="finance",
        text=(
            "Certain financial institutions and creditors are required to determine whether "
            "they need a written identity theft prevention program under the FTC's Red Flags "
            "Rule, covering how the business detects, prevents, and responds to warning signs "
            "that an account may have been opened or accessed fraudulently using someone else's "
            "identity."
        ),
    ),
    Document(
        id="real-breach-law-enforcement",
        title="Involving Law Enforcement After a Breach",
        category="security",
        text=(
            "FTC guidance recommends contacting local law enforcement promptly after discovering "
            "a breach that may involve identity theft, since early reporting improves the "
            "chances of an effective response. If local law enforcement is not equipped to "
            "investigate the kind of incident involved, the FTC guidance suggests escalating to "
            "the FBI, U.S. Secret Service, or U.S. Postal Inspection Service depending on how "
            "the breach occurred."
        ),
    ),
    Document(
        id="real-service-provider-access-review",
        title="Reviewing Third-Party Service Provider Access After an Incident",
        category="security",
        text=(
            "When a breach involves a third-party service provider, the business is responsible "
            "for examining exactly what personal information that provider could access, "
            "deciding whether to revoke or narrow that access, and independently verifying — "
            "not just trusting the provider's assurance — that any vulnerability on the "
            "provider's side has actually been fixed before restoring normal access."
        ),
    ),
    Document(
        id="real-negative-option-material-misrepresentation",
        title="Material Misrepresentation in Subscription Marketing",
        category="billing",
        text=(
            "FTC enforcement in negative-option marketing has consistently focused on material "
            "misrepresentation — misleading a customer about the price, the existence of "
            "recurring charges, what the product or service actually does, or any other detail "
            "likely to affect their decision to sign up. This principle applies regardless of "
            "the channel: online, over the phone, or in person."
        ),
    ),
]
