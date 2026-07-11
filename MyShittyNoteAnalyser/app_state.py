"""
Application state machine — defines the valid states and transitions
for the audio analysis pipeline.

    IDLE ──start_stream()──▶ RMS_ONLY
    RMS_ONLY ──enable_full_analysis()──▶ FULL_ANALYSIS
    FULL_ANALYSIS ──disable_full_analysis()──▶ RMS_ONLY
    FULL_ANALYSIS ──start_game()──▶ GAME_ACTIVE
    GAME_ACTIVE ──stop_game()──▶ FULL_ANALYSIS
    any ──stop_stream()──▶ IDLE
"""

from enum import Enum


class AppState(Enum):
    """Valid states for the audio analysis pipeline."""
    IDLE = "idle"
    RMS_ONLY = "rms_only"
    FULL_ANALYSIS = "full_analysis"
    GAME_ACTIVE = "game_active"


# Valid transitions: {from_state: {to_state, ...}}
_VALID_TRANSITIONS: dict[AppState, set[AppState]] = {
    AppState.IDLE:           {AppState.RMS_ONLY},
    AppState.RMS_ONLY:       {AppState.FULL_ANALYSIS, AppState.IDLE},
    AppState.FULL_ANALYSIS:  {AppState.RMS_ONLY, AppState.GAME_ACTIVE,
                               AppState.IDLE},
    AppState.GAME_ACTIVE:    {AppState.FULL_ANALYSIS, AppState.IDLE},
}


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    def __init__(self, from_state: AppState, to_state: AppState):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid state transition: {from_state.value} → {to_state.value}")


def validate_transition(from_state: AppState, to_state: AppState) -> None:
    """Raise InvalidStateTransitionError if the transition is not allowed."""
    allowed = _VALID_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        raise InvalidStateTransitionError(from_state, to_state)
