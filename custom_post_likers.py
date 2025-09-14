import logging
import os
from functools import partial
from random import seed
from urllib.parse import urlparse, parse_qs

from colorama import Style

from GramAddict.core.decorators import run_safely
from GramAddict.core.handle_sources import handle_likers
from GramAddict.core.interaction import (
    interact_with_user,
    is_follow_limit_reached_for_source,
)
from GramAddict.core.plugin_loader import Plugin
from GramAddict.core.scroll_end_detector import ScrollEndDetector
from GramAddict.core.utils import get_value, init_on_things
from GramAddict.core.views import UniversalActions, SearchView, TabBarView

logger = logging.getLogger(__name__)

# Script Initialization
seed()


class InteractCustomPostLikers(Plugin):
    """Handles the functionality of interacting with custom post likers"""

    def __init__(self):
        super().__init__()
        self.description = "Handles the functionality of interacting with custom post likers"
        self.arguments = [
            {
                "arg": "--custom-post-likers",
                "nargs": None,
                "help": "interact with likers of posts from custom file",
                "metavar": "filename.txt",
                "default": None,
                "operation": True,
            }
        ]

    def run(self, device, configs, storage, sessions, profile_filter, plugin):
        class State:
            def __init__(self):
                pass

            is_job_completed = False

        self.device_id = configs.args.device
        self.sessions = sessions
        self.session_state = sessions[-1]
        self.args = configs.args
        self.current_mode = plugin

        # Get custom post links from file
        filename = self.args.custom_post_likers
        if not filename:
            logger.error("No custom post file specified!")
            return

        if not os.path.exists(filename):
            logger.error(f"File {filename} does not exist!")
            return

        # Read post links from file
        with open(filename, 'r') as f:
            post_links = [line.strip() for line in f if line.strip()]

        if not post_links:
            logger.error(f"No post links found in {filename}!")
            return

        logger.info(f"Found {len(post_links)} post links in {filename}")

        # Rastgele sırala
        from random import shuffle
        shuffle(post_links)

        for post_link in post_links:
            (
                active_limits_reached,
                _,
                actions_limit_reached,
            ) = self.session_state.check_limit(limit_type=self.session_state.Limit.ALL)
            limit_reached = active_limits_reached or actions_limit_reached

            self.state = State()
            logger.info(f"Handling post: {post_link}", extra={"color": f"{Style.BRIGHT}"})

            # Extract shortcode from Instagram URL
            shortcode = self._extract_shortcode(post_link)
            if not shortcode:
                logger.error(f"Invalid Instagram URL: {post_link}")
                continue

            # Init common things
            (
                on_interaction,
                stories_percentage,
                likes_percentage,
                follow_percentage,
                comment_percentage,
                pm_percentage,
                _,
            ) = init_on_things(f"post_{shortcode}", self.args, self.sessions, self.session_state)

            @run_safely(
                device=device,
                device_id=self.device_id,
                sessions=self.sessions,
                session_state=self.session_state,
                screen_record=self.args.screen_record,
                configs=configs,
            )
            def job():
                self.handle_custom_post(
                    device,
                    post_link,
                    shortcode,
                    plugin,
                    storage,
                    profile_filter,
                    on_interaction,
                    stories_percentage,
                    likes_percentage,
                    follow_percentage,
                    comment_percentage,
                    pm_percentage,
                )
                self.state.is_job_completed = True

            while not self.state.is_job_completed and not limit_reached:
                job()

            if limit_reached:
                logger.info("Limits reached for this session.")
                self.session_state.check_limit(
                    limit_type=self.session_state.Limit.ALL, output=True
                )
                break

    def _extract_shortcode(self, url):
        """Extract Instagram post shortcode from URL"""
        parsed = urlparse(url)
        if 'instagram.com' not in parsed.netloc:
            return None
        
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 'p':
            return path_parts[1]
        
        # Handle alternative URL formats
        if 'p/' in parsed.path:
            return parsed.path.split('p/')[-1].split('/')[0]
        
        return None

    def handle_custom_post(
        self,
        device,
        post_link,
        shortcode,
        current_job,
        storage,
        profile_filter,
        on_interaction,
        stories_percentage,
        likes_percentage,
        follow_percentage,
        comment_percentage,
        pm_percentage,
    ):
        # Navigate to the post using the direct link
        if not self._navigate_to_post(device, post_link):
            logger.error(f"Failed to navigate to post: {post_link}")
            return

        interaction = partial(
            interact_with_user,
            my_username=self.session_state.my_username,
            likes_count=self.args.likes_count,
            likes_percentage=likes_percentage,
            stories_percentage=stories_percentage,
            follow_percentage=follow_percentage,
            comment_percentage=comment_percentage,
            pm_percentage=pm_percentage,
            profile_filter=profile_filter,
            args=self.args,
            session_state=self.session_state,
            scraping_file=self.args.scrape_to_file,
            current_mode=self.current_mode,
        )
        
        source_follow_limit = (
            get_value(self.args.follow_limit, None, 15)
            if self.args.follow_limit is not None
            else None
        )
        is_follow_limit_reached = partial(
            is_follow_limit_reached_for_source,
            session_state=self.session_state,
            follow_limit=source_follow_limit,
            source=f"post_{shortcode}",
        )

        skipped_list_limit = get_value(self.args.skipped_list_limit, None, 15)
        skipped_fling_limit = get_value(self.args.fling_when_skipped, None, 0)

        posts_end_detector = ScrollEndDetector(
            repeats_to_end=2,
            skipped_list_limit=skipped_list_limit,
            skipped_fling_limit=skipped_fling_limit,
        )

        # Aşağı kaydırma kısmı başlangıcı
        # Scroll down once to make sure all elements are visible (especially for Reels)
        logger.info("Scrolling down once to ensure likers list is visible.")
        from GramAddict.core.utils import random_sleep
        from GramAddict.core.device_facade import Direction

        # GramAddict çekirdeğinde kullanılan swipe yöntemiyle kaydır

        device.swipe(Direction.UP, scale=0.8)
        random_sleep(1, 2)
        # Aşağı kaydırma kısmı bitiş

    

        # Open likers list
        if not self._open_likers(device):
            logger.error("Failed to open likers list!")
            return

        handle_likers(
            self,
            device,
            self.session_state,
            f"post_{shortcode}",
            current_job,
            storage,
            profile_filter,
            posts_end_detector,
            on_interaction,
            interaction,
            is_follow_limit_reached,
        )

    def _navigate_to_post(self, device, post_link):
        """Navigate to post using direct link"""
        logger.info(f"Navigating to post: {post_link}")
        
        # Open Instagram with the post URL
        from GramAddict.core.utils import open_instagram_with_url
        if open_instagram_with_url(post_link):
            # Wait for post to load
            from GramAddict.core.utils import random_sleep
            random_sleep(3, 5)
            return True
        
        return False

    def _open_likers(self, device):
        """Open the likers list for the current post"""
        logger.info("Opening likers list...")
        
        # Try to find and click the likers count view
        likes_view = device.find(
            resourceIdMatches=".*row_feed_textview_likes|.*likes_count",
            className="android.widget.TextView"
        )
        
        if likes_view.wait(10):
            likes_view.click()
            from GramAddict.core.utils import random_sleep
            random_sleep(3, 5)
            return True

        
        # Alternative method: look for facepile
        facepile = device.find(
            resourceIdMatches=".*facepile|.*likers_facepile",
            className="android.view.View"
        )
        
        if facepile.wait(10):
            facepile.click()
            random_sleep(3, 5)
            return True

        
        return False