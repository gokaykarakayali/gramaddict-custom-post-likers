# GramAddict Custom Post Likers Plugin

A plugin for [GramAddict](https://github.com/GramAddict/bot) that allows interacting with users who liked posts from a custom list of Instagram post URLs.

## Features

- Reads Instagram post URLs from a text file
- Extracts shortcodes from various Instagram URL formats
- Randomizes the order of posts for natural behavior
- Interacts with likers (follow, like, comment, etc.)
- Handles both regular posts and Reels

## Installation

1. Download the `custom_post_likers.py` file
2. Place it in your GramAddict `plugins` folder
3. Download the `handle_sources.py` file
4. Place it in your GramAddict `core` folder
5. Update your interaction settings in config file (ie. custom-post-likers: custompostlikers.txt)
6. Ensure you have GramAddict version 3.2.12 installed

## Usage

1. Create a text file with Instagram post URLs (one per line):
   ```
   https://www.instagram.com/p/Cabc123/
   https://www.instagram.com/reel/Cdef456/
   https://www.instagram.com/p/Cghi789/
   ```

2. Change your interaction settings in config yml file:
   ```bash
   custom-post-likers: custom-post-likers.txt
   ```

3. Run GramAddict with the plugin:
   ```bash
   python run.py --config C:\...\config.yml
   ```

## Configuration Options

The plugin supports all standard GramAddict interaction options:
- `--likes-count` - Number of likes to perform
- `--follow-percentage` - Percentage of users to follow
- `--comment-percentage` - Percentage of posts to comment on
- And other standard GramAddict parameters

## Requirements

- GramAddict version 3.2.12
- Android device with Instagram installed (300.0.0.29.110)

## Limitations

- The functionality of this plugin is quite aggressive

## Contributing

Feel free to not submit issues and enhancement requests. I don't accept criticism.

## License

This project is licensed under the MIT License - see the [GramAddict LICENSE](https://github.com/GramAddict/bot/blob/master/LICENSE) file for details.
