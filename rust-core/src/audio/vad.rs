pub struct VadEngine {
    speaking: bool,
    frames_since_speech: usize,
}

impl VadEngine {
    pub fn new() -> Self {
        Self {
            speaking: false,
            frames_since_speech: 0,
        }
    }

    /// Returns (just_started_speaking, just_stopped_speaking)
    pub fn process(&mut self, audio_chunk: &[f32]) -> (bool, bool) {
        // Calculate RMS Energy as a naive VAD
        let energy: f32 = audio_chunk.iter().map(|&s| s * s).sum::<f32>() / audio_chunk.len() as f32;
        let rms = energy.sqrt();
        let threshold = 0.05; // Naive threshold

        let mut started = false;
        let mut stopped = false;

        if rms > threshold {
            if !self.speaking {
                self.speaking = true;
                started = true;
            }
            self.frames_since_speech = 0;
        } else if self.speaking {
            self.frames_since_speech += 1;
            // 50 frames of silence = stopped speaking (e.g., ~500ms depending on chunk size)
            if self.frames_since_speech > 50 {
                self.speaking = false;
                stopped = true;
            }
        }

        (started, stopped)
    }
}
