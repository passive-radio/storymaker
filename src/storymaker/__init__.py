import argparse
from .create_story import main as create_story_main
from .create_character import main as create_character_main


def main():
    parser = argparse.ArgumentParser(description="Storymaker CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Subcommand for character
    character_parser = subparsers.add_parser("character", help="Create character settings")
    character_parser.add_argument("-i", "--input", type=str, required=True, help="Input news file")
    character_parser.add_argument(
        "-o", "--output", type=str, required=True, help="Output character settings file"
    )

    # Subcommand for story
    story_parser = subparsers.add_parser("story", help="Create a story")
    story_parser.add_argument("-i", "--input", type=str, required=True, help="Input character file")
    story_parser.add_argument(
        "-o", "--output_dir", type=str, required=True, help="Output directory for the story"
    )

    args = parser.parse_args()

    if args.command == "character":
        create_character_main(["--input", args.input, "--output", args.output])
    elif args.command == "story":
        create_story_main(["--input", args.input, "--output_dir", args.output_dir])
    else:
        parser.print_help()
