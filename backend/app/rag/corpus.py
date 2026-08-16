"""
Seed knowledge base for the retrieval pipeline.

In production this would be backed by a real document store (Confluence,
Notion, a ticketing system, contract PDFs, etc.) ingested via `ingest()`
below. For this project it ships with a small but realistic corpus of
enterprise-style documents so the RAG pipeline and the eval harness are
fully self-contained and reproducible.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    category: str
    text: str


CORPUS: list[Document] = [
    Document(
        id="doc-refund-policy",
        title="Refund & Chargeback Policy",
        category="billing",
        text=(
            "Customers on monthly plans are eligible for a full refund within 14 days "
            "of the charge date if usage is under 5% of the plan quota. Refunds beyond "
            "14 days require manager approval and are capped at one per customer per "
            "rolling 12 months. Chargebacks automatically suspend the account pending "
            "finance review."
        ),
    ),
    Document(
        id="doc-enterprise-sla",
        title="Enterprise SLA Terms",
        category="contracts",
        text=(
            "Enterprise tier customers are guaranteed 99.9% monthly uptime and a 1 hour "
            "response time for Sev-1 incidents. SLA credits are issued automatically as "
            "account credit and require no customer action. Sev-2 incidents receive a 4 "
            "hour response commitment."
        ),
    ),
    Document(
        id="doc-security-incident-runbook",
        title="Security Incident Response Runbook",
        category="security",
        text=(
            "On suspected credential leak, immediately rotate the affected API keys, "
            "invalidate active sessions for the account, and notify the customer within "
            "24 hours per the data processing addendum. All security incidents require "
            "human approval before customer communication is sent."
        ),
    ),
    Document(
        id="doc-crm-escalation",
        title="CRM Escalation Matrix",
        category="support",
        text=(
            "Accounts with ARR above $100k are routed to the Strategic Accounts team. "
            "Escalations mentioning legal, security, or churn risk must be flagged as "
            "high priority and require a human reviewer before any commitment is made "
            "to the customer."
        ),
    ),
    Document(
        id="doc-pricing-tiers",
        title="Pricing Tiers Overview",
        category="billing",
        text=(
            "The Starter plan includes 10k API calls/month at $49. The Growth plan "
            "includes 100k API calls/month at $299 and adds priority support. The "
            "Enterprise plan is custom priced and includes a dedicated success manager "
            "and the Enterprise SLA."
        ),
    ),
    Document(
        id="doc-outage-comms",
        title="Outage Communication Guidelines",
        category="operations",
        text=(
            "Any customer-facing message referencing an active incident must be reviewed "
            "by an on-call lead before sending. Do not speculate about root cause in "
            "external communication. Use the status page as the single source of truth "
            "for incident timelines."
        ),
    ),
    Document(
        id="doc-data-retention",
        title="Data Retention & Deletion Policy",
        category="compliance",
        text=(
            "Customer data is retained for 30 days after account cancellation, after "
            "which it is permanently deleted. Deletion requests under GDPR/CCPA must be "
            "fulfilled within 30 days and require a verified identity check before any "
            "irreversible action is taken."
        ),
    ),
    Document(
        id="doc-tool-crm-lookup",
        title="CRM Lookup Tool Reference",
        category="tooling",
        text=(
            "The crm_lookup tool accepts an account_id or email and returns plan tier, "
            "ARR, renewal date, and open support tickets. It times out after 8 seconds "
            "and should not be retried more than twice."
        ),
    ),
    Document(
        id="doc-tool-ticketing",
        title="Ticketing Tool Reference",
        category="tooling",
        text=(
            "The create_ticket tool opens a support ticket with a priority level of low, "
            "medium, high, or urgent. Urgent tickets page the on-call engineer "
            "immediately and should only be used for active customer-impacting issues."
        ),
    ),
    Document(
        id="doc-approval-thresholds",
        title="Human Approval Thresholds",
        category="governance",
        text=(
            "Any agent recommendation with confidence below 0.82, involving a refund "
            "above $500, a security disclosure, or a contract exception must be routed "
            "to a human approver before execution. All approvals are logged with the "
            "reviewer identity and decision rationale."
        ),
    ),
    Document(
        id="doc-onboarding-checklist",
        title="Enterprise Onboarding Checklist",
        category="onboarding",
        text=(
            "New Enterprise accounts require SSO configuration, a kickoff call within 5 "
            "business days, and a named success manager assigned before the contract "
            "start date. Onboarding delays past 10 business days should be escalated."
        ),
    ),
    Document(
        id="doc-legal-contract-exceptions",
        title="Contract Exception Handling",
        category="legal",
        text=(
            "Non-standard contract terms (custom liability caps, data residency "
            "commitments, non-standard payment terms) always require legal and a human "
            "approver, regardless of agent confidence. Never commit to contract "
            "exceptions in an automated response."
        ),
    ),
]
