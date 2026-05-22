use serde::{Deserialize, Serialize};
use tokio::net::TcpListener;
use tokio::io::AsyncWriteExt;
use std::sync::Arc;
use tokio::sync::broadcast;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Event {
    UserStartedSpeaking,
    UserStoppedSpeaking,
    WindowChanged { title: String, app: String },
    MusicStarted,
    MusicPaused,
    WorkflowTriggered { name: String },
    SystemWake,
}

pub struct EventBus {
    pub sender: broadcast::Sender<Event>,
}

impl EventBus {
    pub async fn new(bind_addr: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let (tx, _rx) = broadcast::channel(100);
        let listener = TcpListener::bind(bind_addr).await?;
        
        let tx_clone = tx.clone();
        
        // Spawn task to handle incoming TCP connections for clients subscribing to events
        tokio::spawn(async move {
            loop {
                if let Ok((mut socket, _addr)) = listener.accept().await {
                    let mut rx = tx_clone.subscribe();
                    tokio::spawn(async move {
                        while let Ok(event) = rx.recv().await {
                            if let Ok(payload) = serde_json::to_string(&event) {
                                let message = format!("{}\n", payload);
                                if socket.write_all(message.as_bytes()).await.is_err() {
                                    break;
                                }
                            }
                        }
                    });
                }
            }
        });

        Ok(Self { sender: tx })
    }

    pub fn publish(&self, event: Event) {
        let _ = self.sender.send(event);
    }
}
