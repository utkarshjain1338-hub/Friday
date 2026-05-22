use crate::eventbus::bus::Event;
use std::process::Command;

pub struct ReflexEngine;

impl ReflexEngine {
    pub fn new() -> Self {
        Self
    }

    pub fn handle_intent(&self, intent: &str) -> bool {
        match intent {
            "volume_up" => {
                println!("Reflex: Increasing volume...");
                let _ = Command::new("pactl")
                    .args(["set-sink-volume", "@DEFAULT_SINK@", "+5%"])
                    .output();
                true
            }
            "volume_down" => {
                println!("Reflex: Decreasing volume...");
                let _ = Command::new("pactl")
                    .args(["set-sink-volume", "@DEFAULT_SINK@", "-5%"])
                    .output();
                true
            }
            "brightness_up" => {
                println!("Reflex: Increasing brightness...");
                let _ = Command::new("brightnessctl")
                    .args(["set", "5%+"])
                    .output();
                true
            }
            "brightness_down" => {
                println!("Reflex: Decreasing brightness...");
                let _ = Command::new("brightnessctl")
                    .args(["set", "5%-"])
                    .output();
                true
            }
            _ => false, // Not handled by reflex, let it fall through to Python layer
        }
    }
}
