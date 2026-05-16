"""
Media Tools
Tools for controlling media playback and music
"""

from ..tool_base import Tool, ToolSchema, ToolParameter, ParameterType


class PlayMusicTool(Tool):
    """Play music from Spotify or local player"""
    
    def __init__(self):
        schema = ToolSchema(
            name="media.play_music",
            description="Play music from Spotify or queue a song",
            category="media",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ParameterType.STRING,
                    description="Song name, artist, or playlist to play",
                    required=True
                ),
                ToolParameter(
                    name="service",
                    type=ParameterType.STRING,
                    description="Music service to use (spotify, youtube, etc.)",
                    required=False,
                    enum=["spotify", "youtube", "local"],
                    default="spotify"
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        query = kwargs.get("query")
        service = kwargs.get("service", "spotify")
        
        # This would integrate with Spotify API or music control
        return f"Now playing '{query}' on {service}"


class AdjustVolumeTool(Tool):
    """Adjust system or player volume"""
    
    def __init__(self):
        schema = ToolSchema(
            name="media.adjust_volume",
            description="Adjust system volume level",
            category="media",
            parameters=[
                ToolParameter(
                    name="level",
                    type=ParameterType.INTEGER,
                    description="Volume level (0-100)",
                    required=True
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        level = kwargs.get("level")
        
        if not (0 <= level <= 100):
            raise ValueError("Volume level must be between 0 and 100")
        
        # This would adjust actual system volume
        return f"Volume set to {level}%"


class PausePlayTool(Tool):
    """Pause or resume playback"""
    
    def __init__(self):
        schema = ToolSchema(
            name="media.pause_play",
            description="Pause or resume current playback",
            category="media",
            parameters=[
                ToolParameter(
                    name="action",
                    type=ParameterType.STRING,
                    description="Action to perform",
                    required=True,
                    enum=["pause", "play", "toggle"]
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        action = kwargs.get("action")
        return f"Playback {action}d successfully"
