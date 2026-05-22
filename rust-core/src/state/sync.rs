use std::process::Command;
use crate::eventbus::bus::Event;
use tokio::sync::broadcast;
use std::time::Duration;

pub struct StateSync;

impl StateSync {
    pub fn new() -> Self {
        Self
    }

    pub fn start(&self, event_sender: tokio::sync::mpsc::Sender<Event>) {
        tokio::spawn(async move {
            let mut last_window = String::new();
            let mut last_media_status = String::new();

            loop {
                // Check Active Window (Hyprland)
                if let Ok(output) = Command::new("hyprctl").args(["activewindow", "-j"]).output() {
                    if let Ok(json_str) = String::from_utf8(output.stdout) {
                        if let Ok(json) = serde_json::from_str::<serde_json::Value>(&json_str) {
                            if let (Some(class), Some(title)) = (json.get("class"), json.get("title")) {
                                let current_app = class.as_str().unwrap_or("").to_string();
                                let current_title = title.as_str().unwrap_or("").to_string();
                                
                                let window_id = format!("{}::{}", current_app, current_title);
                                if window_id != last_window && !current_app.is_empty() {
                                    last_window = window_id;
                                    let _ = event_sender.send(Event::WindowChanged { 
                                        app: current_app, 
                                        title: current_title 
                                    }).await;
                                }
                            }
                        }
                    }
                }

                // Check Media State (playerctl)
                if let Ok(output) = Command::new("playerctl").args(["status"]).output() {
                    if let Ok(status) = String::from_utf8(output.stdout) {
                        let status = status.trim().to_string();
                        if status != last_media_status {
                            if status == "Playing" {
                                let _ = event_sender.send(Event::MusicStarted).await;
                            } else if status == "Paused" {
                                let _ = event_sender.send(Event::MusicPaused).await;
                            }
                            last_media_status = status;
                        }
                    }
                }

                tokio::time::sleep(Duration::from_millis(500)).await;
            }
        });
    }
}
