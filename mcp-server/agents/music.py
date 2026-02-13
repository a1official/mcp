"""
Music Agent - iTunes API Integration
Provides music search and playback tools
"""

import json
import httpx

ITUNES_API = "https://itunes.apple.com/search"


def register_music_tools(mcp):
    """Register all music-related tools with the MCP server"""
    
    @mcp.tool()
    async def play_music(query: str) -> str:
        """
        Play music based on natural language query. 
        Searches iTunes and returns a 30-second preview that plays instantly.
        
        Args:
            query: Natural language music query (song name, artist, genre, etc.)
        
        Returns:
            JSON with track information including preview URL
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                ITUNES_API,
                params={
                    "term": query,
                    "entity": "song",
                    "limit": 1
                }
            )
            data = response.json()
            
            results = data.get("results", [])
            
            if not results:
                return json.dumps({
                    "success": False,
                    "error": f"No music found for: {query}"
                })
            
            track = results[0]
            
            if not track.get("previewUrl"):
                return json.dumps({
                    "success": False,
                    "error": f"No preview available for: {track.get('trackName')} by {track.get('artistName')}"
                })
            
            return json.dumps({
                "success": True,
                "action": "PLAY_MUSIC",
                "message": f"Now playing: {track.get('trackName')} by {track.get('artistName')}",
                "track": {
                    "name": track.get("trackName"),
                    "artist": track.get("artistName"),
                    "album": track.get("collectionName"),
                    "previewUrl": track.get("previewUrl"),
                    "artworkUrl": track.get("artworkUrl100"),
                    "genre": track.get("primaryGenreName"),
                    "releaseDate": track.get("releaseDate")
                }
            }, indent=2)

    @mcp.tool()
    async def search_music(query: str, type: str = "song", limit: int = 10) -> str:
        """
        Search for songs, artists, or albums on iTunes.
        
        Args:
            query: Search query (song name, artist name, or album)
            type: Type of search - 'song', 'artist', or 'album' (default: 'song')
            limit: Maximum number of results (default: 10)
        
        Returns:
            JSON with search results
        """
        type_map = {
            "song": "song",
            "artist": "musicArtist",
            "album": "album"
        }
        
        entity = type_map.get(type, "song")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                ITUNES_API,
                params={
                    "term": query,
                    "entity": entity,
                    "limit": limit
                }
            )
            data = response.json()
            
            results = data.get("results", [])
            
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "name": item.get("trackName") or item.get("artistName") or item.get("collectionName"),
                    "artist": item.get("artistName"),
                    "album": item.get("collectionName"),
                    "genre": item.get("primaryGenreName"),
                    "releaseDate": item.get("releaseDate"),
                    "previewUrl": item.get("previewUrl"),
                    "artworkUrl": item.get("artworkUrl100")
                })
            
            return json.dumps({
                "query": query,
                "type": type,
                "count": len(formatted_results),
                "results": formatted_results
            }, indent=2)

    @mcp.tool()
    async def get_artist_info(artist: str) -> str:
        """
        Get information about an artist from iTunes.
        
        Args:
            artist: Artist name
        
        Returns:
            JSON with artist information
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                ITUNES_API,
                params={
                    "term": artist,
                    "entity": "musicArtist",
                    "limit": 1
                }
            )
            data = response.json()
            
            results = data.get("results", [])
            
            if not results:
                return json.dumps({
                    "error": f"Artist not found: {artist}"
                })
            
            artist_data = results[0]
            
            return json.dumps({
                "name": artist_data.get("artistName"),
                "genre": artist_data.get("primaryGenreName"),
                "artistLinkUrl": artist_data.get("artistLinkUrl")
            }, indent=2)
