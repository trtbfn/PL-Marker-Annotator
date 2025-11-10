"""
Main Entry Point for Entity Annotator
Usage:
    python -m incep.plmarker_annotator.main [file.jsonl]
    
    or
    
    python incep/plmarker_annotator/main.py [file.jsonl]
"""
import sys
import os

if __name__ == "__main__":

    try:
        
        print("Entity Annotator v2.0")
        print("=" * 50)
        print("\nInitializing...")
        
        # This import will work once entity_annotator.py is complete
        from entity_annotator import EntityAnnotator
        
        app = EntityAnnotator()
        
        # Load file if provided as command line argument
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                print(f"Loading: {file_path}")
                app.load_file(file_path)
            else:
                print(f"Warning: File not found: {file_path}")
        
        print("Starting application...")
        print("\nKeyboard Shortcuts:")
        print("  Ctrl+O : Open file")
        print("  Ctrl+S : Save")
        print("  F1     : Show help")
        print("=" * 50)
        
        app.run()
        
    except ImportError as e:
        print(f"Error: Could not import required modules: {e}")
        print("\nPlease ensure entity_annotator.py is complete.")
        print("You may need to merge entity_annotator_part2.py into entity_annotator.py")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


