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

    def test_full_analysis_to_game_active(self):
        validate_transition(AppState.FULL_ANALYSIS, AppState.GAME_ACTIVE)

    def test_game_active_to_full_analysis(self):
        validate_transition(AppState.GAME_ACTIVE, AppState.FULL_ANALYSIS)

    def test_rms_only_to_idle(self):
        validate_transition(AppState.RMS_ONLY, AppState.IDLE)

    def test_full_analysis_to_idle(self):
        validate_transition(AppState.FULL_ANALYSIS, AppState.IDLE)

    def test_game_active_to_idle(self):
        validate_transition(AppState.GAME_ACTIVE, AppState.IDLE)

    # ── invalid transitions ─────────────────────────────────────

    def test_idle_to_full_analysis_raises(self):
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(AppState.IDLE, AppState.FULL_ANALYSIS)

    def test_idle_to_game_active_raises(self):
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(AppState.IDLE, AppState.GAME_ACTIVE)

    def test_rms_only_to_game_active_raises(self):
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(AppState.RMS_ONLY, AppState.GAME_ACTIVE)

    def test_game_active_to_rms_only_raises(self):
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(AppState.GAME_ACTIVE, AppState.RMS_ONLY)

    def test_same_state_noop(self):
        # Transitioning to the same state is generally invalid
        # unless explicitly allowed (not in our case)
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(AppState.IDLE, AppState.IDLE)
