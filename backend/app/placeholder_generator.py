import time


class PlaceholderGenerator:

    mojo_message = "Hello world!"

    # This is lorem ipsum translated to English
    mojo_draft_title= "It's going to be a lot of fun."
    mojo_draft_body = "But I must explain to you how all this mistaken idea of denouncing of a pleasure and praising " \
                      "pain was born and I will give you a complete account of the system, and expound the actual teachings " \
                      "of the great explorer of the truth, the master-builder of human happiness. No one rejects, dislikes, or avoids pleasure itself, " \
                      "because it is pleasure, but because those who do not know how to pursue pleasure rationally encounter consequences that are extremely painful. "

    calendar_suggestion_placeholder = "This is a welcome message placeholder."
    calendar_suggestion_title_placeholder = "Title placeholder"
    calendar_suggestion_emoji_placeholder = "👋"
    waiting_message_placeholder = "Waiting..."
    done_message_placeholder = "Done!"

    def stream(self, message, stream_callback, n_initial_chars=3, sleep_time=0.1, n_chars_batch=3):
        try:
            # fake a stream by calling stream_callback every 0.3s
            time.sleep(sleep_time)
            stream_callback(message[:n_initial_chars])
            if n_initial_chars < len(message):
                self.stream(message, stream_callback, n_initial_chars + n_chars_batch)
        except Exception as e:
            raise Exception(f"PlaceholderGenerator:: stream: {e}")