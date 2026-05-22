use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use ringbuf::HeapRb;
use std::sync::Arc;
use tokio::sync::Mutex;
use crate::eventbus::bus::Event;
use tokio::sync::broadcast;

pub struct AudioStream {
    stream: Option<cpal::Stream>,
}

impl AudioStream {
    pub fn new() -> Self {
        Self { stream: None }
    }

    pub fn start(&mut self, event_sender: tokio::sync::mpsc::Sender<Event>) -> Result<(), Box<dyn std::error::Error>> {
        let host = cpal::default_host();
        let device = host.default_input_device().ok_or("No input device available")?;
        
        let config = device.default_input_config()?;
        println!("Default input config: {:?}", config);
        
        // Setup ring buffer for audio data
        let latency_frames = (config.sample_rate().0 as f32 / 1000.0 * 50.0) as usize; // 50ms buffer
        let ring = HeapRb::<f32>::new(latency_frames * 2);
        let (mut producer, mut consumer) = ring.split();

        // Audio Input Callback
        let stream = device.build_input_stream(
            &config.into(),
            move |data: &[f32], _: &cpal::InputCallbackInfo| {
                // Push data to ring buffer
                for &sample in data {
                    let _ = producer.push(sample);
                }
            },
            move |err| {
                eprintln!("An error occurred on the input audio stream: {}", err);
            },
            None, // timeout
        )?;

        stream.play()?;
        self.stream = Some(stream);

        // Spawn async task to process audio from the ring buffer
        tokio::spawn(async move {
            let mut chunk = Vec::with_capacity(512);
            let mut vad = crate::audio::vad::VadEngine::new();
            let mut wakeword = crate::wakeword::engine::WakewordEngine::new();
            
            loop {
                while let Some(sample) = consumer.pop() {
                    chunk.push(sample);
                }
                
                if chunk.len() >= 512 {
                    // Process chunk: VAD & Wakeword
                    let (started, stopped) = vad.process(&chunk);
                    
                    if started {
                        println!("VAD: Speech Started");
                        let _ = event_sender.send(Event::UserStartedSpeaking);
                    }
                    if stopped {
                        println!("VAD: Speech Stopped");
                        let _ = event_sender.send(Event::UserStoppedSpeaking);
                    }
                    
                    if wakeword.process(&chunk) {
                        println!("WAKEWORD DETECTED!");
                        let _ = event_sender.send(Event::SystemWake);
                    }
                    
                    chunk.clear();
                }
                tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
            }
        });

        Ok(())
    }
}
