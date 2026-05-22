pub struct WakewordEngine {
    is_active: bool,
}

impl WakewordEngine {
    pub fn new() -> Self {
        Self { is_active: false }
    }

    /// Process audio chunk, returns true if wakeword detected
    pub fn process(&mut self, _audio_chunk: &[f32]) -> bool {
        // Here we would run an ONNX model, Rustpotter, or Porcupine
        // For now, it's a stub
        false
    }
}
