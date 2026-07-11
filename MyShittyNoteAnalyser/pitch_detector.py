import numpy as np
import math
import logging

logger = logging.getLogger(__name__)

_aubio_pitch_cache = {}

def _get_aubio_pitch(block_size, sample_rate):
    """Get or create a cached aubio pitch object for the given parameters."""
    key = (block_size, int(sample_rate))
    if key not in _aubio_pitch_cache:
        import aubio
        pitch_o = aubio.pitch("default", block_size, block_size, int(sample_rate))
        pitch_o.set_unit("Hz")
        pitch_o.set_tolerance(0.8)
        _aubio_pitch_cache[key] = pitch_o
    return _aubio_pitch_cache[key]

def detect_pitch(audio, sample_rate, block_size, use_aubio=True):
    """
    Return frequency in Hz or None.
    If use_aubio is True and aubio is installed, use it.
    Otherwise, fall back to autocorrelation.
    """
    if use_aubio:
        try:
            import aubio
            pitch_o = _get_aubio_pitch(block_size, sample_rate)
            vec = aubio.fvec(audio)
            freq = pitch_o(vec)[0]
            if freq > 0:
                return freq
            return None
        except ImportError:
            # aubio not installed, fall back to autocorrelation
            pass
        except Exception as e:
            # Other errors (e.g., FFT size not power of two) – fall back
            logger.warning("aubio error: %s, falling back to autocorrelation", e)
            pass

    # ------------------------------------------------------------------
    # Autocorrelation pitch detection (fallback)
    # ------------------------------------------------------------------
    # 1. Remove DC offset (subtract mean)
    audio = audio - np.mean(audio)

    # 2. Compute unbiased autocorrelation
    corr = np.correlate(audio, audio, mode='full')
    corr = corr[len(corr) // 2:]  # keep only the positive half

    # 3. Search for the first strong peak in the plausible lag range
    #    Corresponds to pitches between ~80 Hz and ~800 Hz
    min_lag = int(sample_rate / 800)   # highest expected period
    max_lag = int(sample_rate / 80)    # lowest  expected period
    if max_lag >= len(corr):
        max_lag = len(corr) - 1
    if min_lag >= max_lag:
        return None

    segment = corr[min_lag:max_lag]
    if len(segment) == 0:
        return None
    peak_idx = np.argmax(segment) + min_lag

    # 4. Parabolic interpolation around the peak for sub-sample accuracy
    if peak_idx == 0 or peak_idx == len(corr) - 1:
        lag = float(peak_idx)
    else:
        y0, y1, y2 = corr[peak_idx - 1], corr[peak_idx], corr[peak_idx + 1]
        denom = y0 - 2 * y1 + y2
        if abs(denom) > 1e-12:
            offset = 0.5 * (y0 - y2) / denom
            lag = peak_idx + offset
        else:
            lag = float(peak_idx)

    if lag == 0:
        return None

    # 5. Convert lag (samples) to frequency (Hz)
    freq = sample_rate / lag
    return freq if 80 < freq < 1000 else None

def freq_to_midi(freq):
    if freq is None or freq <= 0:
        return None
    return 69 + 12 * math.log2(freq / 440.0)