"""Regenerates the synthetic PDF fixtures under tests/fixtures/.

These are test data for the ingestion pipeline's unit/integration
tests, not the real demo corpus (that's uploaded live through the UI -
see docs/requirements.md). Content just needs to be long enough to
exercise chunking/overlap and distinct enough across the two files to
make cross-document test assertions meaningful.

Run with: uv run python scripts/generate_test_fixtures.py
"""

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"

HR_PARAGRAPHS = [
    "Sample HR Policy Handbook",
    (
        "Section 1: Paid Time Off. "
        "Full-time employees accrue fifteen days of paid time off per calendar "
        "year during their first three years of employment. Accrual increases "
        "to twenty days beginning in the fourth year of continuous service. "
        "Part-time employees accrue paid time off on a prorated basis "
        "according to their regularly scheduled hours."
    ),
    (
        "Section 2: Sick Leave. "
        "Employees accrue one sick day per month of continuous employment, "
        "up to a maximum of twelve days per calendar year. Unused sick leave "
        "carries over to the following year up to a cap of thirty days total. "
        "A doctor's note is required for any sick leave absence exceeding "
        "three consecutive working days."
    ),
    (
        "Section 3: Parental Leave. "
        "Employees who have completed at least twelve months of continuous "
        "service are eligible for up to twelve weeks of parental leave "
        "following the birth, adoption, or foster placement of a child. The "
        "first two weeks of parental leave are paid at full salary; the "
        "remaining ten weeks are unpaid but job-protected."
    ),
    (
        "Section 4: Remote Work. "
        "Employees may request a remote work arrangement subject to manager "
        "approval and role suitability. Remote work agreements are reviewed "
        "annually and may be revoked if performance or availability "
        "expectations are not met."
    ),
    (
        "Section 5: Overtime. "
        "Non-exempt employees who work more than forty hours in a single "
        "work week are entitled to overtime pay at one and one-half times "
        "their regular hourly rate for all hours worked beyond forty. "
        "Overtime must be pre-approved by a direct manager except in "
        "genuine emergency circumstances."
    ),
    (
        "Section 6: Workplace Safety. "
        "All employees are required to complete annual safety training "
        "relevant to their role. Any workplace injury, no matter how minor, "
        "must be reported to a supervisor within twenty-four hours. Failure "
        "to report an injury in a timely manner may affect eligibility for "
        "workers' compensation benefits."
    ),
]

COMPLIANCE_PARAGRAPHS = [
    "Sample Code of Conduct and Ethics",
    (
        "Section 1: Conflicts of Interest. "
        "Employees must disclose any financial or personal interest that "
        "could reasonably be seen to conflict with their duties. Undisclosed "
        "conflicts of interest are grounds for disciplinary action up to and "
        "including termination of employment."
    ),
    (
        "Section 2: Gifts and Entertainment. "
        "Employees may not accept gifts, meals, or entertainment from vendors "
        "or clients with a value exceeding one hundred dollars without prior "
        "written approval from their department head. Cash gifts of any "
        "amount are strictly prohibited under all circumstances."
    ),
    (
        "Section 3: Reporting Violations. "
        "Employees who become aware of a suspected violation of this code "
        "are required to report it to their supervisor or the compliance "
        "hotline. Reports made in good faith are protected from retaliation "
        "under this policy, regardless of the outcome of any investigation."
    ),
    (
        "Section 4: Confidential Information. "
        "Employees must not disclose confidential business information to "
        "any external party without authorization, both during and after "
        "their employment with the organization."
    ),
    (
        "Section 5: Anti-Bribery. "
        "Employees, agents, and contractors are strictly prohibited from "
        "offering, promising, or giving anything of value to a government "
        "official for the purpose of obtaining or retaining business. This "
        "prohibition applies regardless of local custom and regardless of "
        "whether the payment is made directly or through a third party."
    ),
    (
        "Section 6: Data Protection. "
        "Employees who handle customer or employee personal data must "
        "follow the organization's data protection standards at all times. "
        "Any suspected data breach must be reported to the compliance "
        "officer immediately, and in no case later than twenty-four hours "
        "after discovery."
    ),
]


def _build_pdf(path: Path, title: str, paragraphs: list[str]) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=LETTER)
    story = [Paragraph(title, styles["Title"]), Spacer(1, 24)]
    body_paragraphs = paragraphs[1:]
    midpoint = len(body_paragraphs) // 2
    for i, para in enumerate(body_paragraphs):
        if i == midpoint:
            story.append(PageBreak())
        story.append(Paragraph(para, styles["BodyText"]))
        story.append(Spacer(1, 12))
    doc.build(story)


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    _build_pdf(FIXTURES_DIR / "sample_policy_a.pdf", HR_PARAGRAPHS[0], HR_PARAGRAPHS)
    _build_pdf(
        FIXTURES_DIR / "sample_policy_b.pdf", COMPLIANCE_PARAGRAPHS[0], COMPLIANCE_PARAGRAPHS
    )
    print(f"Wrote fixtures to {FIXTURES_DIR}")


if __name__ == "__main__":
    main()
