"""Tests for the application state machine."""

import pytest
from MyShittyNoteAnalyser.app_state import (AppState, validate_transition,
                                            InvalidStateTransitionError)


class TestAppStateTransitions:
    """Tests for valid and invalid state transitions."""

    def test_idle_to_rms_only(self):
        validate_transition(AppState.IDLE, AppState.RMS_ONLY)  # should not raise

    def test_rms_only_to_full_analysis(self):
        validate_transition(AppState.RMS_ONLY, AppState.FULL_ANALYSIS)

    def test_full_analysis_to_rms_only(self):
        validate_transition(AppState.FULL_ANALYSIS, AppState.RMS_ONLY)

    def test_rms_only_to_idle(self):
        validate_transition(AppState.RMS_ONLY, AppState.IDLE)

    def test_full_analysis_to_idle(self):
        validate_transition(AppState.FULL_ANALYSIS, AppState.IDLE)

    # ── invalid transitions ─────────────────────────────────────

    def test_idle_to_full_analysis_raises(self):
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(AppState.IDLE, AppState.FULL_ANALYSIS)

    def test_same_state_noop(self):
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(AppState.IDLE, AppState.IDLE)
