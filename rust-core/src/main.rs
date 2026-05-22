mod audio;
mod wakeword;
mod eventbus;
mod scheduler;
mod reflex;
mod state;

#[tokio::main]
async fn main() {
    println!("Friday Core (Rust) Initialized");
    
    // Initialize Event Bus (TCP Publisher)
    let bind_addr = "127.0.0.1:5555";
    let event_bus = crate::eventbus::bus::EventBus::new(bind_addr).await.expect("Failed to bind TCP EventBus");
    println!("EventBus bound to {}", bind_addr);

    // Initialize Local Tokio channels for Rust internal modules
    let (tx, mut rx) = tokio::sync::mpsc::channel::<crate::eventbus::bus::Event>(100);
    
    // Initialize Reflex Engine
    let reflex_engine = crate::reflex::engine::ReflexEngine::new();
    
    // Start internal event router
    tokio::spawn(async move {
        // Route internal rust events out to EventBus
        while let Some(event) = rx.recv().await {
            println!("Publishing event: {:?}", event);
            event_bus.publish(event);
        }
    });

    // Test Reflex Action
    reflex_engine.handle_intent("volume_up");

    // Initialize System State Engine
    let state_sync = crate::state::sync::StateSync::new();
    state_sync.start(tx.clone());

    // Initialize Audio stream (VAD & Wakeword)
    let mut audio_stream = crate::audio::stream::AudioStream::new();
    if let Err(e) = audio_stream.start(tx.clone()) {
        eprintln!("Failed to start audio stream: {}", e);
    }
    
    // Send a startup event test
    let _ = tx.send(crate::eventbus::bus::Event::SystemWake).await;
    
    // Keep alive
    loop {
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    }
}
