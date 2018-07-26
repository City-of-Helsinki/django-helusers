# Import SOCIAL_AUTH_PIPELINE in your settings.py
SOCIAL_AUTH_PIPELINE = (
    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. On some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    'social_core.pipeline.social_auth.social_details',

    # Get the social uid from whichever service we're authing thru. The uid is
    # the unique identifier of the given user in the provider.
    'social_core.pipeline.social_auth.social_uid',

    # Reset logged-in user if UUID differs
    'helusers.pipeline.ensure_uuid_match',

    # Generate username from UUID
    'helusers.pipeline.get_username',

    # Checks if the current social-account is already associated in the site.
    'social_core.pipeline.social_auth.social_user',

    # Get or create the user and update user data
    'helusers.pipeline.create_or_update_user',

    # Create the record that associated the social account with this user.
    'social_core.pipeline.social_auth.associate_user',

    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    'social_core.pipeline.social_auth.load_extra_data',

    # Store the end session URL in the user's session data so that
    # we can format logout links properly.
    'helusers.pipeline.store_end_session_url',

    # If the access token gives access to external APIs, fetch the
    # API tokens here.
    'helusers.pipeline.fetch_api_tokens',
)
