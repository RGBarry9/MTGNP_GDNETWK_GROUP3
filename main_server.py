# main_server.py
import sys
import argparse
from server.game_server import GameServer


def main():
    """Start the MTGNP server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MTGNP Server")
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose mode to print all PDUs"
    )
    args = parser.parse_args()
    
    # Create and start server
    server = GameServer()
    server.set_verbose(args.verbose)
    
    print("="*60)
    print("MTGNP SERVER v1.0")
    print("="*60)
    if args.verbose:
        print("🔊 Verbose mode ENABLED")
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        server.stop()
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()