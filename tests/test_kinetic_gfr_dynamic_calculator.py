"""
Automated Pytest Test Suite for Kinetic Gfr Dynamic Calculator.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException, AuditTrail
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_phi_guard_ssn_detection():
    """SSN pattern should be detected and blocked."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient SSN: 123-45-6789")


def test_phi_guard_phone_detection():
    """Phone number pattern should be detected and blocked."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Contact: (555) 123-4567")


def test_phi_guard_email_detection():
    """Email pattern should be detected and blocked."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Email: patient@hospital.org")


def test_phi_redact():
    """PHIGuard.redact_phi should replace PII with placeholder."""
    redacted = PHIGuard.redact_phi("Patient MRN-12345678 is here")
    assert "MRN-12345678" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_workers_no_alerts_on_nominal():
    """Workers should not raise alerts for nominal payloads."""
    p = SystemTaskPayload(task_id="T-NOM", target_identifier="KEY-NOM", primary_metric=10.0, status_descriptor="NOMINAL")
    assert len(InvariantQCWorker.evaluate(p)) == 0
    assert len(SafetyEscalationWorker.evaluate(p)) == 0
    assert len(ProtocolConformanceWorker.evaluate(p)) == 0


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_supervisor_critical_escalation():
    """Critical flag should result in CRITICAL_STAT urgency."""
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-CRIT",
        target_identifier="KEY-CRIT",
        primary_metric=30.0,
        secondary_metric=15.0,
        is_critical_flag=True,
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.CRITICAL_STAT
    assert dossier.integrity_status == SystemIntegrityStatus.RECALIBRATION_REQUIRED


def test_supervisor_phi_rejection():
    """PHI in task_id should be rejected."""
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="Patient MRN-12345678",
        target_identifier="KEY-01",
        primary_metric=10.0,
    )
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)


def test_audit_trail_integrity():
    """Audit trail should maintain cryptographic chain integrity."""
    trail = AuditTrail(secret_key="test-key-for-integrity")
    trail.log("test", "tier1", "EVENT_1", {"data": "value1"})
    trail.log("test", "tier1", "EVENT_2", {"data": "value2"})
    assert trail.verify_integrity() is True
    assert len(trail.get_trail()) == 2


def test_audit_trail_tamper_detection():
    """Tampered audit trail should fail integrity check."""
    trail = AuditTrail(secret_key="test-key-for-tamper")
    trail.log("test", "tier1", "EVENT_1", {"data": "value1"})
    trail.log("test", "tier1", "EVENT_2", {"data": "value2"})
    # Tamper with the first entry
    trail.logs[0]["payload_hash"] = "tampered_hash"
    assert trail.verify_integrity() is False


def test_cli_batch_missing_file():
    """CLI batch command should return error code for missing file."""
    result = main(["batch", "-i", "nonexistent_file_12345.csv"])
    assert result == 1
