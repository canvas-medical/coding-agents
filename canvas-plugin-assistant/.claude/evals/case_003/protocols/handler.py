"""
Eval case: Handler with N+1 query performance issues.

VULNERABILITIES:
1. Query inside loop - Condition.objects.filter() called for each patient
2. Missing select_related - accessing patient.primary_care_provider without prefetch

The database performance review should detect both issues.
"""

from canvas_sdk.effects import Effect
from canvas_sdk.events import EventType
from canvas_sdk.protocols import BaseProtocol
from canvas_sdk.v1.data.patient import Patient
from canvas_sdk.v1.data.condition import Condition
from logger import log


class DailyDigestHandler(BaseProtocol):
    """Handler that demonstrates N+1 query performance issues."""

    RESPONDS_TO = [EventType.Name(EventType.CRON_TASK)]

    def compute(self) -> list[Effect]:
        # Get all active patients
        patients = Patient.objects.filter(active=True)

        results = []
        for patient in patients:
            # VULNERABILITY 1: N+1 query - this executes a NEW query for EACH patient
            # Should be: prefetch conditions in initial query or batch fetch
            conditions = Condition.objects.filter(patient_id=patient.id)

            # VULNERABILITY 2: Missing select_related - accessing FK without prefetch
            # Should be: Patient.objects.filter(active=True).select_related('primary_care_provider')
            provider_name = patient.primary_care_provider.full_name

            # VULNERABILITY 3: Another N+1 - count() inside loop
            condition_count = conditions.count()

            results.append(
                {
                    "patient_id": patient.id,
                    "provider": provider_name,
                    "conditions": condition_count,
                }
            )

        log.info(f"Generated digest for {len(results)} patients")
        return []
